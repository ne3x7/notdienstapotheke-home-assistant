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
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN, SCAN_INTERVAL
from .aponet import Apotheke, Aponet

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
    if DOMAIN in hass.data and "yaml_config" in hass.data[DOMAIN]:
        addresses = hass.data[DOMAIN]["yaml_config"].get("addresses", [])
        entities = []
        for address in addresses:
            api_client = Aponet(
                plzort=address["plzort"],
                date=address.get("date"),
                street=address.get("street"),
                lat=address.get("lat"),
                lon=address.get("lon"),
                radius=address.get("radius", 5),
            )
            entities.append(PharmacySensor(hass, address, api_client))
        async_add_entities(entities)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
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
        self.config = config
        self.api_client = api_client
        self.sensor_name: str = config["name"]
        self.plzort = config["plzort"]
        self.street: str = config.get("street")

        self._unsub = async_track_time_interval(hass, self.async_update, SCAN_INTERVAL)

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

    async def async_update(self, _=None):
        """Fetch data from the Aponet API."""
        try:
            # Call the API with the sensor-specific parameters
            self.pharmacies = await self.hass.async_add_executor_job(
                self.api_client.get_data,
            )

            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error(f"Error updating {self.name}: {err}")

    async def async_will_remove_from_hass(self):
        """Cleanup when entity is removed."""
        if self._unsub is not None:
            self._unsub()
