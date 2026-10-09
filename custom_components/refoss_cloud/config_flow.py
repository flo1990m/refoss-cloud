from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    DOMAIN,
)
from .refoss_api import (
    RefossApi,
    RefossAuthError,
    RefossConnectionError,
)

_LOGGER = logging.getLogger(__name__)


class RefossCloudConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    VERSION = 1

    async def async_step_user(
        self,
        user_input=None,
    ):
        errors = {}

        if user_input is not None:
            email = (
                user_input[CONF_EMAIL]
                .strip()
                .lower()
            )

            password = user_input[
                CONF_PASSWORD
            ]

            api = RefossApi(
                self.hass,
                email,
                password,
            )

            try:
                login_data = (
                    await api.async_login()
                )

            except RefossAuthError:
                errors["base"] = (
                    "invalid_auth"
                )

            except RefossConnectionError:
                errors["base"] = (
                    "cannot_connect"
                )

            except Exception:
                _LOGGER.exception(
                    "Erreur pendant "
                    "la connexion Refoss"
                )
                errors["base"] = "unknown"

            else:
                user_id = str(
                    login_data["userid"]
                )

                await self.async_set_unique_id(
                    user_id
                )

                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_EMAIL
                ): str,
                vol.Required(
                    CONF_PASSWORD
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
