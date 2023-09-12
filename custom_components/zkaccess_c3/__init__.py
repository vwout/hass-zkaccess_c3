"""The C3 integration."""
from __future__ import annotations

# from datetime import timedelta
import logging

from c3.consts import C3_PORT_DEFAULT
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    DATA_C3_COORDINATOR,
    DATA_DISCOVERY_INTERVAL,
    DATA_DISCOVERY_SERVICE,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import C3Coordinator

# from homeassistant.components.network import async_get_ipv4_broadcast_addresses

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=C3_PORT_DEFAULT): cv.port,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NAME): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    if discovery_info is not None:
        pass
        # conf, coordinator, rest = await async_get_config_and_coordinator(
        #    hass, DOMAIN, discovery_info
        # )


async def async_setup(hass: HomeAssistant, config_entry: ConfigType) -> bool:
    """Set up the C3 panel platform."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up C3 from a config entry."""
    hass.data.setdefault(
        DOMAIN,
        {
            config_entry.entry_id: {
                DATA_C3_COORDINATOR: None,
                Platform.LOCK: [],
                Platform.SWITCH: [],
                Platform.BINARY_SENSOR: [],
            }
        },
    )

    # # Setup C3 discovery to automatically add devices
    # c3_discovery = C3DiscoveryService(hass)
    # hass.data[DOMAIN][DATA_DISCOVERY_SERVICE] = c3_discovery
    #
    # await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    #
    # #def _async_scan_update(_=None):
    #     c3_discovery.scan()
    #
    # _LOGGER.debug("Scanning network for ZKAccess C3 devices")
    # await _async_scan_update()
    #
    # hass.data[DOMAIN][DATA_DISCOVERY_INTERVAL] = async_track_time_interval(
    #     hass, _async_scan_update, timedelta(seconds=DISCOVERY_SCAN_INTERVAL)
    # )

    c3_coordinator = C3Coordinator(
        hass,
        config_entry,
        config_entry.data[CONF_HOST],
        config_entry.data[CONF_PORT],
        config_entry.data.get(CONF_PASSWORD, ""),
    )

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    await c3_coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload discovery thread and entities entry."""

    if hass.data[DOMAIN].get(DATA_DISCOVERY_INTERVAL) is not None:
        hass.data[DOMAIN].pop(DATA_DISCOVERY_INTERVAL)()

    if hass.data[DOMAIN].get(DATA_DISCOVERY_SERVICE) is not None:
        hass.data[DOMAIN].pop(DATA_DISCOVERY_SERVICE)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
