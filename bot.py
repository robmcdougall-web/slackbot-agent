"""
Slack bot that answers questions in #ask-finance and #ask-navan channels using Claude AI.
Uses channel history and a knowledge base to provide contextual, accurate responses.
"""

import os
import re
import time
import logging
import threading
from datetime import datetime, timedelta

import schedule

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import anthropic

from knowledge_base import get_relevant_knowledge
from integrations.navan import NavanClient

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

ASK_FINANCE_CHANNEL_ID = os.environ["ASK_FINANCE_CHANNEL_ID"]
ASK_NAVAN_CHANNEL_ID = os.environ["ASK_NAVAN_CHANNEL_ID"]

# Test mode: listen in test channels, but read history from real channels
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
if TEST_MODE:
    LISTEN_FINANCE_CHANNEL_ID = os.environ["TEST_FINANCE_CHANNEL_ID"]
    LISTEN_NAVAN_CHANNEL_ID = os.environ["TEST_NAVAN_CHANNEL_ID"]
    logger.info("TEST MODE enabled — listening in test channels, reading history from real channels.")
else:
    LISTEN_FINANCE_CHANNEL_ID = ASK_FINANCE_CHANNEL_ID
    LISTEN_NAVAN_CHANNEL_ID = ASK_NAVAN_CHANNEL_ID

# Future Navan integration toggle
NAVAN_ENABLED = False
# When enabled, instantiate like:
#   navan_client = NavanClient(
#       api_key=os.environ["NAVAN_API_KEY"],
#       api_secret=os.environ["NAVAN_API_SECRET"],
#   )

# ---------------------------------------------------------------------------
# Slack & Anthropic clients
# ---------------------------------------------------------------------------
app = App(token=SLACK_BOT_TOKEN)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ---------------------------------------------------------------------------
# Channel configuration
# ---------------------------------------------------------------------------
CHANNEL_CONFIG = {
    LISTEN_FINANCE_CHANNEL_ID: {
        "type": "finance",
        "history_source": ASK_FINANCE_CHANNEL_ID,
        "system_prompt": (
            "You are a helpful finance assistant for the company Kaluza. "
            "You answer questions about expense policies, reimbursements, budgets, "
            "invoices, procurement, and general finance queries. "
            "Be concise and professional. When you reference past answers, say "
            '"Based on how we\'ve handled similar questions..." '
            "If you are uncertain, clearly say so and suggest the person contacts "
            "the Finance team directly or posts in #ask-finance for a human follow-up."
        ),
    },
    LISTEN_NAVAN_CHANNEL_ID: {
        "type": "navan",
        "history_source": ASK_NAVAN_CHANNEL_ID,
        "system_prompt": (
            "You are a helpful travel and Navan assistant for the company Kaluza. "
            "You answer questions about travel booking via the Navan platform, "
            "travel policies, flights, hotels, cancellations, travel insurance, "
            "and expense claims related to travel. "
            "Be concise and professional. When you reference past answers, say "
            '"Based on how we\'ve handled similar questions..." '
            "If you are uncertain, clearly say so and suggest the person contacts "
            "the Finance team or Navan support directly."
        ),
    },
}

# ---------------------------------------------------------------------------
# History cache
# ---------------------------------------------------------------------------
# Populated on startup, refreshed every hour via a background thread.
# Structure: {channel_id: {"messages": [...], "threads": {ts: [...]}, "last_refreshed": datetime}}
_history_cache: dict = {}


def _refresh_single_channel(channel_id: str) -> dict:
    """Fetch channel history and all thread replies, returning a cache entry."""
    logger.info("Refreshing cache for channel %s …", channel_id)
    messages = fetch_channel_history(channel_id)

    threads: dict[str, list[dict]] = {}
    for msg in messages:
        if int(msg.get("reply_count", 0)) > 0:
            thread_ts = msg["ts"]
            try:
                threads[thread_ts] = fetch_thread_replies(channel_id, thread_ts)
            except Exception:
                logger.warning(
                    "Failed to fetch thread %s in channel %s — skipping.",
                    thread_ts, channel_id,
                )
            time.sleep(0.5)  # respect Slack rate limits during bulk fetch

    logger.info(
        "Cache refreshed for channel %s: %d messages, %d threads.",
        channel_id, len(messages), len(threads),
    )
    return {
        "messages": messages,
        "threads": threads,
        "last_refreshed": datetime.now(),
    }


