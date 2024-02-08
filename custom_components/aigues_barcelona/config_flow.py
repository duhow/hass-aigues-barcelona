"""Config flow for integration."""
from __future__ import annotations

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_TOKEN
from homeassistant.const import CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import AiguesApiClient
from .const import CONF_CONTRACT
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ACCOUNT_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)
TOKEN_SCHEMA = vol.Schema({vol.Required(CONF_TOKEN): cv.string})


def check_valid_nif(username: str) -> bool:
    """Quick check for NIF/DNI/NIE and return if valid."""

    if len(username) != 9:
        return False

    # DNI 12341234D
    if username[0:8].isnumeric() and not username[-1].isnumeric():
        return True

    # NIF X2341234H
    if (
        username[0].upper() in ["X", "Y", "Z"]
        and username[1:8].isnumeric()
        and not username[-1].isnumeric()
    ):
        return True

    return False


async def validate_credentials(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    token = data.get(CONF_TOKEN)

    if not check_valid_nif(username):
        raise InvalidUsername

    try:
        api = AiguesApiClient(username, password)
        if token:
            api.set_token(token)
        else:
            _LOGGER.info("Attempting to login")
            login = await hass.async_add_executor_job(api.login)
            if not login:
                raise InvalidAuth
            _LOGGER.info("Login succeeded!")
        contracts = await hass.async_add_executor_job(api.contracts, username)

        available_contracts = [x["contractDetail"]["contractNumber"] for x in contracts]
        return {CONF_CONTRACT: available_contracts}

    except Exception:
        _LOGGER.debug(f"Last data: {api.last_response}")
        if not api.last_response:
            return False

        if (
            isinstance(api.last_response, dict)
            and api.last_response.get("path") == "recaptchaClientResponse"
        ):
            raise RecaptchaAppeared

        if (
            isinstance(api.last_response, str)
            and api.last_response == "JWT Token Revoked"
        ):
            raise TokenExpired

        return False


class AiguesBarcelonaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2
    stored_input = dict()

    async def async_step_token(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Return to user step with stored input (previous user creds) and the
        current provided token."""
        return await self.async_step_user({**self.stored_input, **user_input})

    async def async_step_reauth(self, entry) -> FlowResult:
        """Request OAuth Token again when expired."""
        # get previous entity content back to flow
        self.entry = entry
        if hasattr(entry, "data"):
            self.stored_input = entry.data
        else:
            # FIXME: for DataUpdateCoordinator, entry is not valid,
            # as it contains only sensor data. Missing entry_id.
            # Reauth when restarting works.
            self.stored_input = entry
        return await self.async_step_reauth_confirm(None)

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Return to user step with stored input (previous user creds) and the
        current provided token."""
        if not user_input:
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=TOKEN_SCHEMA
            )

        errors = {}
        user_input = {**self.stored_input, **user_input}
        try:
            info = await validate_credentials(self.hass, user_input)
            contracts = info[CONF_CONTRACT]
            if contracts != self.stored_input.get(CONF_CONTRACT):
                _LOGGER.error("Reauth failed, contract does not match stored one")
                raise InvalidAuth

            self.hass.config_entries.async_update_entry(self.entry, data=user_input)
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.entry.entry_id)
            )

            return self.async_abort(reason="reauth_successful")

        except InvalidUsername:
            errors["base"] = "invalid_auth"
        except InvalidAuth:
            errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=TOKEN_SCHEMA, errors=errors
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle configuration step from UI."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=ACCOUNT_CONFIG_SCHEMA
            )

        errors = {}

        try:
            self.stored_input = user_input
            info = await validate_credentials(self.hass, user_input)
            _LOGGER.debug(f"Result is {info}")
            if not info:
                raise InvalidAuth
            contracts = info[CONF_CONTRACT]

            await self.async_set_unique_id(user_input["username"])
            self._abort_if_unique_id_configured()
        except NotImplementedError:
            errors["base"] = "not_implemented"
        except TokenExpired:
            errors["base"] = "token_expired"
            return self.async_show_form(
                step_id="token", data_schema=TOKEN_SCHEMA, errors=errors
            )
        except RecaptchaAppeared:
            # Ask for OAuth Token to login.
            return self.async_show_form(step_id="token", data_schema=TOKEN_SCHEMA)
        except InvalidUsername:
            errors["base"] = "invalid_auth"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except AlreadyConfigured:
            errors["base"] = "already_configured"
        else:
            _LOGGER.debug(f"Creating entity with {user_input} and {contracts=}")
            nif_oculto = user_input[CONF_USERNAME][-3:][0:2]

            return self.async_create_entry(
                title=f"Aigua ****{nif_oculto}", data={**user_input, **info}
            )

        return self.async_show_form(
            step_id="user", data_schema=ACCOUNT_CONFIG_SCHEMA, errors=errors
        )


class AlreadyConfigured(HomeAssistantError):
    """Error to indicate integration is already configured."""


class RecaptchaAppeared(HomeAssistantError):
    """Error to indicate a Recaptcha appeared and requires an OAuth token
    issued."""


class TokenExpired(HomeAssistantError):
    """Error to indicate the OAuth token has expired."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate credentials are invalid."""


class InvalidUsername(HomeAssistantError):
    """Error to indicate invalid username."""
