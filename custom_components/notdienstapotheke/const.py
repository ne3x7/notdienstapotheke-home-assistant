"""Constants."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "notdienstapotheke"
SCAN_INTERVAL = timedelta(days=1)
API_ENDPOINT = "https://www.aponet.de/apotheke/notdienstsuche/"
API_MAX_RESULTS = 15
CONF_PLZORT = "plzort"
CONF_STREET = "street"
CONF_LAT = "lat"
CONF_LON = "lon"
CONF_RADIUS = "radius"
CONF_NAME = "name"
CONF_ADDRESSES = "addresses"
