from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    API_BASE,
    CONF_API_URL,
    CONF_EMAIL,
    CONF_KEY,
    CONF_MQTT_HOST,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USER_ID,
    DOMAIN,
)
from .refoss_api import (
    RefossApi,
    RefossAuthError,
    RefossConnectionError,
    RefossMfaInvalid,
    RefossMfaRequired,
)

_LOGGER = logging.getLogger(__name__)
CONF_MFA_CODE = "mfa_code"


class RefossCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._mfa_context = None

    async def _async_login(self, email, password, mfa_code=None):
        """Perform a Refoss login, optionally supplying the MFA code."""
        api = RefossApi(self.hass, email, password)
        return await api.async_login(mfa_code=mfa_code)

    @staticmethod
    def _session_data(login_data):
        """Persist the authenticated session, never the one-time MFA code."""
        return {
            CONF_USER_ID: str(login_data["userid"]),
            CONF_KEY: str(login_data["key"]),
            CONF_TOKEN: str(login_data["token"]),
            CONF_API_URL: login_data.get("domain") or API_BASE,
            CONF_MQTT_HOST: login_data.get("mqttDomain"),
        }

    async def _async_finish_login(self, mode, email, password, login_data):
        """Complete the flow after a successful password/MFA login."""
        user_id = str(login_data["userid"])
        session_data = self._session_data(login_data)
        await self.async_set_unique_id(user_id)

        if mode == "user":
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=email,
                data={
                    CONF_EMAIL: email,
                    CONF_PASSWORD: password,
                    **session_data,
                },
            )

        if mode == "reconfigure":
            self._abort_if_unique_id_mismatch()
            entry = self._get_reconfigure_entry()
            return self.async_update_reload_and_abort(
                entry,
                title=email,
                data_updates={
                    CONF_EMAIL: email,
                    CONF_PASSWORD: password,
                    **session_data,
                },
            )

        if mode == "reauth":
            self._abort_if_unique_id_mismatch()
            entry = self._get_reauth_entry()
            return self.async_update_reload_and_abort(
                entry,
                data_updates={
                    CONF_PASSWORD: password,
                    **session_data,
                },
            )

        raise RuntimeError(f"Unknown Refoss login flow mode: {mode}")

    def _start_mfa(self, mode, email, password):
        """Keep credentials in memory while the user completes the MFA step."""
        self._mfa_context = {
            "mode": mode,
            "email": email,
            "password": password,
        }

    async def _async_show_mfa_form(self, errors=None):
        if not self._mfa_context:
            return self.async_abort(reason="unknown")
        return self.async_show_form(
            step_id="mfa",
            data_schema=vol.Schema({vol.Required(CONF_MFA_CODE): str}),
            errors=errors or {},
            description_placeholders={"email": self._mfa_context["email"]},
        )

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()
            password = user_input[CONF_PASSWORD]

            try:
                login_data = await self._async_login(email, password)
            except RefossMfaRequired:
                self._start_mfa("user", email, password)
                return await self._async_show_mfa_form()
            except RefossMfaInvalid:
                errors["base"] = "invalid_mfa"
            except RefossAuthError:
                errors["base"] = "invalid_auth"
            except RefossConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Erreur pendant la connexion Refoss")
                errors["base"] = "unknown"
            else:
                return await self._async_finish_login(
                    "user", email, password, login_data
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_mfa(self, user_input=None):
        """Complete initial setup, reconfigure, or reauth with a one-time code."""
        if not self._mfa_context:
            return self.async_abort(reason="unknown")

        errors = {}
        if user_input is not None:
            context = self._mfa_context
            try:
                login_data = await self._async_login(
                    context["email"],
                    context["password"],
                    user_input[CONF_MFA_CODE].strip(),
                )
            except RefossMfaRequired:
                errors["base"] = "mfa_required"
            except RefossMfaInvalid:
                errors["base"] = "invalid_mfa"
            except RefossAuthError:
                errors["base"] = "invalid_auth"
            except RefossConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Erreur pendant la validation MFA Refoss")
                errors["base"] = "unknown"
            else:
                self._mfa_context = None
                return await self._async_finish_login(
                    context["mode"],
                    context["email"],
                    context["password"],
                    login_data,
                )

        return await self._async_show_mfa_form(errors)

    async def async_step_reconfigure(self, user_input=None):
        """Allow the user to update Refoss account credentials manually."""
        entry = self._get_reconfigure_entry()
        errors = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()
            password = user_input[CONF_PASSWORD]

            try:
                login_data = await self._async_login(email, password)
            except RefossMfaRequired:
                self._start_mfa("reconfigure", email, password)
                return await self._async_show_mfa_form()
            except RefossMfaInvalid:
                errors["base"] = "invalid_mfa"
            except RefossAuthError:
                errors["base"] = "invalid_auth"
            except (RefossConnectionError, OSError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Erreur pendant la reconfiguration Refoss")
                errors["base"] = "unknown"
            else:
                return await self._async_finish_login(
                    "reconfigure", email, password, login_data
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL, default=entry.data[CONF_EMAIL]): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=schema, errors=errors
        )

    async def async_step_reauth(self, entry_data):
        """Start reauthentication for an existing Refoss account."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Ask for the current Refoss password and update the existing entry."""
        entry = self._get_reauth_entry()
        errors = {}

        if user_input is not None:
            password = user_input[CONF_PASSWORD]
            email = entry.data[CONF_EMAIL]

            try:
                login_data = await self._async_login(email, password)
            except RefossMfaRequired:
                self._start_mfa("reauth", email, password)
                return await self._async_show_mfa_form()
            except RefossMfaInvalid:
                errors["base"] = "invalid_mfa"
            except RefossAuthError:
                errors["base"] = "invalid_auth"
            except RefossConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Erreur pendant la réauthentification Refoss")
                errors["base"] = "unknown"
            else:
                return await self._async_finish_login(
                    "reauth", email, password, login_data
                )

        schema = vol.Schema({vol.Required(CONF_PASSWORD): str})
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"email": entry.data[CONF_EMAIL]},
        )
