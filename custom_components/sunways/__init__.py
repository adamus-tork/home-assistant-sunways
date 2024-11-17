"""The Sunways integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from types import MappingProxyType

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import  ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import CONF_STATION_ID
from .config_flow import create_sunways_client
from .coordinator import SunwaysStationOverviewUpdateCoordinator
from .api.client import SunwaysClient

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]
SCAN_INTERVAL = timedelta(seconds=60)

@dataclass(slots=True)
class SunwaysRuntimeData:
    """Class for storing sunways data."""

    client: SunwaysClient
    coordinator: SunwaysStationOverviewUpdateCoordinator

type SunwaysConfigEntry = ConfigEntry[SunwaysRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: SunwaysConfigEntry) -> bool:
    """Set up the sensors from a ConfigEntry."""

    try:
        client = await create_sunways_client(
            hass,
            MappingProxyType(entry.data),
        )
    except Exception as err:
        raise ConfigEntryNotReady from err

    coordinator = SunwaysStationOverviewUpdateCoordinator(
        hass,
        _LOGGER,
        client,
        entry.data[CONF_STATION_ID]
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = SunwaysRuntimeData(client=client, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SunwaysConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
