"""
Knowledge base for the #ask-finance and #ask-navan Slack bot.

Contains company policy content used to ground Claude's answers.
The get_relevant_knowledge() function does simple keyword matching
to return the most relevant sections for a given question.
"""

import re

KNOWLEDGE_BASE: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------
    # FINANCE knowledge
    # ------------------------------------------------------------------
    "finance": {
        "expense_policy": (
            "Expenses should be as economical and efficient as possible. "
            "Typically you purchase items yourself and expense them back with the receipt. "
            "If you're unsure whether a purchase would be covered, ask your People Leader "
            "or Finance Partner. People Leaders should ensure expense claims have receipts "
            "attached and approve them in a timely manner — typically within 2 weeks."
        ),
        "claiming_expenses": (
            "Enter your expenses into Navan with a full receipt unless absolutely not possible. "
            "Guides are available on Navan to help you. "
            "If you need help, message your Finance Partner."
        ),
        "entertainment": (
            "Lunch or entertaining should typically only be expensed if it's a client event. "
            "Alcohol may be part of these expenses but please use your best judgement. "
            "Non-reimbursable items include: laundry/dry-cleaning, toiletries, mini-bar, "
            "newspapers, movies/videos, parking fines or other fines, damage to personal "
            "vehicles, loss/theft of goods, and any personal elements of expenditure."
        ),
        "mileage_rates": (
            "UK private car: 45p/mile for the first 10,000 miles, 25p/mile thereafter. "
            "Motorcycles: 24p/mile. Cycling: 20p/mile. "
            "US private car/van/pickup: 65.5 cents per mile (from 1 Jan 2023). "
            "These rates are set by HMRC (UK) / IRS (US), not Kaluza."
        ),
        "car_hire": (
            "Car hire is allowed for journeys over 100 miles and if more than one "
            "employee is travelling. Parking costs on business travel can be claimed."
        ),
        "taxis": (
            "Always try to use public transport first. Taxi fares may only be claimed "
            "where no suitable public transport is available, when travelling in an unsafe "
            "area, when public transport is infrequent, or where there is a business cost "
            "saving. You'll need a receipt."
        ),
        "interview_expenses": (
            "Candidates travelling over 2 hours to a Kaluza interview may claim up to "
            "£100 in expenses with receipts. Candidates provide bank details to the "
            "Talent Acquisition team who arrange payment via Finance."
        ),
        # TODO: Add additional finance policy content here, e.g.:
        # "procurement_policy": "...",
        # "invoice_process": "...",
        # "budget_approvals": "...",
    },

    # ------------------------------------------------------------------
    # NAVAN / TRAVEL knowledge
    # ------------------------------------------------------------------
    "navan": {
        "booking_process": (
            "Use the Navan booking platform for flights and accommodation. "
            "For rail travel, use Trainline or another provider for split-ticketing prices "
            "(this will move to Navan once available). "
            "When booking taxis, use a reputable firm. "
            "For in-country travel, check with your People Leader then book. "
            "For international travel, get approval from your HoD/Director first."
        ),
        "flight_booking": (
            "Review prices in Navan and compare with Skyscanner. If prices are similar "
            "and flight times align, book through Navan. "
            "If variance is high (>£50 per flight) or right times aren't available, "
            "contact Navan directly via chat or telephone for concierge service."
        ),
        "flight_class": (
            "Class of travel policy:\n"
            "- Up to 5 hours: Economy for all employees.\n"
            "- Up to 12 hours: Economy below Director level; Premium Economy for Directors+.\n"
            "- Over 12 hours: Premium Economy below VP; Business Class for VPs and above.\n"
            "Upgrades at no cost to the company are fine. Self-funded upgrades are allowed. "
            "Only excess baggage for Kaluza business items is refunded."
        ),
        "flight_rest_policy": (
            "Post-flight rest expectations:\n"
            "- Up to 5 hours: meetings within 1–2 hours of landing.\n"
            "- Up to 12 hours (overnight / up to 3 time zones): 4 hours rest before meetings.\n"
            "- Over 12 hours: no meetings until at least 8 hours after landing; "
            "crossing 4+ time zones: 24 hours rest.\n\n"
            "Time-off-in-lieu for non-working-hours travel (return trip):\n"
            "- Up to 5 hours: take back time as TOIL.\n"
            "- Up to 12 hours: one day off in lieu.\n"
            "- Over 12 hours: two days off in lieu."
        ),
        "accommodation": (
            "Book overnight stays through Navan. Choose a moderate business-class hotel "
            "near your meeting location at the cheapest available rate.\n"
            "Rate guidelines: up to £150/night inner city (e.g. Bristol), "
            "up to £200/night London.\n"
            "Meal guideline while staying overnight: max £25/€30/$30 per day per person.\n\n"
            "Corporate rate hotels are available in London (Hoxton Shepherds Bush £180, "
            "DoubleTree Hyde Park £195 inc breakfast, Ruby Zoe 12% off), "
            "Edinburgh (Yotel 20% off, Mercure Princes St £110 inc breakfast), "
            "Bristol (Leonardo £100–£110, DoubleTree £135–£150 inc breakfast), "
            "Melbourne (Savoy $220, Next Hotel 15% off, Movenpick $270 inc breakfast), "
            "Washington DC (Canopy by Hilton 12% off), "
            "and Lisbon (MAMA Lisboa seasonal rates from €95)."
        ),
        "travel_insurance": (
            "Kaluza holds a group Personal Accident and Travel (PAT) insurance policy "
            "through AON UK Limited under Energy Transition Holdings Ltd (Ovo Group). "
            "Insurers: Chubb (45%), AIG (45%), Zurich (10%). "
            "All employees travelling abroad for short-term work are covered. "
            "No exclusions for pre-existing conditions or allergies. "
            "Emergency line: +44 (0)207 173 7797. "
            "Policy number: P25PATPTP04121. "
            "Claims email: aum.claims@aon.co.uk. "
            "For pre-existing conditions, get written email confirmation from AON before travel."
        ),
        "rail": (
            "Always book standard class, as far ahead as possible for cheapest fares. "
            "You can claim the annual cost of a railcard if you regularly expense train "
            "travel (not commuting to your core office). "
            "OYSTER/Contactless: attach a breakdown of all journeys to your expense claim."
        ),
        "overseas_travel": (
            "International travel must be approved by your HoD/Director. "
            "Visa costs, travel insurance, foreign currency exchange charges, and GPS hire "
            "with rental cars can be claimed. "
            "Ensure you have the right to work in the destination country (check Working "
            "Abroad Policy) and all necessary documentation (e.g. VISAs) before booking. "
            "Contact your People Partner with questions."
        ),
        "sustainability": (
            "Kaluza is committed to reducing the environmental impact of business travel. "
            "Where possible, replace face-to-face meetings with video conferencing. "
            "If travel is necessary, combine meetings into one trip and use the most "
            "sustainable transport feasible."
        ),
        "duty_of_care": (
            "Always inform your People Leader (or a team member if they're away) of your "
            "overnight location. Schedule travel times into your calendar and share with "
            "your People Leader. Have emergency contacts saved in your phone. "
            "In an emergency, contact local emergency services first, then notify your "
            "People Leader and People Partner."
        ),
        "medical_travel": (
            "Employees with health issues should consult their healthcare provider before "
            "long-haul travel (especially flights over 5 hours). A doctor's note can be "
            "provided to your People Partner for specific travel accommodations. "
            "Notify your People Leader and People Partner of health conditions early. "
            "Alternative travel dates may be requested and approved where health conditions "
            "require extra recovery time."
        ),
        # TODO: Add additional Navan/travel content here, e.g.:
        # "navan_platform_guide": "...",
        # "cancellation_policy": "...",
    },
}


def _tokenise(text: str) -> set[str]:
    """Lowercase tokenisation — mirrors the bot's tokeniser."""
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


def get_relevant_knowledge(channel_type: str, question: str) -> str:
    """
    Return concatenated knowledge-base content whose topics share at least
    one keyword with the question.  Returns an empty string if nothing matches.
    """
    topics = KNOWLEDGE_BASE.get(channel_type, {})
    if not topics:
        return ""

    q_tokens = _tokenise(question)
    matches: list[tuple[int, str, str]] = []

    for topic, content in topics.items():
        topic_tokens = _tokenise(topic) | _tokenise(content)
        overlap = len(q_tokens & topic_tokens)
        if overlap > 0:
            matches.append((overlap, topic, content))

    # Sort by relevance
    matches.sort(key=lambda m: m[0], reverse=True)

    if not matches:
        return ""

    sections = [f"### {topic}\n{content}" for _, topic, content in matches]
    return "\n\n".join(sections)
