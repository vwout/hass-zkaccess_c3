"""Coordinator class for the C3 panel entities."""
import asyncio
import logging
from datetime import timedelta
from typing import Any, TypeVar

import async_timeout
import requests
from c3 import C3, rtlog
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    MAJOR_VERSION,
    MINOR_VERSION,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AUX_ON_DURATION,
    CONF_UNLOCK_DURATION,
    DATA_C3_COORDINATOR,
    DEFAULT_AUX_ON_DURATION,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_UNLOCK_DURATION,
    DOMAIN,
    MANUFACTURER,
)

_DataT = TypeVar("_DataT")
_LOGGER = logging.getLogger(__name__)


class C3Coordinator(DataUpdateCoordinator):
    """ZKAccess C3 panel coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        host: str,
        port: int,
        password: str,
    ) -> None:
        """Initialize C3 coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=f"ZKAccess C3 @ {host}:{port}",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(
                seconds=config_entry.options.get(CONF_SCAN_INTERVAL)
                or DEFAULT_POLL_INTERVAL
            ),
        )

        self._password = password
        self._poll_timeout_count = 0
        self._entry_id = config_entry.entry_id
        self._attr_unique_id = self._entry_id

        self._status = rtlog.DoorAlarmStatusRecord()
        self._door_events: dict[rtlog.EventRecord, Any] = {}
        self.unlock_duration: int = (
            config_entry.options.get(CONF_UNLOCK_DURATION) or DEFAULT_UNLOCK_DURATION
        )
        self.aux_on_duration: int = (
            config_entry.options.get(CONF_AUX_ON_DURATION) or DEFAULT_AUX_ON_DURATION
        )

        config_entry.async_on_unload(
            config_entry.add_update_listener(self._update_options_listener)
        )

        self.c3_panel: C3 = C3(host, port)
        if self.c3_panel.connect(password):
            hass.data[DOMAIN][self._entry_id] = {
                DATA_C3_COORDINATOR: self,
                Platform.LOCK: list(range(1, self.c3_panel.nr_of_locks + 1)),
                Platform.SWITCH: list(range(1, self.c3_panel.nr_aux_out + 1)),
                Platform.BINARY_SENSOR: list(range(1, self.c3_panel.nr_aux_in + 1)),
            }

            # Cache door settings
            if self.c3_panel.nr_of_locks:
                self.c3_panel.door_settings(1)

            device_registry = dr.async_get(hass)
            device_info = {
                "config_entry_id": self._entry_id,
                "identifiers": {(DOMAIN, self.c3_panel.serial_number)},
                "manufacturer": MANUFACTURER,
                "model": "C3/inBio",
                "name": (self.c3_panel.device_name if not "?" else "")
                or config_entry.title,
                "sw_version": self.c3_panel.firmware_version,
            }
            if MAJOR_VERSION >= 2023 and MINOR_VERSION >= 11:
                device_info["serial_number"] = self.c3_panel.serial_number
            device_registry.async_get_or_create(**device_info)
        else:
            raise UpdateFailed(f"Connection to C3 {host} failed.")

    @property
    def status(self) -> rtlog.DoorAlarmStatusRecord:
        """Return the last received Door/Alarm status."""
        return self._status

    def last_door_event(self, door_id: int) -> rtlog.EventRecord:
        """Return the last received Event."""
        return (
            self._door_events[door_id]
            if door_id in self._door_events
            else rtlog.EventRecord()
        )

    async def _update_options_listener(
        self, hass: HomeAssistant, config_entry: ConfigEntry
    ):
        """Handle options update."""
        self.update_interval = timedelta(
            seconds=config_entry.options.get(CONF_SCAN_INTERVAL)
            or DEFAULT_POLL_INTERVAL
        )
        self.unlock_duration = (
            config_entry.options.get(CONF_UNLOCK_DURATION) or DEFAULT_UNLOCK_DURATION
        )
        self.aux_on_duration = (
            config_entry.options.get(CONF_AUX_ON_DURATION) or DEFAULT_AUX_ON_DURATION
        )

    def _poll_rt_log(self) -> _DataT:
        """Fetch RT log from C3."""
        try:
            if not self.c3_panel.is_connected():
                self.c3_panel.connect(self._password)
        except ValueError as ex:
            raise UpdateFailed(f"Invalid response received: {ex}") from ex
        except Exception as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex

        updated = False

        try:
            last_record_is_status = False
            while not last_record_is_status:
                logs = self.c3_panel.get_rt_log()
                for log in logs:
                    if isinstance(log, rtlog.DoorAlarmStatusRecord):
                        self._status = log
                        last_record_is_status = True
                    elif isinstance(log, rtlog.EventRecord):
                        if log.port_nr > 0:
                            self._door_events[log.port_nr] = log
                    updated = True
        except ConnectionError as ex:
            _LOGGER.error("Realtime log update failed: %s", ex)

        if updated:
            self._poll_timeout_count = 0
        else:
            # Disconnect explicitly, so a re-connect can be performed at the next attempt
            try:
                self.c3_panel.disconnect()
            finally:
                pass

        return updated

    async def _async_update_data(self) -> _DataT:
        """Fetch RT log with handling of timeouts.

        The RT logs are retrieved, with a small timeout of 5 seconds.
        When multiple consecutive fetch actions fail, the connection to the panel
        is actively disconnected to reset the connection at the next poll attempt.
        """
        try:
            async with async_timeout.timeout(5):
                return self._poll_rt_log()
        except (asyncio.TimeoutError, requests.exceptions.Timeout):
            self._poll_timeout_count = self._poll_timeout_count + 1
            if self._poll_timeout_count > 5:
                # Disconnect explicitly, so a re-connect can be performed at the next attempt
                try:
                    self.c3_panel.disconnect()
                finally:
                    pass
            raise
