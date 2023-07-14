"""Binary sensor entity implementation for C3 auxiliary inputs."""
from __future__ import annotations

from c3.consts import InOutStatus

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_C3_COORDINATOR, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plugwise switch based on config_entry."""
    c3_coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_C3_COORDINATOR]
    aux_inputs = hass.data[DOMAIN][config_entry.entry_id][Platform.BINARY_SENSOR]

    entities = []
    for aux_in_idx in aux_inputs:
        entities.append(C3AuxInEntity(c3_coordinator, aux_in_idx))

    async_add_entities(entities)


class C3AuxInEntity(CoordinatorEntity, BinarySensorEntity):
    """Entity representing the C3 panel auxiliary inputs."""

    def __init__(self, coordinator, idx) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self._coordinator = coordinator
        self._idx = idx
        self._attr_device_class = BinarySensorDeviceClass.DOOR.value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._coordinator.c3_panel.aux_in_status(self._idx) == InOutStatus.OPEN:
            self._attr_is_on = True
        elif self._coordinator.c3_panel.aux_in_status(self._idx) == InOutStatus.CLOSED:
            self._attr_is_on = False

        self.async_write_ha_state()

    @property
    def name(self):
        """Return the display name of this entity."""
        return f"Auxiliary Input {self._idx}"

    @property
    def should_poll(self):
        """Disable polling, the C3 coordinator polls."""
        return False

    @property
    def unique_id(self):
        """Get unique ID."""
        return f"{self._coordinator.c3_panel.serial_number}-in{self._idx}"

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:door-sensor"
