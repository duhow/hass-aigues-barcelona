import logging
from .const import DOMAIN

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

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
        # await clear_stored_data(hass, coordinator)
        await fetch_historic_data(hass, coordinator)

    hass.services.async_register(
        DOMAIN, "reset_and_refresh_data", handle_reset_and_refresh_data
    )
    return True


async def clear_stored_data(hass: HomeAssistant, coordinator) -> None:
    await coordinator._clear_statistics()


async def fetch_historic_data(hass: HomeAssistant, coordinator) -> None:
    await coordinator.import_old_consumptions(days=365)
