"""Support for Sunways inverter via cloud API."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SunwaysConfigEntry
from .const import DOMAIN, MANUFACTURER, SENSOR_DESCRIPTIONS, CONF_STATION_ID
from .coordinator import SunwaysStationOverviewUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SunwaysConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry setup."""
    coordinator = entry.runtime_data.coordinator

    await coordinator.async_config_entry_first_refresh()

    station_id = entry.data[CONF_STATION_ID]
    sensors: dict = coordinator.data['sensors']
    entities: list[InverterSensorEntity] = []

    for sensor_key in sensors.keys():
        description = SENSOR_DESCRIPTIONS[sensor_key]

        uid = f"{station_id}-{sensor_key}"
        entities.append(
            InverterSensorEntity(
                coordinator,
                station_id,
                entry.title,
                uid,
                description
            )
        )
    async_add_entities(entities)


class InverterSensorEntity(CoordinatorEntity, SensorEntity):
    """Class for a sensor."""

    has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: SunwaysStationOverviewUpdateCoordinator,
        station_id: str,
        station_name: str,
        uid: str,
        description: SensorEntityDescription
    ) -> None:
        """Initialize an inverter sensor."""
        super().__init__(coordinator, context=description.key)
        self.entity_description = description
        self._attr_unique_id = uid
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            manufacturer=MANUFACTURER,
            name=f"{MANUFACTURER} {station_name}",
        )

    @property
    def native_value(self):
        """State of this inverter attribute."""
        return self.coordinator.data['sensors'][self.coordinator_context]
