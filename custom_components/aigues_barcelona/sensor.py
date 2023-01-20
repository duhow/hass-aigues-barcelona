"""Platform for sensor integration."""
#from __future__ import annotations

from homeassistant.core import HomeAssistant, CoreState, callback
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_START,
    UnitOfVolume,
)
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_CONTRACT,
)

from .api import AiguesApiClient

from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities
):
    """Set up entry."""
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.info("calling async_setup_entry")

    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    contract = config_entry.data[CONF_CONTRACT]

    platform = entity_platform.async_get_current_platform()

    coordinator = ContratoAgua(
        hass,
        username,
        password,
        contract,
        prev_data=None
    )

    # postpone first refresh to speed up startup
    @callback
    async def async_first_refresh(*args):
        """Force the component to assess the first refresh."""
        await coordinator.async_refresh()

    if hass.state == CoreState.running:
        await async_first_refresh()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, async_first_refresh)

    _LOGGER.info("about to add entities")
    # add sensor entities
    async_add_entities([ContadorAgua(coordinator)])

    return True

class ContratoAgua(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        contract: str,
        prev_data=None,
    ) -> None:
        """Initialize the data handler."""
        self.reset = prev_data is None

        self.contract = contract.upper()
        self.id = contract.lower()

        # init data shared store
        hass.data[DOMAIN][self.contract] = {}

        # the api object
        self._api = AiguesApiClient(
            username,
            password,
            contract
        )

        super().__init__(
            hass,
            _LOGGER,
            name=self.id,
            update_interval=timedelta(minutes=240),
        )

    async def _async_update_data(self):
        return True


class ContadorAgua(CoordinatorEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._data = coordinator.hass.data[DOMAIN][coordinator.id.upper()]
        self._attr_name = f"Contador {coordinator.name}"
        self._attr_unique_id = coordinator.id
        self._attr_icon = "mdi:water-pump"
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        #self._attr_state = None
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        self._attr_state_class = "total"

    @property
    def native_value(self):
        return self._data.get("state", -1)

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_state = 55 # TEST
