"""Simple Http client for Sunways REST User API."""

from typing import NamedTuple, Any
from aiohttp.client import ClientSession

from .connection import (
    SunwaysApiConnection,
    TokenJar,
    API_STATION_LIST,
    API_STATION_OVERVIEW
)


class SunwaysStation(NamedTuple):
    """Identifies a station registered for the user at sunways."""

    name: str
    id: str


class SunwaysStationOverview():
    """Overview of a PV station"""

    def __init__(self, data: dict[str, Any]):
        self._data = data

    @property
    def id(self) -> str:
        """ID of the station."""
        return self._data["id"]

    @property
    def solar_power(self) -> float:
        return self._data["pac"]

    @property
    def solar_power_unit(self) -> str:
        return self._data["pacUnit"]

    @property    
    def installed_power(self) -> float:
        return self._data["instatlledPower"]

    @property
    def installed_power_unit(self) -> str:
        return self._data["instatlledPowerUnit"]

    @property
    def solar_installed_ratio(self) -> float:
        return self._data["powerRatio"]

    @property
    def load_power(self) -> float:
        return self._data["pLoad"]

    @property
    def load_power_unit(self) -> str:
        return self._data["pLoadUnit"]
    
    @property
    def grid_power_consumption(self) -> float:
        return self._data["pmeterTotal"] if self._data["arrowGridInverter"] == 1 else 0.0
    
    @property
    def grid_power_return(self) -> float:
        return self._data["pmeterTotal"] if self._data["arrowInverterGrid"] == 1 else 0.0
    
    @property
    def grid_power_unit(self) -> float:
        return self._data["pmeterTotalUnit"]

    @property
    def daily_generation(self) -> float:
        return self._data["eDay"]

    @property
    def daily_generation_unit(self) -> str:
        return self._data["eDayUnit"]

    @property
    def monthly_generation(self) -> float:
        return self._data["eMonth"]

    @property
    def monthly_generation_unit(self) -> str:
        return self._data["eMonthUnit"]

    @property
    def yearly_generation(self) -> float:
        return self._data["eYear"]

    @property
    def yearly_generation_unit(self) -> str:
        return self._data["eYearUnit"]

    @property
    def total_generation(self) -> float:
        return self._data["eTotal"]

    @property
    def total_generation_unit(self) -> str:
        return self._data["eTotalUnit"]


class SunwaysClient:
    """
    Simple client for Sunways API
    """

    def __init__(
        self,
        email: str,
        password: str,
        websession: ClientSession,
        token_jar: TokenJar | None = None
    ):
        self._api = SunwaysApiConnection(email, password, websession, token_jar)

    async def __aenter__(self):
        await self._api.__aenter__()
        return self

    async def __aexit__(self, *args) -> bool:
        """Call when the client is disposed."""
        # Close the web session, if we created it (i.e. it was not passed in)
        return await self._api.__aexit__(*args)

    async def get_stations(self) -> list[SunwaysStation]:
        """Get the availabile stations."""
        result = await self._api.request("get", API_STATION_LIST)

        stations = [SunwaysStation(s["name"], s["id"]) for s in result["records"]]
        return stations

    async def get_station_overview(self, station_id: str) -> SunwaysStationOverview:
        """Get the overview of a single station."""
        result = await self._api.request("get", API_STATION_OVERVIEW, {'id': station_id})

        station = SunwaysStationOverview(result)
        return station
