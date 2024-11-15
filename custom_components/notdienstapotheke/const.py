"""Constants."""

from datetime import timedelta

DOMAIN = "notdienstapotheke"
SCAN_INTERVAL = timedelta(days=1)
API_ENDPOINT = "https://www.aponet.de/apotheke/notdienstsuche/"
API_MAX_RESULTS = 15
