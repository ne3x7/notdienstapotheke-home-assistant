"""Sensor platform."""

# pylint: disable=W0239

from __future__ import annotations
import logging
from typing import List

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import PLATFORM_SCHEMA

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from .const import SCAN_INTERVAL, CONF_ADDRESSES
from .aponet import Apotheke, Aponet
from .schemas import ADDRESS_SCHEMA

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESSES): vol.All(cv.ensure_list, [ADDRESS_SCHEMA]),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the pharmacy sensors from YAML configuration."""
    if discovery_info is not None:
        config = discovery_info

    # Create and add entities from the YAML config
    if "addresses" in config:
        for address in config["addresses"]:
            api_client = Aponet(
                plzort=address["plzort"],
                date=address.get("date"),
                street=address.get("street"),
                lat=address.get("lat"),
                lon=address.get("lon"),
                radius=address.get("radius", 5),
            )
            async_add_entities([PharmacySensor(hass, address, api_client)])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the integration from a config entry."""
    address = config_entry.data
    api_client = Aponet(
        plzort=address["plzort"],
        date=address.get("date"),
        street=address.get("street"),
        lat=address.get("lat"),
        lon=address.get("lon"),
        radius=address.get("radius", 5),
    )
    async_add_entities([PharmacySensor(hass, address, api_client)])


class PharmacySensor(SensorEntity):
    """Representation of a Pharmacy Sensor."""

    pharmacies: List[Apotheke] = []

    def __init__(self, hass, config, api_client):
        """Initialize the sensor."""
        self.hass: HomeAssistant = hass
        self.api_client = api_client
        self.sensor_name: str = config["name"]
        self.plzort = config["plzort"]
        self.street: str = config.get("street")

        self._unsub = async_track_time_interval(hass, self.async_update, SCAN_INTERVAL)

        hass.async_create_task(self.async_update())

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.sensor_name or f"Pharmacies near {self.street or self.plzort}"

    @property
    def state(self):
        _LOGGER.debug("Current pharmacies: %s", self.pharmacies)
        closest_pharmacy: Apotheke = self.get_closest_pharmacy()
        if closest_pharmacy:
            return (
                f"Closest open pharmacy {closest_pharmacy.name}"
                f"in {int(round(float(closest_pharmacy.distance)))} km"
            )
        return "N/A"

    @property
    def extra_state_attributes(self):
        _LOGGER.debug("Current pharmacies: %s", self.pharmacies)
        closest_pharmacy: Apotheke = self.get_closest_pharmacy()
        if closest_pharmacy:
            return closest_pharmacy.to_dict()
        return {"message": "No pharmacies found"}

    def get_closest_pharmacy(self):
        """Get the closest pharmacy, sorting is assumed."""
        if (
            self.pharmacies
            and isinstance(self.pharmacies, list)
            and len(self.pharmacies) > 0
        ):
            return self.pharmacies[0]
        return None

    async def async_update(self, _=None):
        """Fetch data from the Aponet API."""
        try:
            # Call the API with the sensor-specific parameters
            self.pharmacies = await self.hass.async_add_executor_job(
                self.api_client.get_data,
            )
            _LOGGER.debug("Fetched pharmacies: %s", self.pharmacies)

            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Error updating %s: %s", self.name, err)

    async def async_will_remove_from_hass(self):
        """Cleanup when entity is removed."""
        if self._unsub is not None:
            self._unsub()
