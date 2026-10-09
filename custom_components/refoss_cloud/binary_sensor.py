from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
)
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import RefossEntity


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
            if device_uuid in known:
                continue

            known.add(
                device_uuid
            )

            entities.append(
                RefossOnlineSensor(
                    coordinator,
                    device_uuid,
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


class RefossOnlineSensor(
    RefossEntity,
    BinarySensorEntity,
):
    _attr_has_entity_name = True
    _attr_name = "Connexion"

    _attr_device_class = (
        BinarySensorDeviceClass.CONNECTIVITY
    )
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator,
        device_uuid,
    ):
        super().__init__(
            coordinator,
            device_uuid,
        )

        self._attr_unique_id = (
            f"{device_uuid}_online"
        )

    @property
    def is_on(self):
        return bool(
            self.refoss_state.get(
                "online"
            )
        )

    @property
    def available(self):
        return True
