"""Lock entity implementation for C3 doors."""
from __future__ import annotations

from typing import Any

from c3.consts import ControlOutputAddress, InOutStatus
from c3.controldevice import ControlDeviceOutput
from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_C3_COORDINATOR, DOMAIN
from .coordinator import C3Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plugwise switch based on config_entry."""
    c3_coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_C3_COORDINATOR]
    locks = hass.data[DOMAIN][config_entry.entry_id][Platform.LOCK]

    async_add_entities(C3LockEntity(c3_coordinator, lock_idx) for lock_idx in locks)


class C3LockEntity(CoordinatorEntity, LockEntity):
    """Entity representing the C3 panel door locks."""

    def __init__(self, coordinator: C3Coordinator, idx) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self._coordinator = coordinator
        self._idx = idx
        """The lock does not support opening, it only represents status"""
        self._attr_supported_features: LockEntityFeature = LockEntityFeature(0)
        self._attr_is_locked = None
        self._attr_is_locking = None
        self._attr_is_unlocking = None
        self._attr_is_jammed = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.c3_panel.serial_number)},
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._coordinator.c3_panel.lock_status(self._idx) == InOutStatus.OPEN:
            self._attr_is_locked = False
            self._attr_is_unlocking = False
        elif self._coordinator.c3_panel.lock_status(self._idx) == InOutStatus.CLOSED:
            self._attr_is_locked = True
            self._attr_is_locking = False
        else:
            self._attr_is_locked = None

        self._attr_is_jammed = None  # self._coordinator.status.has_alarm(self._idx, AlarmStatus.DOOR_OPEN_TIMEOUT)

        self.async_write_ha_state()

    @property
    def name(self):
        """Return the display name of this entity."""
        return f"Door {self._idx}"

    @property
    def should_poll(self):
        """Disable polling, the C3 coordinator polls."""
        return False

    @property
    def unique_id(self):
        """Get unique ID."""
        return f"{self._coordinator.c3_panel.serial_number}-lock{self._idx}"

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:door"

    def lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        control_command = ControlDeviceOutput(
            self._idx, ControlOutputAddress.DOOR_OUTPUT, 0
        )
        self._coordinator.c3_panel.control_device(control_command)
        self._attr_is_locking = True

    def unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        control_command = ControlDeviceOutput(
            self._idx,
            ControlOutputAddress.DOOR_OUTPUT,
            self._coordinator.unlock_duration,
        )
        self._coordinator.c3_panel.control_device(control_command)
        self._attr_is_unlocking = True