def refresh_cache() -> None:
    """Refresh the history cache for all history source channels."""
    # Deduplicate: in production mode, listen channel == history source
    source_channels = {
        config["history_source"] for config in CHANNEL_CONFIG.values()
    }
    for channel_id in source_channels:
        try:
            _history_cache[channel_id] = _refresh_single_channel(channel_id)
        except Exception:
            logger.exception(
                "Failed to refresh cache for channel %s.", channel_id,
            )


def _run_scheduler() -> None:
    """Run the schedule loop in a background daemon thread."""
    while True:
        schedule.run_pending()
        time.sleep(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_question_text(text: str, bot_user_id: str) -> str:
    """Strip the @mention from the message to get the raw question."""
    cleaned = re.sub(rf"<@{bot_user_id}>", "", text).strip()
    return cleaned


def _tokenise(text: str) -> set[str]:
    """Lowercase tokenisation for keyword overlap matching."""
    stopwords = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "must", "can", "could", "i", "me", "my",
        "we", "our", "you", "your", "he", "she", "it", "they", "them", "and",
        "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
        "from", "as", "into", "about", "that", "this", "what", "which", "who",
        "how", "when", "where", "why", "not", "no", "so", "if", "then",
    }
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return words - stopwords


def _similarity(text_a: str, text_b: str) -> int:
    """Return the number of overlapping non-stopword tokens."""
    return len(_tokenise(text_a) & _tokenise(text_b))


def fetch_channel_history(channel_id: str, days: int = 30) -> list[dict]:
    """
    Fetch the last *days* of messages from a channel.
    Returns a list of message dicts.
    """
    oldest = str((datetime.now() - timedelta(days=days)).timestamp())
    messages: list[dict] = []
    cursor = None

    while True:
        kwargs = {
            "channel": channel_id,
            "oldest": oldest,
            "limit": 200,
            "inclusive": True,
        }
        if cursor:
            kwargs["cursor"] = cursor

        resp = app.client.conversations_history(**kwargs)
        messages.extend(resp["messages"])

        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    return messages


def fetch_thread_replies(channel_id: str, thread_ts: str) -> list[dict]:
    """Fetch all replies in a thread."""
    resp = app.client.conversations_replies(
        channel=channel_id,
        ts=thread_ts,
        limit=200,
    )
    return resp.get("messages", [])


def find_similar_qa_pairs(
    channel_id: str,
    question: str,
    top_n: int = 3,
    min_overlap: int = 3,
) -> list[dict]:
    """
    Look through cached channel history for messages that:
      1. Are not bot messages
      2. Have thread replies from humans
      3. Share at least *min_overlap* keywords with the new question

    Returns the top-N matches as {question, answer, score} dicts.
    """
    cache_entry = _history_cache.get(channel_id)

    if cache_entry:
        history = cache_entry["messages"]
        cached_threads = cache_entry["threads"]
    else:
        logger.warning(
            "Cache miss for channel %s — falling back to live API.", channel_id,
        )
        history = fetch_channel_history(channel_id)
        cached_threads = {}

    candidates: list[dict] = []

    for msg in history:
        # Skip bot messages
        if msg.get("bot_id") or msg.get("subtype") == "bot_message":
            continue
        # Only consider messages that started a thread
        if int(msg.get("reply_count", 0)) == 0:
            continue

        score = _similarity(question, msg.get("text", ""))
        if score < min_overlap:
            continue

        # Get thread replies from cache, or fetch live as fallback
        thread_ts = msg["ts"]
        replies = cached_threads.get(thread_ts) or fetch_thread_replies(channel_id, thread_ts)
        human_replies = [
            r for r in replies
            if r["ts"] != msg["ts"]
            and not r.get("bot_id")
            and r.get("subtype") != "bot_message"
        ]
        if not human_replies:
            continue

        # Use the first human reply as the canonical answer
        candidates.append({
            "question": msg.get("text", ""),
            "answer": human_replies[0].get("text", ""),
            "score": score,
        })

    # Sort by relevance and return top N
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:top_n]


