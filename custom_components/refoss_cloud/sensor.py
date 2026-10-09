from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
)

from .const import DOMAIN
from .entity import RefossEntity


SENSORS = {
    "power": {
        "name": "Puissance",
        "device_class":
            SensorDeviceClass.POWER,
        "state_class":
            SensorStateClass.MEASUREMENT,
        "unit":
            UnitOfPower.WATT,
    },
    "voltage": {
        "name": "Tension",
        "device_class":
            SensorDeviceClass.VOLTAGE,
        "state_class":
            SensorStateClass.MEASUREMENT,
        "unit":
            UnitOfElectricPotential.VOLT,
    },
    "current": {
        "name": "Courant",
        "device_class":
            SensorDeviceClass.CURRENT,
        "state_class":
            SensorStateClass.MEASUREMENT,
        "unit":
            UnitOfElectricCurrent.AMPERE,
    },
    "energy_today": {
        "name": "Énergie aujourd'hui",
        "device_class":
            SensorDeviceClass.ENERGY,
        "state_class":
            SensorStateClass.TOTAL,
        "unit":
            UnitOfEnergy.KILO_WATT_HOUR,
    },
}


async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
):
    coordinator = hass.data[
        DOMAIN
    ][
        entry.entry_id
    ]

    known = set()

    def add_devices(
        device_uuids,
    ):
        entities = []

        for device_uuid in device_uuids:
            for key in SENSORS:
                unique = (
                    device_uuid,
                    key,
                )

                if unique in known:
                    continue

                known.add(
                    unique
                )

                entities.append(
                    RefossSensor(
                        coordinator,
                        device_uuid,
                        key,
                    )
                )

        if entities:
            async_add_entities(
                entities
            )

    add_devices(
        coordinator.devices.keys()
    )

    unsubscribe = (
        async_dispatcher_connect(
            hass,
            (
                f"{DOMAIN}_"
                f"{entry.entry_id}_"
                f"new_devices"
            ),
            add_devices,
        )
    )

    entry.async_on_unload(
        unsubscribe
    )


class RefossSensor(
    RefossEntity,
    SensorEntity,
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        device_uuid,
        sensor_key,
    ):
        super().__init__(
            coordinator,
            device_uuid,
        )

        description = (
            SENSORS[sensor_key]
        )

        self.sensor_key = (
            sensor_key
        )

        self._attr_unique_id = (
            f"{device_uuid}_"
            f"{sensor_key}"
        )

        self._attr_name = (
            description["name"]
        )

        self._attr_device_class = (
            description[
                "device_class"
            ]
        )

        self._attr_state_class = (
            description[
                "state_class"
            ]
        )

        self._attr_native_unit_of_measurement = (
            description["unit"]
        )

    @property
    def native_value(self):
        return self.refoss_state.get(
            self.sensor_key
        )

    @property
    def available(self):
        if not super().available:
            return False

        if self.sensor_key in (
            "power",
            "voltage",
            "current",
        ):
            return bool(
                self.refoss_state.get(
                    "supports_electricity"
                )
            )

        if (
            self.sensor_key
            == "energy_today"
        ):
            return bool(
                self.refoss_state.get(
                    "supports_consumption"
                )
            )

        return True
