"""Config flow for Notdienstapotheke integration."""

from __future__ import annotations

from typing import Any
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .schemas import ADDRESS_SCHEMA, OPTIONS_SCHEMA
from .aponet import Aponet


class NotdienstapothekeConfigFlow(ConfigFlow, domain=DOMAIN):  # ignore: call-arg
    """Handle a config flow for Notdienstapotheke."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate user input
            plzort = user_input.get("plzort")
            if not self._validate_plzort(plzort):  # type: ignore
                errors["plzort"] = "invalid_plzort"
            else:
                # If valid, create a config entry
                return self.async_create_entry(
                    title=user_input["name"], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=ADDRESS_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def _validate_plzort(plzort: str) -> bool:
        """Validate postal code or city input."""
        return (
            not Aponet(plzort=plzort)
            .call_api()
            .content.decode("ascii")
            .startswith("Oops")
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> NotdienstapothekeOptionsFlow:
        """Return the options flow."""
        return NotdienstapothekeOptionsFlow(config_entry)


class NotdienstapothekeOptionsFlow(OptionsFlow):
    """Handle the options flow for the integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the options
            return self.async_create_entry(data=user_input)

        return self.async_show_form(step_id="init", data_schema=OPTIONS_SCHEMA)
