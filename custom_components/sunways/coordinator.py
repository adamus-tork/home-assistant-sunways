"""Update coordinatior for the Sunways integration."""

from datetime import timedelta
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.client import SunwaysClient, SunwaysStationOverview
from .api.exceptions import SunwaysClientException
from .const import SensorKeys

SCAN_INTERVAL = timedelta(seconds=60)


def convert_to_kilo(value: float | None, unit: str) -> float:
    if value is None:
        return 0.0
    if unit.startswith('k'):
        return value
    if unit.startswith('M'):
        return value * 1000
    return round(value / 1000, 2)

def convert_to_mega(value: float | None, unit: str) -> float:
    if value is None:
        return 0.0
    if unit.startswith('k'):
        return round(value / 1000, 2)
    if unit.startswith('M'):
        return value
    return round(value / 1000 / 1000, 2)


class SunwaysStationOverviewUpdateCoordinator(DataUpdateCoordinator[SunwaysStationOverview]):
    """Coordinator for getting details about the station."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        client: SunwaysClient,
        station_id: str
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            logger,
            name="Sunways API Data - Station",
            update_interval=SCAN_INTERVAL,
        )
        self._client = client
        self._station_id = station_id

    async def _async_update_data(self):
        """Fetch data from API endpoint."""

        try:
            async with asyncio.timeout(10):
                overview = await self._client.get_station_overview(self._station_id)

                return {
                    'id': self._station_id,
                    'sensors': {
                        SensorKeys.SOLAR_POWER: convert_to_kilo(overview.solar_power, overview.solar_power_unit),
                        SensorKeys.INSTALLED_POWER: convert_to_kilo(overview.installed_power, overview.installed_power_unit),
                        SensorKeys.EFFICIENCY: overview.solar_installed_ratio if overview.solar_installed_ratio else 0.0,
                        SensorKeys.LOAD_POWER: convert_to_kilo(overview.load_power, overview.load_power_unit),
                        SensorKeys.GRID_POWER_CONSUMPTION: convert_to_kilo(overview.grid_power_consumption, overview.grid_power_unit),
                        SensorKeys.GRID_POWER_RETURN: convert_to_kilo(overview.grid_power_return, overview.grid_power_unit),
                        SensorKeys.DAILY_GENERATION: convert_to_kilo(overview.daily_generation, overview.daily_generation_unit),
                        SensorKeys.MONTHLY_GENERATION: convert_to_kilo(overview.monthly_generation, overview.monthly_generation_unit),
                        SensorKeys.YEARLY_GENERATION: convert_to_mega(overview.yearly_generation, overview.yearly_generation_unit),
                        SensorKeys.TOTAL_GENERATION: convert_to_mega(overview.total_generation, overview.total_generation_unit)
                    }
                }
        except SunwaysClientException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
