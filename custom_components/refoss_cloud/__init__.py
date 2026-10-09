from __future__ import annotations

from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import RefossCoordinator
from .refoss_api import RefossApi


async def async_setup_entry(hass, entry):
    api = RefossApi(
        hass,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )

    coordinator = RefossCoordinator(
        hass,
        api,
        entry,
    )

    await coordinator.async_initialize()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)

        await coordinator.async_shutdown()
        await coordinator.api.async_disconnect()

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok
