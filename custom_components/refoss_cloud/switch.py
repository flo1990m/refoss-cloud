from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .entity import RefossEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    known = set()

    def add_devices(device_uuids):
        entities = []

        for device_uuid in device_uuids:
            if device_uuid in known:
                continue

            known.add(device_uuid)
            entities.append(RefossSwitch(coordinator, device_uuid))

        if entities:
            async_add_entities(entities)

    add_devices(coordinator.devices.keys())

    unsubscribe = async_dispatcher_connect(
        hass,
        f"{DOMAIN}_{entry.entry_id}_new_devices",
        add_devices,
    )

    entry.async_on_unload(unsubscribe)


class RefossSwitch(RefossEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_switch"

    @property
    def is_on(self):
        return self.refoss_state.get("onoff")

    @property
    def extra_state_attributes(self):
        attributes = {}
        power = self.refoss_state.get("power")
        supports_electricity = self.refoss_state.get("supports_electricity")

        if supports_electricity is True:
            attributes["power"] = power

            if self.is_on and power is not None:
                attributes["power_display"] = f"{power:.0f} W"
            else:
                attributes["power_display"] = ""

        return attributes

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_switch(
            self.device_uuid,
            True,
        )

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_switch(
            self.device_uuid,
            False,
        )
