"""Config flow for ZKAccess C3."""
import logging
from typing import Any

from c3 import C3
from c3.consts import C3_PORT_DEFAULT
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import network
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=C3_PORT_DEFAULT): cv.port,
        vol.Optional(CONF_NAME): cv.string,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate C3 connection parameters."""
    panel = C3(data[CONF_HOST], port=data[CONF_PORT])
    if not panel.connect():
        raise CannotConnect

    return {"title": data[CONF_NAME] or "ZKAccess C3"}


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""
    adapters = await network.async_get_adapters(hass)
    ipv4_adapters = [adapter["ipv4"] for adapter in adapters]
    ipv4_adresses = [ip_info[0]["address"] for ip_info in ipv4_adapters]

    devices = await hass.async_add_executor_job(C3.discover, ipv4_adresses)
    return len(devices) > 0


# config_entry_flow.register_discovery_flow(DOMAIN, "C3", _async_has_devices)


class C3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for C3."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
