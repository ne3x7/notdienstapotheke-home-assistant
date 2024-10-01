from __future__ import annotations
import logging
from typing import List, Optional

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity

import homeassistant.helpers.config_validation as cv
from .const import DOMAIN
from .aponet import Apotheke

_LOGGER = logging.getLogger(__name__)

# Define the configuration schema for the YAML
PLATFORM_SCHEMA = vol.Schema({
    vol.Required("addresses"): vol.All(
        cv.ensure_list,  # Ensure the "pharmacies" is a list of dictionaries
        [
            vol.Schema({
                vol.Required("name"): cv.string,
                vol.Required("plzort"): cv.string,
                vol.Optional("date"): cv.date,  # Optional, but must be a valid date if provided
                vol.Optional("street"): cv.string,  # Optional street
                vol.Optional("lat"): vol.Coerce(float),  # Optional latitude
                vol.Optional("lon"): vol.Coerce(float),  # Optional longitude
                vol.Optional("radius", default=5): vol.Coerce(int),  # Optional radius, default is 5
            })
        ]
    ),
})

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    if "addresses" in config:
        for address in config["addresses"]:
            async_add_entities([PharmacySensor(hass, address)])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PharmacySensor(hass, config_entry.data)])


class PharmacySensor(SensorEntity):
    """Representation of a Pharmacy Sensor."""
    pharmacies: List[Apotheke] = []

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass: HomeAssistant = hass
        self.config = config
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

        client = self.hass.data[DOMAIN].get("client")
        try:
            self.pharmacies = await self.hass.async_add_executor_job(
                client.get_data, self.plzort, self.date, self.street, self.lat, self.lon, self.radius
            )

        except Exception as e:
            _LOGGER.error(f"Error fetching data for {self.plzort}: {e}")
