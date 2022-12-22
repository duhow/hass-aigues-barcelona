"""Platform for sensor integration."""
#from __future__ import annotations

from homeassistant.core import HomeAssistant, CoreState, callback
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
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

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""

    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    contract = config[CONF_CONTRACT]
    try:
        client = AiguesApiClient(username, password, contract=contract)

        _LOGGER.info("Attempting to login in setup_platform")
        login = await hass.async_add_executor_job(client.login)
        if not login:
            _LOGGER.warning("Wrong username and/or password")
            return

    except Exception:
        _LOGGER.warning("Unable to create Aigues Barcelona Client")
        return

    async_add_entities([ContadorAgua(client)])

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities
):
    """Set up entry."""
    hass.data.setdefault(DOMAIN, {})

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

    # add sensor entities
    async_add_entities([ContadorAgua(coordinator)])

    # register websockets
    async_register_websockets(hass)

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
        self.hass = hass
        self.reset = prev_data is None

        self.contract = contract.upper()
        self.id = contract.lower()

        # init data shared store
        hass.data[DOMAIN][self.contract] = {}

        # the api object
        #self._api = AiguesApiClientHelper(
        #    username,
        #    password,
        #    contract,
        #    data=prev_data,
        #)

        # shared storage
        # making self._data to reference hass.data[const.DOMAIN][self.id.upper()] so we can use it like an alias
        #self._data = hass.data[DOMAIN][self.id.upper()]
        #self._data.update(
        #    {
        #        const.DATA_STATE: const.STATE_LOADING,
        #        const.DATA_ATTRIBUTES: {x: None for x in ATTRIBUTES},
        #    }
        #)

        #if prev_data is not None:
        #    self._load_data(preprocess=True)

        #self.statistics = EdataStatistics(
        #    self.hass, self.id, self._billing is not None, self.reset, self._datadis
        #)
        super().__init__(
            hass,
            _LOGGER,
            name=self.id,
            update_interval=timedelta(minutes=240),
        )


class ContadorAgua(CoordinatorEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = coordinator.name
        self._data = coordinator.hass.data[DOMAIN][coordinator.id.upper()]
        self._coordinator = coordinator
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return 'Consumo de Agua'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:water-pump"

    @property
    def native_value(self):
        return self._data.get("state", -1)

    @property
    def device_class(self) -> str:
        return SensorDeviceClass.WATER

    @property
    def state_class(self) -> str:
        return "total"

    @property
    def unit_of_measurement(self) -> str:
        return UnitOfVolume.CUBIC_METERS

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = 55 # TEST
