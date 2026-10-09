from __future__ import annotations

from homeassistant.helpers.device_registry import (
    DeviceInfo,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN


class RefossEntity(
    CoordinatorEntity
):
    def __init__(
        self,
        coordinator,
        device_uuid,
    ):
        super().__init__(
            coordinator
        )

        self.device_uuid = (
            device_uuid
        )

    @property
    def device(self):
        return (
            self.coordinator
            .devices[
                self.device_uuid
            ]
        )

    @property
    def refoss_state(self):
        return (
            self.coordinator
            .states.get(
                self.device_uuid,
                {},
            )
        )

    @property
    def available(self):
        return bool(
            self.refoss_state.get(
                "online",
                False,
            )
        )

    @property
    def device_info(self):
        device = self.device

        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.device_uuid,
                )
            },
            name=device.get(
                "devName",
                "Refoss",
            ),
            manufacturer="Refoss",
            model=device.get(
                "deviceType"
            ),
            hw_version=device.get(
                "hdwareVersion"
            ),
            sw_version=device.get(
                "fmwareVersion"
            ),
        )
