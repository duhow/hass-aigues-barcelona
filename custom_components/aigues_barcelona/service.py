import logging
from .const import DOMAIN

from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .sensor import ContratoAgua

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def handle_reset_and_refresh_data(call: ServiceCall) -> None:
        contract = next(iter(hass.data[DOMAIN]), None)
        if not contract:
            _LOGGER.error("No contracts available")
            return
        _LOGGER.warning(f"Performing reset and refresh for {contract}")

        #await clear_stored_data(hass, contract)
        await fetch_historic_data(hass, contract)

    hass.services.async_register(DOMAIN, "reset_and_refresh_data", handle_reset_and_refresh_data)
    return True

async def clear_stored_data(hass: HomeAssistant, contract: str) -> None:
    coordinator = hass.data[DOMAIN].get(contract.upper()).get("coordinator")
    if not coordinator:
        _LOGGER.error(f"Contract {contract} not found")
        return
    
    _LOGGER.debug(dir(coordinator))

    await coordinator._clear_statistics()

async def fetch_historic_data(hass: HomeAssistant, contract: str) -> None:
    coordinator = hass.data[DOMAIN].get(contract.upper()).get("coordinator")
    if not coordinator:
        _LOGGER.error(f"Contract {contract} not found")
        return

    today = datetime.now()
    one_year_ago = today - timedelta(days=365)

    current_date = one_year_ago
    while current_date < today:
        await coordinator._async_import_statistics(
            await hass.async_add_executor_job(
                coordinator._api.consumptions_week, current_date, contract
            )
        )
        current_date += timedelta(weeks=1)
