"""Support for Citura."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DIRECTION, CONF_LINE, CONF_START, CONNECTIONS_COUNT, DOMAIN
from .coordinator import CituraDataUpdateCoordinator, DataConnection

_LOGGER = logging.getLogger(__name__)


DEFAULT_NAME = "Next Departure"

SCAN_INTERVAL = timedelta(seconds=10)


SENSOR_PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_START): cv.string,
        vol.Required(CONF_LINE): cv.string,
        vol.Required(CONF_DIRECTION): cv.boolean,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


@dataclass(kw_only=True, frozen=True)
class CituraSensorEntityDescription(SensorEntityDescription):
    """Describes Citura sensor entity."""

    value_fn: Callable[[DataConnection], StateType | datetime]

    index: int = 0


SENSORS: tuple[CituraSensorEntityDescription, ...] = (
    *[
        CituraSensorEntityDescription(
            key=f"departure{i or ''}",
            translation_key=f"departure{i}",
            device_class=SensorDeviceClass.TIMESTAMP,
            value_fn=lambda data_connection: data_connection["departure"],
            index=i,
        )
        for i in range(CONNECTIONS_COUNT)
    ],
    # CituraSensorEntityDescription(
    #     key="duration",
    #     device_class=SensorDeviceClass.DURATION,
    #     native_unit_of_measurement=UnitOfTime.SECONDS,
    #     value_fn=lambda data_connection: data_connection["duration"],
    # ),
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    unique_id = config_entry.unique_id or ""

    async_add_entities(
        CituraSensor(coordinator, description, unique_id) for description in SENSORS
    )


class CituraSensor(CoordinatorEntity[CituraDataUpdateCoordinator], SensorEntity):
    """Implementation of a Citura sensor."""

    entity_description: CituraSensorEntityDescription
    _attr_attribution = "Data provided by Citura"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CituraDataUpdateCoordinator,
        entity_description: CituraSensorEntityDescription,
        unique_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{unique_id}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="Citura",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        value = None
        if self.entity_description.index < len(self.coordinator.data):
            value = self.entity_description.value_fn(
                self.coordinator.data[self.entity_description.index]
            )
        return value

    @property
    def extra_state_attributes(self):
        """Return extra attributes of the sensor."""
        attributes = {}
        if self.entity_description.index < len(self.coordinator.data):
            attributes["destination"] = self.coordinator.data[
                self.entity_description.index
            ]["destination"]
            attributes["realtime"] = self.coordinator.data[
                self.entity_description.index
            ]["realtime"]
        return attributes
