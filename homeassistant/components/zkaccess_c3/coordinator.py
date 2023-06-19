"""Coordinator class for the C3 panel entities."""
from datetime import timedelta
import logging

from c3 import C3, rtlog

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AUX_ON_DURATION,
    CONF_UNLOCK_DURATION,
    DATA_C3_COORDINATOR,
    DEFAULT_AUX_ON_DURATION,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_UNLOCK_DURATION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class C3Coordinator(DataUpdateCoordinator):
    """ZKAccess C3 panel coordinator."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, host: str, port: int
    ) -> None:
        """Initialize C3 coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=f"Zkaccess C3 @ {host}:{port}",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(
                seconds=config_entry.options.get(CONF_SCAN_INTERVAL)
                or DEFAULT_POLL_INTERVAL
            ),
        )

        self._entry_id = config_entry.entry_id
        self._status = rtlog.DoorAlarmStatusRecord()
        self.unlock_duration = (
            config_entry.options.get(CONF_UNLOCK_DURATION) or DEFAULT_UNLOCK_DURATION
        )
        self.aux_on_duration = (
            config_entry.options.get(CONF_AUX_ON_DURATION) or DEFAULT_AUX_ON_DURATION
        )

        config_entry.async_on_unload(
            config_entry.add_update_listener(self._update_options_listener)
        )

        self.c3_panel: C3 = C3(host, port)
        if self.c3_panel.connect():
            coordinator_data = {
                DATA_C3_COORDINATOR: self,
                Platform.LOCK: [],
                Platform.SWITCH: [],
                Platform.BINARY_SENSOR: [],
            }

            coordinator_data[Platform.LOCK] = list(
                range(1, self.c3_panel.nr_of_locks + 1)
            )
            coordinator_data[Platform.BINARY_SENSOR] = list(
                range(1, self.c3_panel.nr_aux_in + 1)
            )
            coordinator_data[Platform.SWITCH] = list(
                range(1, self.c3_panel.nr_aux_out + 1)
            )

            hass.data[DOMAIN][self._entry_id] = coordinator_data
        else:
            raise UpdateFailed(f"Connection to C3 {host} failed.")

    @property
    def status(self) -> rtlog.DoorAlarmStatusRecord:
        """Return the last received Door/Alarm status."""
        return self._status

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

    async def _async_update_data(self):
        """Fetch data from API endpoint."""

        try:
            if not self.c3_panel.is_connected():
                self.c3_panel.connect()

            updated = False

            try:
                last_record_is_status = False
                while not last_record_is_status:
                    logs = self.c3_panel.get_rt_log()
                    for log in logs:
                        if isinstance(log, rtlog.DoorAlarmStatusRecord):
                            self._status = log
                            last_record_is_status = True

                        updated = True

            except ConnectionError as ex:
                _LOGGER.error("Realtime log update failed: %s", ex)

                # Attempt to reconnect
                try:
                    self.c3_panel.disconnect()
                finally:
                    pass

            return updated

        except Exception as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex
