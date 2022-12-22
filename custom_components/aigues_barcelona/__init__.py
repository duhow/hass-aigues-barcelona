"""Example integration."""

import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL
)
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DEFAULT_SCAN_PERIOD

_LOGGER = logging.getLogger(__name__)

ACCOUNT_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_PERIOD): cv.time_period,
    }
)

async def async_setup(hass: HomeAssistant, config: ConfigType, discovery_info=None) -> bool:
    """ Set up the domain. """

    if DOMAIN not in config:
        _LOGGER.debug(
            "Nothing to import from configuration.yaml, loading from Integrations",
        )
        return True
