from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import secrets
import string
import time
import uuid

import aiohttp
import paho.mqtt.client as mqtt

from .const import (
    API_BASE,
    API_SECRET,
    APP_TYPE,
    APP_VERSION,
    VENDOR,
)

_LOGGER = logging.getLogger(__name__)


class RefossError(Exception):
    pass


class RefossAuthError(RefossError):
    pass


class RefossConnectionError(
    RefossError
):
    pass


class RefossApi:
    def __init__(
        self,
        hass,
        email,
        password,
    ):
        self.hass = hass
        self.email = email
        self.password = password

        self.user_id = None
        self.key = None
        self.token = None

        self.api_url = API_BASE
        self.mqtt_host = None

        self.client = None
        self.app_id = None

        self.topic_user = None
        self.topic_reply = None

        self.connected = False

        self.devices = {}

        self._pending = {}
        self._push_callback = None

        # Serialize refreshes so parallel polls only sign in once.
        self._auth_lock = asyncio.Lock()
        self._auth_failed = False

    @staticmethod
    def _md5(value):
        return hashlib.md5(
            value.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _nonce():
        alphabet = (
            string.ascii_uppercase
            + string.digits
        )

        return "".join(
            secrets.choice(alphabet)
            for _ in range(16)
        )

    def _envelope(
        self,
        params,
    ):
        raw = json.dumps(
            params,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        encoded = (
            base64.b64encode(raw)
            .decode("ascii")
        )

        timestamp = int(
            time.time() * 1000
        )

        nonce = self._nonce()

        sign = self._md5(
            API_SECRET
            + str(timestamp)
            + nonce
            + encoded
        )

        return {
            "params": encoded,
            "sign": sign,
            "timestamp": timestamp,
            "nonce": nonce,
        }

    @staticmethod
    def _is_auth_error(data):
        """Return True when Refoss reports an expired or rejected session."""
        fields = (
            "info",
            "message",
            "msg",
            "error",
            "errorMessage",
            "error_code",
        )
        message = " ".join(
            str(data.get(field, ""))
            for field in fields
            if data.get(field) is not None
        ).casefold()

        return any(
            marker in message
            for marker in (
                "token",
                "unauthorized",
                "unauthorised",
                "not authorized",
                "not authorised",
                "authentication failed",
                "authorization failed",
                "auth failed",
                "session expired",
                "invalid session",
                "login required",
                "please login",
                "please sign in",
                "not logged in",
            )
        )

    async def _async_refresh_token(self, failed_token):
        """Refresh the Refoss session once when the cloud rejects its token."""
        async with self._auth_lock:
            if self._auth_failed:
                raise RefossAuthError(
                    "Le compte Refoss doit être reconnecté"
                )

            # Another concurrent request may already have refreshed the token.
            if self.token != failed_token:
                return

            try:
                await self.async_login()
            except RefossAuthError:
                self._auth_failed = True
                raise

    async def _post(
        self,
        base_url,
        path,
        params,
        token=None,
    ):
        """Post to Refoss and renew an expired session once if needed."""
        try:
            return await self._post_once(
                base_url,
                path,
                params,
                token=token,
            )
        except RefossAuthError:
            if not token:
                raise

            await self._async_refresh_token(token)

            return await self._post_once(
                self.api_url,
                path,
                params,
                token=self.token,
            )

    async def _post_once(
        self,
        base_url,
        path,
        params,
        token=None,
    ):
        headers = {
            "Content-Type":
                "application/json",
            "AppVersion":
                APP_VERSION,
            "AppType":
                APP_TYPE,
            "AppLanguage":
                "FR",
            "vender":
                VENDOR,
            "User-Agent":
                f"Refoss/{APP_VERSION}",
        }

        if token:
            headers[
                "Authorization"
            ] = "Basic " + token

        payload = self._envelope(
            params
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    base_url + path,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(
                        total=20
                    ),
                ) as response:

                    text = (
                        await response.text()
                    )

                    if response.status in (401, 403) and (
                        token or path.endswith("/signIn")
                    ):
                        raise RefossAuthError(
                            "Jeton ou identifiants Refoss refusés "
                            f"(HTTP {response.status})"
                        )

                    if response.status != 200:
                        raise RefossConnectionError(
                            f"HTTP {response.status}"
                        )

        except asyncio.TimeoutError as exc:
            raise RefossConnectionError(
                "Timeout Refoss"
            ) from exc

        except aiohttp.ClientError as exc:
            raise RefossConnectionError(
                str(exc)
            ) from exc

        try:
            data = json.loads(text)

        except json.JSONDecodeError as exc:
            raise RefossConnectionError(
                "Réponse Refoss invalide"
            ) from exc

        api_status = data.get(
            "apiStatus"
        )

        if api_status not in (
            None,
            0,
        ):
            info = data.get(
                "info",
                "Erreur Refoss",
            )

            if path.endswith("/signIn") or (
                token
                and (
                    api_status in (401, 403, "401", "403")
                    or self._is_auth_error(data)
                )
            ):
                raise RefossAuthError(str(info))

            raise RefossError(str(info))

        return data.get(
            "data",
            data,
        )

    async def async_login(self):
        data = await self._post(
            API_BASE,
            "/v1/Auth/signIn",
            {
                "email": self.email,
                "password": self._md5(
                    self.password
                ),
                "accountCountryCode":
                    "FR",
                "encryption": 1,
                "agree": 1,
            },
        )

        self.user_id = str(
            data["userid"]
        )

        self.key = str(
            data["key"]
        )

        self.token = str(
            data["token"]
        )

        self.api_url = (
            data.get("domain")
            or API_BASE
        )

        self.mqtt_host = data.get(
            "mqttDomain"
        )

        self._auth_failed = False

        return data

    async def async_get_devices(
        self,
    ):
        data = await self._post(
            self.api_url,
            "/v1/Device/devList",
            {},
            token=self.token,
        )

        devices = []

        if isinstance(
            data,
            list,
        ):
            devices = data

        elif isinstance(
            data,
            dict,
        ):
            for key in (
                "list",
                "devices",
                "deviceList",
                "devList",
            ):
                value = data.get(
                    key
                )

                if isinstance(
                    value,
                    list,
                ):
                    devices = value
                    break

        result = {}

        for device in devices:
            device_uuid = device.get(
                "uuid"
            )

            if not device_uuid:
                continue

            result[
                device_uuid
            ] = device

        self.devices = result

        return result

    def set_push_callback(
        self,
        callback,
    ):
        self._push_callback = (
            callback
        )

    async def async_connect_mqtt(
        self,
    ):
        if self.connected:
            return

        loop = self.hass.loop

        self.app_id = (
            uuid.uuid4().hex
        )

        self.topic_user = (
            f"/app/"
            f"{self.user_id}"
            f"/subscribe"
        )

        self.topic_reply = (
            f"/app/"
            f"{self.user_id}"
            f"-{self.app_id}"
            f"/subscribe"
        )

        mqtt_password = (
            self._md5(
                self.user_id
                + self.key
            )
        )

        def on_connect(
            client,
            userdata,
            flags,
            reason_code,
            properties,
        ):
            if getattr(
                reason_code,
                "is_failure",
                False,
            ):
                _LOGGER.error(
                    "Connexion MQTT "
                    "Refoss refusée : %s",
                    reason_code,
                )
                return

            _LOGGER.debug(
                "Connexion MQTT "
                "Refoss réussie : %s",
                reason_code,
            )

            client.subscribe(
                self.topic_user,
                qos=1,
            )

            client.subscribe(
                self.topic_reply,
                qos=1,
            )

            loop.call_soon_threadsafe(
                self._set_connected,
                True,
            )

        def on_disconnect(
            client,
            userdata,
            disconnect_flags,
            reason_code,
            properties,
        ):
            loop.call_soon_threadsafe(
                self._set_connected,
                False,
            )

        def on_message(
            client,
            userdata,
            msg,
        ):
            try:
                data = json.loads(
                    msg.payload.decode(
                        "utf-8",
                        errors="replace",
                    )
                )

            except Exception:
                return

            loop.call_soon_threadsafe(
                self._handle_message,
                data,
            )

        self.client = mqtt.Client(
            callback_api_version=(
                mqtt.CallbackAPIVersion.VERSION2
            ),
            client_id=(
                "app:"
                + self.app_id
            ),
            protocol=mqtt.MQTTv311,
        )

        self.client.username_pw_set(
            username=self.user_id,
            password=mqtt_password,
        )

        await self.hass.async_add_executor_job(
            self.client.tls_set
        )

        self.client.on_connect = (
            on_connect
        )

        self.client.on_disconnect = (
            on_disconnect
        )

        self.client.on_message = (
            on_message
        )

        await self.hass.async_add_executor_job(
            self.client.connect,
            self.mqtt_host,
            443,
            60,
        )

        self.client.loop_start()

        for _ in range(50):
            if self.connected:
                return

            await asyncio.sleep(
                0.1
            )

        raise RefossConnectionError(
            "Connexion MQTT "
            "Refoss impossible"
        )

    def _set_connected(
        self,
        value,
    ):
        self.connected = value

    def _handle_message(
        self,
        message,
    ):
        header = message.get(
            "header",
            {}
        )

        message_id = header.get(
            "messageId"
        )

        method = header.get(
            "method"
        )

        if (
            message_id
            and message_id
            in self._pending
            and method
            in (
                "GETACK",
                "SETACK",
                "ERROR",
            )
        ):
            future = self._pending.pop(
                message_id
            )

            if not future.done():
                future.set_result(
                    message
                )

        if (
            method == "PUSH"
            and self._push_callback
        ):
            self._push_callback(
                message
            )

    def _build_message(
        self,
        device_uuid,
        namespace,
        method,
        payload,
    ):
        message_id = (
            uuid.uuid4().hex
        )

        timestamp = int(
            time.time()
        )

        sign = self._md5(
            message_id
            + self.key
            + str(timestamp)
        )

        message = {
            "header": {
                "from":
                    self.topic_reply,
                "messageId":
                    message_id,
                "method":
                    method,
                "namespace":
                    namespace,
                "payloadVersion":
                    1,
                "sign":
                    sign,
                "timestamp":
                    timestamp,
                "triggerSrc":
                    "Android",
                "uuid":
                    device_uuid,
            },
            "payload": payload,
        }

        return (
            message_id,
            message,
        )

    async def async_request(
        self,
        device_uuid,
        namespace,
        method="GET",
        payload=None,
        timeout=10,
    ):
        if payload is None:
            payload = {}

        if not self.connected:
            await self.async_connect_mqtt()

        (
            message_id,
            message,
        ) = self._build_message(
            device_uuid,
            namespace,
            method,
            payload,
        )

        future = (
            self.hass.loop
            .create_future()
        )

        self._pending[
            message_id
        ] = future

        topic = (
            f"/appliance/"
            f"{device_uuid}"
            f"/subscribe"
        )

        info = self.client.publish(
            topic,
            json.dumps(
                message,
                separators=(",", ":"),
            ),
            qos=1,
        )

        await self.hass.async_add_executor_job(
            info.wait_for_publish
        )

        try:
            return await asyncio.wait_for(
                future,
                timeout=timeout,
            )

        except asyncio.TimeoutError:
            self._pending.pop(
                message_id,
                None,
            )
            return None

    async def async_get_all(
        self,
        device_uuid,
    ):
        return await self.async_request(
            device_uuid,
            "Appliance.System.All",
        )

    async def async_get_electricity(
        self,
        device_uuid,
    ):
        return await self.async_request(
            device_uuid,
            "Appliance.Control.Electricity",
            timeout=5,
        )

    async def async_get_consumption(
        self,
        device_uuid,
    ):
        return await self.async_request(
            device_uuid,
            "Appliance.Control.ConsumptionX",
            timeout=5,
        )

    async def async_set_switch(
        self,
        device_uuid,
        onoff,
    ):
        return await self.async_request(
            device_uuid,
            "Appliance.Control.ToggleX",
            method="SET",
            payload={
                "togglex": {
                    "channel": 0,
                    "onoff": (
                        1
                        if onoff
                        else 0
                    ),
                }
            },
        )

    async def async_disconnect(
        self,
    ):
        if not self.client:
            return

        try:
            self.client.loop_stop()

            await (
                self.hass
                .async_add_executor_job(
                    self.client.disconnect
                )
            )

        except Exception:
            pass

        self.client = None
        self.connected = False
