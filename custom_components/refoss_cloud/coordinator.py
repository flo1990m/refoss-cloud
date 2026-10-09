from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
import time

from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DEVICE_DISCOVERY_INTERVAL,
    DOMAIN,
    SLOW_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

FAST_ELECTRICITY_INTERVAL = 5


class RefossCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, entry):
        super().__init__(
            hass,
            _LOGGER,
            name="Refoss Cloud",
            update_interval=timedelta(seconds=SLOW_UPDATE_INTERVAL),
        )

        self.api = api
        self.entry = entry
        self.devices = {}
        self.states = {}
        self._last_discovery = 0
        self._electricity_task = None
        self._stopping = False

        self.api.set_push_callback(self._handle_push)

    async def async_initialize(self):
        await self.api.async_login()
        self.devices = await self.api.async_get_devices()
        await self.api.async_connect_mqtt()
        self._last_discovery = time.monotonic()
        await self.async_refresh()

        self._electricity_task = self.hass.async_create_task(
            self._electricity_loop()
        )

    async def _async_update_data(self):
        try:
            now = time.monotonic()

            if now - self._last_discovery >= DEVICE_DISCOVERY_INTERVAL:
                await self._async_discover_devices()
                self._last_discovery = now

            await asyncio.gather(
                *[
                    self._async_update_slow(device_uuid, device)
                    for device_uuid, device in list(self.devices.items())
                ],
                return_exceptions=True,
            )

            return self.states

        except Exception as exc:
            raise UpdateFailed(str(exc)) from exc

    async def _electricity_loop(self):
        while not self._stopping:
            try:
                tasks = []

                for device_uuid, device in list(self.devices.items()):
                    state = self._ensure_state(device_uuid)

                    if (
                        state.get("onoff") is True
                        and state.get("supports_electricity") is True
                    ):
                        tasks.append(self._async_update_electricity(device_uuid))

                    elif (
                        state.get("onoff") is False
                        and state.get("supports_electricity") is True
                    ):
                        state["power"] = 0
                        state["current"] = 0

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    self.async_set_updated_data(self.states)

            except asyncio.CancelledError:
                return

            except Exception as exc:
                _LOGGER.debug("Refoss electricity loop error: %s", exc)

            await asyncio.sleep(FAST_ELECTRICITY_INTERVAL)

    async def _async_discover_devices(self):
        old_uuids = set(self.devices)
        devices = await self.api.async_get_devices()
        self.devices = devices
        new_uuids = set(devices) - old_uuids

        if new_uuids:
            _LOGGER.info("Detected %s new Refoss device(s)", len(new_uuids))

            for device_uuid in new_uuids:
                self._ensure_state(device_uuid)

            async_dispatcher_send(
                self.hass,
                f"{DOMAIN}_{self.entry.entry_id}_new_devices",
                new_uuids,
            )

    def _ensure_state(self, device_uuid):
        if device_uuid not in self.states:
            device = self.devices.get(device_uuid, {})
            model = str(device.get("deviceType", "")).lower()
            known_electricity = model == "mss310"

            self.states[device_uuid] = {
                "online": False,
                "onoff": None,
                "power": 0 if known_electricity else None,
                "voltage": None,
                "current": 0 if known_electricity else None,
                "energy_today": None,
                "supports_electricity": True if known_electricity else None,
                "electricity_initialized": False,
                "electricity_probe_done": False,
                "supports_consumption": False,
            }

        return self.states[device_uuid]

    async def _async_update_slow(self, device_uuid, device):
        state = self._ensure_state(device_uuid)

        try:
            response = await self.api.async_get_all(device_uuid)

            if response:
                payload = response.get("payload", {})
                all_data = payload.get("all", {})
                system = all_data.get("system", {})
                online = system.get("online", {})
                state["online"] = online.get("status") == 1
                digest = all_data.get("digest", {})
                togglex = digest.get("togglex")

                if isinstance(togglex, list) and togglex:
                    state["onoff"] = bool(togglex[0].get("onoff", 0))

                    if (
                        state["onoff"] is False
                        and state.get("supports_electricity") is True
                    ):
                        state["power"] = 0
                        state["current"] = 0

        except Exception as exc:
            _LOGGER.debug(
                "System.All error for %s: %s",
                device.get("devName", device_uuid),
                exc,
            )

        should_probe_electricity = (
            not state.get("electricity_initialized")
            and (
                state.get("supports_electricity") is True
                or not state.get("electricity_probe_done")
            )
        )

        if should_probe_electricity:
            try:
                electricity = await self.api.async_get_electricity(device_uuid)

                if electricity:
                    payload = electricity.get("payload", {})
                    data = payload.get("electricity")

                    if isinstance(data, dict):
                        state["supports_electricity"] = True
                        state["electricity_initialized"] = True
                        state["electricity_probe_done"] = True
                        self._apply_electricity(state, data)

                elif state.get("supports_electricity") is not True:
                    state["supports_electricity"] = False
                    state["electricity_probe_done"] = True

            except Exception as exc:
                _LOGGER.debug(
                    "Electricity probe error for %s: %s",
                    device.get("devName", device_uuid),
                    exc,
                )

                if state.get("supports_electricity") is not True:
                    state["supports_electricity"] = False
                    state["electricity_probe_done"] = True

        try:
            consumption = await self.api.async_get_consumption(device_uuid)

            if consumption:
                payload = consumption.get("payload", {})
                values = payload.get("consumptionx")

                if isinstance(values, list):
                    state["supports_consumption"] = True
                    today = time.strftime("%Y-%m-%d")
                    found_today = False

                    for item in values:
                        if item.get("date") == today:
                            state["energy_today"] = item.get("value", 0) / 1000
                            found_today = True
                            break

                    if not found_today:
                        state["energy_today"] = 0

        except Exception as exc:
            _LOGGER.debug(
                "ConsumptionX error for %s: %s",
                device.get("devName", device_uuid),
                exc,
            )

    def _apply_electricity(self, state, data):
        power = data.get("power")
        voltage = data.get("voltage")
        current = data.get("current")

        if power is not None:
            state["power"] = power / 1000

        if voltage is not None:
            state["voltage"] = voltage / 10

        if current is not None:
            state["current"] = current / 1000

        if state.get("onoff") is False:
            state["power"] = 0
            state["current"] = 0

    async def _async_update_electricity(self, device_uuid):
        state = self._ensure_state(device_uuid)

        try:
            electricity = await self.api.async_get_electricity(device_uuid)

            if not electricity:
                return

            payload = electricity.get("payload", {})
            data = payload.get("electricity")

            if not isinstance(data, dict):
                return

            state["supports_electricity"] = True
            state["electricity_initialized"] = True
            self._apply_electricity(state, data)

        except Exception as exc:
            _LOGGER.debug(
                "Electricity error for %s: %s",
                device_uuid,
                exc,
            )

    async def _async_update_electricity_now(self, device_uuid):
        await self._async_update_electricity(device_uuid)
        self.async_set_updated_data(self.states)

    def _handle_push(self, message):
        header = message.get("header", {})
        namespace = header.get("namespace")
        device_uuid = header.get("uuid")

        if not device_uuid:
            source = header.get("from", "")

            if source.startswith("/appliance/"):
                parts = source.split("/")

                if len(parts) >= 3:
                    device_uuid = parts[2]

        if not device_uuid or device_uuid not in self.devices:
            return

        state = self._ensure_state(device_uuid)

        if namespace == "Appliance.Control.ToggleX":
            togglex = message.get("payload", {}).get("togglex")

            if isinstance(togglex, list) and togglex:
                onoff = bool(togglex[0].get("onoff", 0))
                state["onoff"] = onoff
                state["online"] = True

                if not onoff and state.get("supports_electricity") is True:
                    state["power"] = 0
                    state["current"] = 0

                elif onoff and state.get("supports_electricity") is True:
                    self.hass.async_create_task(
                        self._async_update_electricity_now(device_uuid)
                    )

        self.async_set_updated_data(self.states)

    async def async_set_switch(self, device_uuid, value):
        response = await self.api.async_set_switch(device_uuid, value)

        if response is not None:
            state = self._ensure_state(device_uuid)
            state["onoff"] = bool(value)

            if not value and state.get("supports_electricity") is True:
                state["power"] = 0
                state["current"] = 0

            elif value and state.get("supports_electricity") is True:
                self.hass.async_create_task(
                    self._async_update_electricity_now(device_uuid)
                )

            self.async_set_updated_data(self.states)

    async def async_shutdown(self):
        self._stopping = True

        if self._electricity_task:
            self._electricity_task.cancel()

            try:
                await self._electricity_task
            except asyncio.CancelledError:
                pass

            self._electricity_task = None
