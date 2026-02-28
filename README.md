# Ask-Finance / Ask-Navan Slack Bot

A Slack bot that uses Claude AI to answer questions in **#ask-finance** and **#ask-navan** channels. It draws on company policy knowledge and past channel Q&A to give accurate, contextual responses.

## How It Works

1. A user @mentions the bot in one of the configured channels
2. The bot fetches the last 30 days of channel history and finds similar past Q&A pairs
3. It sends the question, relevant knowledge-base content, and historical context to Claude
4. Claude's response is posted as a thread reply

## Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app
2. Enable **Socket Mode** under Settings and generate an App-Level Token with `connections:write` scope
3. Under **OAuth & Permissions**, add these Bot Token Scopes:
   - `app_mentions:read`
   - `channels:history`
   - `channels:read`
   - `chat:write`
4. Under **Event Subscriptions**, subscribe to the `app_mention` bot event
5. Install the app to your workspace and copy the Bot User OAuth Token

### 2. Configure Environment

```bash
cp .env.example .env
```

Fill in your `.env` file:
- `SLACK_BOT_TOKEN` — Bot User OAuth Token (`xoxb-...`)
- `SLACK_APP_TOKEN` — App-Level Token (`xapp-...`)
- `ANTHROPIC_API_KEY` — Your Anthropic API key
- `ASK_FINANCE_CHANNEL_ID` — Channel ID for #ask-finance
- `ASK_NAVAN_CHANNEL_ID` — Channel ID for #ask-navan

To find a channel ID: right-click the channel name in Slack, select "Copy link", and extract the ID from the URL.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Invite the Bot

Invite the bot to both channels in Slack:

```
/invite @YourBotName
```

### 5. Run

```bash
python bot.py
```

## File Structure

```
bot.py                  — Main bot application
knowledge_base.py       — Company policy content and retrieval logic
integrations/
  __init__.py
  base.py               — Abstract base class for integrations
  navan.py              — Placeholder Navan API client
.env.example            — Environment variable template
requirements.txt        — Python dependencies
```

## Customising the Knowledge Base

Edit `knowledge_base.py` to add or update policy content. Each channel type (`finance` or `navan`) has a dictionary of topic-content pairs. The bot matches question keywords against these topics and includes relevant content in Claude's context.

## Future: Navan Integration

The `integrations/navan.py` module contains a `NavanClient` class with placeholder methods for:

- `get_user_trips(email)` — fetch a user's upcoming trips
- `get_booking_status(booking_id)` — check a booking's status
- `search_flights(origin, destination, date)` — search available flights
- `search_hotels(location, checkin, checkout)` — search available hotels

To enable:

1. Implement the API calls in `NavanClient`
2. Have `NavanClient` inherit from `integrations.base.Integration`
3. Set `NAVAN_ENABLED = True` in `bot.py`
4. Add `NAVAN_API_KEY` and `NAVAN_API_SECRET` to your `.env`
5. Uncomment the Navan context injection block in `build_prompt_messages()`
