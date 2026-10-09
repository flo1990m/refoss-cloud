from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

REDACT_DEVICE_KEYS = {
    "uuid",
    "devUuid",
    "userId",
    "userid",
    "token",
    "key",
}


def _sanitized_devices(coordinator) -> list[dict[str, Any]]:
    devices = []

    for device_uuid, device in coordinator.devices.items():
        state = coordinator.states.get(device_uuid, {})

        devices.append(
            {
                "device": async_redact_data(dict(device), REDACT_DEVICE_KEYS),
                "state": {
                    "online": state.get("online"),
                    "onoff": state.get("onoff"),
                    "supports_electricity": state.get("supports_electricity"),
                    "supports_consumption": state.get("supports_consumption"),
                    "power": state.get("power"),
                    "voltage": state.get("voltage"),
                    "current": state.get("current"),
                    "energy_today": state.get("energy_today"),
                },
            }
        )

    return devices


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics without account credentials or device UUIDs."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "integration": {
            "domain": DOMAIN,
            "device_count": len(coordinator.devices),
        },
        "devices": _sanitized_devices(coordinator),
    }
