"""Notdienstapotheke integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Notdienstapotheke from YAML configuration."""
    _LOGGER.info("Setting up Notdienstapotheke from YAML configuration")

    # Store the configuration in `hass.data` for use by platforms
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data.setdefault(DOMAIN, {})

    # Forward the setup to the sensor platform
    hass.async_create_task(
        hass.helpers.entity_platform.async_load_platform(
            Platform.SENSOR, DOMAIN, config[DOMAIN], hass.data
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Notdienstapotheke integration from a ConfigEntry (UI-based)."""
    _LOGGER.info("Setting up Notdienstapotheke from ConfigEntry (UI-based)")

    # Store the ConfigEntry data in `hass.data` for use by platforms
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up listener to handle config entry updates
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle updates to the configuration entry (e.g., changes to API key or URL)."""
    _LOGGER.info("Config entry updated, reloading integration...")
    # Reload the integration if any config is changed
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of a ConfigEntry (UI-based)."""
    _LOGGER.info("Unloading Notdienstapotheke ConfigEntry")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
