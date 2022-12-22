"""Config flow for integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL
)
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .api import AiguesApiClient

_LOGGER = logging.getLogger(__name__)

ACCOUNT_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        #vol.Optional(CONF_SCAN_INTERVAL, default=const.DEFAULT_SCAN_PERIOD): cv.time_period_seconds
    }
)

async def validate_credentials(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    # QUICK check DNI/NIF. TODO improve
    if len(username) != 9 or not username[0:8].isnumeric():
        raise InvalidUsername

    try:
        api = AiguesApiClient(username, password)
        _LOGGER.info("Attempting to login")
        login = await hass.async_add_executor_job(api.login)
        if not login:
            raise InvalidAuth
        contracts = api.contract_id

        if len(contracts) > 1:
            raise NotImplementedError("Multiple contracts are not supported")
        return {"contract": contracts[0]}

    except Exception:
        return False

class AiguesBarcelonaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle configuration step from UI."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=ACCOUNT_CONFIG_SCHEMA
            )

        errors = {}

        try:
            info = await validate_credentials(self.hass, user_input)
            _LOGGER.debug(f"Result is {info}")
            if not info:
                raise InvalidAuth
            contract = info["contract"]

            await self.async_set_unique_id(contract.lower())
            self._abort_if_unique_id_configured()
        except NotImplementedError:
            errors["base"] = "not_implemented"
        except InvalidUsername:
            errors["base"] = "invalid_auth"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except AlreadyConfigured:
            errors["base"] = "already_configured"
        else:
            _LOGGER.debug(f"Creating entity with {user_input} and {contract=}")

            return self.async_create_entry(
                title=f"Aigua {contract}", data={**user_input, **info}
            )

        return self.async_show_form(
            step_id="user", data_schema=ACCOUNT_CONFIG_SCHEMA, errors=errors
        )

class AlreadyConfigured(HomeAssistantError):
    """Error to indicate integration is already configured."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate credentials are invalid"""

class InvalidUsername(HomeAssistantError):
    """Error to indicate invalid username"""
