"""Helper and wrapper classes for ZKAccess discovery."""
from __future__ import annotations

import logging

from c3 import C3
from homeassistant.core import HomeAssistant

from .const import DISCOVERY_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class C3DiscoveryService:
    """Discovery event handler for gree devices."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize discovery service."""
        # super().__init__()
        self.hass = hass

        # self.discovery = Discovery(DISCOVERY_TIMEOUT)
        # self.discovery.add_listener(self)

        # hass.data[DOMAIN].setdefault(COORDINATORS, [])

    def scan(self):
        """Scan for devices on the local network."""
        devices = C3.discover(timeout=DISCOVERY_TIMEOUT)
        for device in devices:
            _LOGGER.debug("Found device (%s):\n%s", {device.mac or "?"}, repr(device))

    # async def device_found(self, device_info: DeviceInfo) -> None:
    #    """Handle new device found on the network."""

    #    device = Device(device_info)
    #    try:
    #        await device.bind()
    #    except DeviceNotBoundError:
    #        _LOGGER.error("Unable to bind to gree device: %s", device_info)
    #    except DeviceTimeoutError:
    #        _LOGGER.error("Timeout trying to bind to gree device: %s", device_info)

    #    _LOGGER.info(
    #        "Adding Gree device %s at %s:%i",
    #        device.device_info.name,
    #        device.device_info.ip,
    #        device.device_info.port,
    #    )
    #    coordo = DeviceDataUpdateCoordinator(self.hass, device)
    #    self.hass.data[DOMAIN][COORDINATORS].append(coordo)
    #    await coordo.async_refresh()
    #
    #    async_dispatcher_send(self.hass, DISPATCH_DEVICE_DISCOVERED, coordo)

    # async def device_update(self, device_info: DeviceInfo) -> None:
    #    """Handle updates in device information, update if ip has changed."""
    #    for coordinator in self.hass.data[DOMAIN][COORDINATORS]:
    #        if coordinator.device.device_info.mac == device_info.mac:
    #            coordinator.device.device_info.ip = device_info.ip
    #            await coordinator.async_refresh()
