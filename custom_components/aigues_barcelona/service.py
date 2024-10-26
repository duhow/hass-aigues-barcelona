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

        coordinator = hass.data[DOMAIN].get(contract).get("coordinator")
        if not coordinator:
            _LOGGER.error(f"Contract coordinator for {contract} not found")
            return

        _LOGGER.warning(f"Performing reset and refresh for {contract}")

        # TODO: Not working - Detected unsafe call not in recorder thread
        #await clear_stored_data(hass, coordinator)
        await fetch_historic_data(hass, coordinator, contract)

    hass.services.async_register(DOMAIN, "reset_and_refresh_data", handle_reset_and_refresh_data)
    return True

async def clear_stored_data(hass: HomeAssistant, coordinator) -> None:
    await coordinator._clear_statistics()

async def fetch_historic_data(hass: HomeAssistant, coordinator, contract: str = None) -> None:
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)

    current_date = one_year_ago
    while current_date < today:
        consumptions = await hass.async_add_executor_job(
            coordinator._api.consumptions_week, current_date, contract
        )

        if not consumptions:
            _LOGGER.warning(f"No data available for {current_date}")
        else:
            await coordinator._async_import_statistics(consumptions)

        current_date += timedelta(weeks=1)