def build_prompt_messages(
    channel_id: str,
    question: str,
    similar_qa: list[dict],
) -> list[dict]:
    """
    Assemble the messages list for the Claude API call, including:
      - System prompt (channel-specific)
      - Knowledge base context
      - Similar past Q&A pairs
      - The user's question
    """
    config = CHANNEL_CONFIG[channel_id]
    channel_type = config["type"]

    # Gather knowledge-base context
    kb_context = get_relevant_knowledge(channel_type, question)

    # Build context sections
    context_parts: list[str] = []

    if kb_context:
        context_parts.append(
            "## Relevant Company Policy / Knowledge Base\n" + kb_context
        )

    if similar_qa:
        qa_text = "\n\n".join(
            f"Q: {qa['question']}\nA: {qa['answer']}" for qa in similar_qa
        )
        context_parts.append(
            "## Similar Past Questions & Answers from This Channel\n" + qa_text
        )

    # --- Future Navan integration injection point ---
    # if NAVAN_ENABLED:
    #     navan_context = navan_client.enrich_context(question, user_email)
    #     if navan_context:
    #         context_parts.append("## Navan Account Context\n" + navan_context)

    user_content = ""
    if context_parts:
        user_content += "\n\n".join(context_parts) + "\n\n"
    user_content += f"## New Question\n{question}"

    return {
        "system": config["system_prompt"],
        "messages": [{"role": "user", "content": user_content}],
    }


def ask_claude(channel_id: str, question: str, similar_qa: list[dict]) -> str:
    """Send the question and context to Claude and return the response text."""
    prompt_data = build_prompt_messages(channel_id, question, similar_qa)

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=prompt_data["system"],
        messages=prompt_data["messages"],
    )

    return response.content[0].text


# ---------------------------------------------------------------------------
# Slack event handler
# ---------------------------------------------------------------------------

@app.event("app_mention")
def handle_mention(event, say):
    """Respond to @mentions in configured channels."""
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts") or event.get("ts")
    user = event.get("user")

    if channel_id not in CHANNEL_CONFIG:
        logger.info("Mention in unconfigured channel %s — ignoring.", channel_id)
        return

    config = CHANNEL_CONFIG[channel_id]
    channel_type = config["type"]
    history_source = config["history_source"]
    bot_user_id = app.client.auth_test()["user_id"]
    question = _extract_question_text(event.get("text", ""), bot_user_id)

    if not question:
        say(
            text="It looks like you mentioned me but didn't ask a question. How can I help?",
            thread_ts=thread_ts,
        )
        return

    logger.info(
        "Received question in #ask-%s from <@%s>: %s",
        channel_type, user, question[:120],
    )

    try:
        # Find similar past Q&A (reads from real channel history, even in test mode)
        similar_qa = find_similar_qa_pairs(history_source, question)
        logger.info("Found %d similar past Q&A pairs.", len(similar_qa))

        # Ask Claude (use listen channel_id for config lookup)
        answer = ask_claude(channel_id, question, similar_qa)

        say(text=answer, thread_ts=thread_ts)
        logger.info("Replied in thread %s.", thread_ts)

    except Exception:
        logger.exception("Error handling question.")
        say(
            text=(
                "Sorry, I ran into an issue trying to answer your question. "
                "Please try again or reach out to the team directly."
            ),
            thread_ts=thread_ts,
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting Slack bot in Socket Mode…")

    # Populate cache on startup (blocks until ready)
    logger.info("Populating history cache for all channels…")
    refresh_cache()
    logger.info("History cache populated.")

    # Schedule hourly cache refresh in a background thread
    schedule.every(1).hours.do(refresh_cache)
    threading.Thread(target=_run_scheduler, daemon=True).start()
    logger.info("Background cache refresh scheduled (every 1 hour).")

    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
