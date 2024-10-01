from __future__ import annotations
import logging
from typing import List, Optional

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import PLATFORM_SCHEMA

import homeassistant.helpers.config_validation as cv
from .const import DOMAIN
from .aponet import Apotheke

_LOGGER = logging.getLogger(__name__)

CONF_NAME = "name"
CONF_PLZORT = "plzort"
CONF_STREET = "street"
CONF_LAT = "lat"
CONF_LON = "lon"
CONF_RADIUS = "radius"
CONF_ADDRESSES = "addresses"

ADDRESS_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_PLZORT): cv.string,
    vol.Optional(CONF_STREET): cv.string,
    vol.Optional(CONF_LAT): vol.Coerce(float),
    vol.Optional(CONF_LON): vol.Coerce(float),
    vol.Optional(CONF_RADIUS, default=5): cv.positive_int,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ADDRESSES): vol.All(cv.ensure_list, [ADDRESS_SCHEMA]),
})


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    coordinator = hass.data[DOMAIN]['coordinator']
    if "addresses" in config:
        for address in config["addresses"]:
            async_add_entities([PharmacySensor(hass, address, coordinator)])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN]['coordinator']
    async_add_entities([PharmacySensor(hass, config_entry.data, coordinator)])


class PharmacySensor(SensorEntity):
    """Representation of a Pharmacy Sensor."""
    pharmacies: List[Apotheke] = []

    def __init__(self, hass, config, coordinator):
        """Initialize the sensor."""
        self.hass: HomeAssistant = hass
        self.config = config
        self.coordinator = coordinator
        self.sensor_name: str = config["name"]
        self.plzort: str = config["plzort"]
        self.date: Optional[str] = config.get("date")
        self.street: Optional[str] = config.get("street")
        self.lat: Optional[str] = config.get("lat")
        self.lon: Optional[str] = config.get("lon")
        self.radius: Optional[int] = config.get("radius", 5)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.sensor_name or f"Pharmacies near {self.street or self.plzort}"

    @property
    def state(self):
        closest_pharmacy: Apotheke = self.get_closest_pharmacy()
        if closest_pharmacy:
            return f"Closest open pharmacy {closest_pharmacy.name} in {int(closest_pharmacy.distance)} km"
        return "N/A"

    @property
    def extra_state_attributes(self):
        closest_pharmacy: Apotheke = self.get_closest_pharmacy()
        if closest_pharmacy:
            return closest_pharmacy.to_dict()
        return {"message": "No pharmacies found"}

    def get_closest_pharmacy(self):
        if self.pharmacies and isinstance(self.pharmacies, list):
            return self.pharmacies[0]
        return None

    async def async_update(self):
        """Fetch data from the API and update the sensor state."""
        _LOGGER.info(f"Updating sensor for PLZ/Ort: {self.plzort}, Date: {self.date}")

        await self.coordinator.async_request_refresh()

        # Extract data from the coordinator's latest data
        data = self.coordinator.data
        if data:
            self.pharmacies = data.get_data()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        # Ensure the coordinator updates when the sensor is added
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))
