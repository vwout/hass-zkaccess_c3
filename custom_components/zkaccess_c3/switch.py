"""Switch entity implementation for C3 auxiliary outputs."""
from __future__ import annotations

from typing import Any

from c3.consts import ControlOutputAddress, InOutStatus
from c3.controldevice import ControlDeviceCancelAlarms, ControlDeviceOutput
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
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
    aux_outputs = hass.data[DOMAIN][config_entry.entry_id][Platform.SWITCH]
    door_alarms = hass.data[DOMAIN][config_entry.entry_id][Platform.LOCK]

    async_add_entities(
        C3AuxOutEntity(c3_coordinator, aux_out_idx) for aux_out_idx in aux_outputs
    )
    async_add_entities(
        C3AlarmEntity(c3_coordinator, door_idx) for door_idx in door_alarms
    )


class C3AuxOutEntity(CoordinatorEntity, SwitchEntity):
    """Entity representing the C3 panel auxiliary outputs."""

    def __init__(self, coordinator: C3Coordinator, idx) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self._coordinator = coordinator
        self._idx = idx

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._coordinator.c3_panel.aux_out_status(self._idx) == InOutStatus.OPEN:
            self._attr_is_on = True
        elif self._coordinator.c3_panel.aux_out_status(self._idx) == InOutStatus.CLOSED:
            self._attr_is_on = False

        self.async_write_ha_state()

    @property
    def name(self) -> str | None:
        """Return the display name of this entity."""
        return f"Auxiliary Output {self._idx}"

    @property
    def should_poll(self) -> bool:
        """Disable polling, the C3 coordinator polls."""
        return False

    @property
    def unique_id(self) -> str | None:
        """Get unique ID."""
        return f"{self._coordinator.c3_panel.serial_number}-out{self._idx}"

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:door-open"

    def turn_on(self, **kwargs: Any) -> None:
        """Activate the auxiliary output."""
        control_command = ControlDeviceOutput(
            self._idx,
            ControlOutputAddress.AUX_OUTPUT,
            self._coordinator.aux_on_duration,
        )
        self._coordinator.c3_panel.control_device(control_command)

    def turn_off(self, **kwargs: Any) -> None:
        """Deactivate the auxiliary output."""
        control_command = ControlDeviceOutput(
            self._idx, ControlOutputAddress.AUX_OUTPUT, 0
        )
        self._coordinator.c3_panel.control_device(control_command)


class C3AlarmEntity(CoordinatorEntity, SwitchEntity):
    """Entity representing the C3 panel auxiliary outputs."""

    def __init__(self, coordinator: C3Coordinator, idx) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self._coordinator = coordinator
        self._idx = idx
        self._attr_extra_state_attributes = {
            "last_event_time": None,
            "last_event": None,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self._coordinator.status.has_alarm(self._idx)
        self._attr_extra_state_attributes["last_event_time"] = str(
            self._coordinator.last_door_event(self._idx).time_second
        )
        self._attr_extra_state_attributes["last_event"] = repr(
            self._coordinator.last_door_event(self._idx).event_type
        )

        self.async_write_ha_state()

    @property
    def name(self) -> str | None:
        """Return the display name of this entity."""
        return f"Door {self._idx} alarm"

    @property
    def should_poll(self) -> bool:
        """Disable polling, the C3 coordinator polls."""
        return False

    @property
    def unique_id(self) -> str | None:
        """Get unique ID."""
        return f"{self._coordinator.c3_panel.serial_number}-alarm{self._idx}"

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:door-sensor"

    def turn_on(self, **kwargs: Any) -> None:
        """Perform no action.

        You can't actively turn on an alarm.
        """

    def turn_off(self, **kwargs: Any) -> None:
        """Reset the alarm - all alarms."""
        self._coordinator.c3_panel.control_device(ControlDeviceCancelAlarms())
        self._attr_is_on = False
