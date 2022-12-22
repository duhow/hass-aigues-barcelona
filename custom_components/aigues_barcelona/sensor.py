"""Platform for sensor integration."""
#from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfVolume
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""

    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    contract = config["contract"]
    try:
        client = AiguesApiClient(username, password, contract=contract)

        login = await hass.async_add_executor_job(client.login)
        if not login:
            _LOGGER.warning("Wrong username and/or password")
            return

    except Exception:
        _LOGGER.warning("Unable to create Aigues Barcelona Client")
        return

    async_add_entities([ContadorAgua(client)])

class ContadorAgua(SensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
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
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return UnitOfVolume.CUBIC_METERS

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.hass.data[DOMAIN]['temperature']
