"""Input schemas for Notdienstapotheke."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_NAME,
    CONF_PLZORT,
    CONF_STREET,
    CONF_LAT,
    CONF_LON,
    CONF_RADIUS,
)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PLZORT): cv.string,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_STREET): cv.string,
        vol.Optional(CONF_LAT): vol.Coerce(float),
        vol.Optional(CONF_LON): vol.Coerce(float),
        vol.Optional(CONF_RADIUS, default=5): cv.positive_int,
    }
)

ADDRESS_SCHEMA = SENSOR_SCHEMA.extend(OPTIONS_SCHEMA)
