"""Notdienstapotheke integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .aponet import Aponet
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry (UI-based)."""
    # api_key = entry.data[CONF_API_KEY]
    # base_url = entry.data[CONF_URL]

    # Initialize the API client
    api_client = Aponet(base_url, api_key)

    # Set up the coordinator to fetch data once per day
    coordinator = AponetDailyDataCoordinator(hass, api_client)

    # Store the coordinator for future use by platforms
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Trigger the first data fetch (this will load data when the integration is set up)
    await coordinator.async_config_entry_first_refresh()

    # Forward the setup to all platforms (defined in PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for config entry updates
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle updates to the configuration entry (e.g., changes to API key or URL)."""
    _LOGGER.info("Config entry updated, reloading integration...")
    # Reload the integration if any config is changed
    await hass.config_entries.async_reload(entry.entry_id)


def setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration via YAML configuration."""
    _LOGGER.info("Setting up integration via YAML configuration.")
    # This can be used to process YAML-based configuration, but this example assumes
    # you are focusing on config entry (UI) setup, so it does nothing.
    return True


class AponetDailyDataCoordinator(DataUpdateCoordinator):
    """Custom coordinator to fetch data from API once per day."""

    def __init__(self, hass, api_client):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Aponet Daily Data",
            update_interval=SCAN_INTERVAL,  # Fetch once per day
        )
        self.api_client = api_client

    async def _async_update_data(self):
        """Fetch data from the API."""
        try:
            # Fetch the data from the API (run the API call in a background thread)
            return await self.hass.async_add_executor_job(self.api_client.get_data)
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")
