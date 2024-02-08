"""Integration for Aigues de Barcelona."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_TOKEN
from homeassistant.const import CONF_USERNAME
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import AiguesApiClient
from .const import DOMAIN

# from homeassistant.exceptions import ConfigEntryNotReady

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    # TODO Change after fixing Recaptcha.
    api = AiguesApiClient(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    api.set_token(entry.data.get(CONF_TOKEN))

    if api.is_token_expired():
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH},
            data=entry,
        )
        return False
        raise ConfigEntryAuthFailed

    # try:
    #    await hass.async_add_executor_job(api.login)
    # except:
    #    raise ConfigEntryNotReady

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        if entry.entry_id in hass.data[DOMAIN].keys():
            hass.data[DOMAIN].pop(entry.entry_id)
    if not hass.data[DOMAIN]:
        del hass.data[DOMAIN]

    return unload_ok
