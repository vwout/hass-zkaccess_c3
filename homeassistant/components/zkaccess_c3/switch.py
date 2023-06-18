"""Switch entity implementation for C3 auxiliary outputs."""
from __future__ import annotations

from typing import Any

from c3.consts import ControlOutputAddress, InOutStatus
from c3.controldevice import ControlDeviceOutput

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_C3_COORDINATOR, DEFAULT_AUX_ON_DURATION, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plugwise switch based on config_entry."""
    c3_coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_C3_COORDINATOR]
    aux_outputs = hass.data[DOMAIN][config_entry.entry_id][Platform.SWITCH]

    entities = []
    for aux_out_idx in aux_outputs:
        entities.append(C3AuxOutEntity(c3_coordinator, aux_out_idx))

    async_add_entities(entities)


class C3AuxOutEntity(CoordinatorEntity, SwitchEntity):
    """Entity representing the C3 panel auxiliary outputs."""

    def __init__(self, coordinator, idx) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self._coordinator = coordinator
        self._idx = idx
        self._attr_extra_state_attributes = {"aux_on_duration": DEFAULT_AUX_ON_DURATION}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._coordinator.c3_panel.aux_out_status(self._idx) == InOutStatus.OPEN:
            self._attr_is_on = True
        elif self._coordinator.c3_panel.aux_out_status(self._idx) == InOutStatus.CLOSED:
            self._attr_is_on = False

        self.async_write_ha_state()

    @property
    def name(self):
        """Return the display name of this entity."""
        return f"Auxiliary Output {self._idx}"

    @property
    def should_poll(self):
        """Disable polling, the C3 coordinator polls."""
        return False

    @property
    def unique_id(self):
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
            self._attr_extra_state_attributes["aux_on_duration"],
        )
        self._coordinator.c3_panel.control_device(control_command)

    def turn_off(self, **kwargs):
        """Deactivate the auxiliary output."""
        control_command = ControlDeviceOutput(
            self._idx, ControlOutputAddress.AUX_OUTPUT, 0
        )
        self._coordinator.c3_panel.control_device(control_command)
