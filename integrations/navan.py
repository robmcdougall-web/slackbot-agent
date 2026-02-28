"""
Placeholder Navan API client.

This module provides a NavanClient class with stub methods for interacting
with the Navan (formerly TripActions) API.  None of the methods are
implemented yet — they exist so the integration surface is defined and
ready to build on once Navan API access is available.

When the Navan API is enabled:
  1. Set NAVAN_ENABLED = True in bot.py
  2. Populate NAVAN_API_KEY and NAVAN_API_SECRET in your .env
  3. Have NavanClient inherit from integrations.base.Integration
  4. Implement the methods below
"""


class NavanClient:
    """Client for the Navan travel platform API."""

    def __init__(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret

    def get_user_trips(self, email: str) -> list | None:
        """Fetch upcoming trips for a user.

        Args:
            email: The user's company email address.

        Returns:
            A list of trip dicts, or None while unimplemented.
        """
        # TODO: Implement when Navan API access is available
        return None

    def get_booking_status(self, booking_id: str) -> dict | None:
        """Get the status of a specific booking.

        Args:
            booking_id: The Navan booking reference ID.

        Returns:
            A dict with booking details, or None while unimplemented.
        """
        # TODO: Implement when Navan API access is available
        return None

    def search_flights(
        self, origin: str, destination: str, date: str
    ) -> list | None:
        """Search available flights.

        Args:
            origin: IATA airport code for departure (e.g. "LHR").
            destination: IATA airport code for arrival (e.g. "JFK").
            date: Travel date in YYYY-MM-DD format.

        Returns:
            A list of flight option dicts, or None while unimplemented.
        """
        # TODO: Implement when Navan API access is available
        return None

    def search_hotels(
        self, location: str, checkin: str, checkout: str
    ) -> list | None:
        """Search available hotels.

        Args:
            location: City name or area (e.g. "London").
            checkin: Check-in date in YYYY-MM-DD format.
            checkout: Check-out date in YYYY-MM-DD format.

        Returns:
            A list of hotel option dicts, or None while unimplemented.
        """
        # TODO: Implement when Navan API access is available
        return None
