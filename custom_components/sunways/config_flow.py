"""Config flow for Sunways integration."""

from __future__ import annotations

import time
import logging
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, NamedTuple
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_STATION_ID, CONF_INITIAL_TOKEN
from .api.client import SunwaysClient, SunwaysStation
from .api.connection import TokenJar
from .api.exceptions import ConnectionFailed, LoginFailed, SunwaysClientException


_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_INITIAL_TOKEN): str
    }
)


async def create_sunways_client(
    hass: HomeAssistant,
    data: MappingProxyType[str, Any]
) -> SunwaysClient:
    """Create a Sunways client API for the given config entry."""

    email = data[CONF_EMAIL]
    password = data[CONF_PASSWORD]

    websession = async_get_clientsession(hass, verify_ssl=True)
    token_jar = None

    if CONF_INITIAL_TOKEN in data:
        token_jar = TokenJar(data[CONF_INITIAL_TOKEN], time.time())

    return SunwaysClient(email, password, websession, token_jar)


class UserInfo(NamedTuple):
    """Fetched user information."""

    stations: list[SunwaysStation]


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> UserInfo:
    """Validate the user input allows us to connect."""

    client = await create_sunways_client(hass, MappingProxyType(data))
    stations = await client.get_stations()
    
    return UserInfo(stations)


class SunwaysConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sunways."""

    VERSION = 1

    def __init__(self) -> None:
        """Create the config flow for a new integration."""
        self._config_data: dict[str, Any] = {}
        self._stations: list[SunwaysStation] = []

    async def async_step_user(
        self, 
        user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        info = None
        errors: dict[str, str] = {}
        if user_input is not None:
            #user_input[CONF_USER_AGENT] = USER_AGENT
            info = await self._test_login(user_input, errors)

        if info is None or user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )
        
        self._config_data.update(user_input)
        self._stations = info.stations
        if len(info.stations) > 1:
            return await self.async_step_station()
        return await self.async_step_station({CONF_STATION_ID: info.stations[0].id})

    async def async_step_station(
            self, 
            user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
        """Handle step to select station to manage."""

        if user_input is None:
            schema = vol.Schema(
                {
                    vol.Required(CONF_STATION_ID, CONF_STATION_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=s.id, label=s.name)
                                for s in self._stations
                            ],
                            multiple=False,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            )

            return self.async_show_form(step_id=CONF_STATION_ID, data_schema=schema)
        
        await self.async_set_unique_id(user_input[CONF_STATION_ID])
        self._abort_if_unique_id_configured()
        
        self._config_data.update(user_input)

        display_name = next(
            s for s in self._stations if s.id == user_input[CONF_STATION_ID]
        ).name

        return self.async_create_entry(title=display_name, data=self._config_data)
    
    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        self._config_data = dict(entry_data)
        return await self.async_step_reauth_confirm()
    
    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""

        errors: dict[str, str] = {}

        if user_input is not None:
            self._config_data.update(user_input)
            stations = await self._test_login(self._config_data, errors)

            if stations is not None:
                # Auth successful - update the config entry with the new credentials
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data=self._config_data
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_login(
        self, data: dict[str, Any], 
        errors: dict[str, str]
    ) -> UserInfo | None:
        try:
            info = await _validate_input(self.hass, data)
            if len(info.stations) > 0:
                return info
            errors["base"] = "no_stations_found"

        except ConnectionFailed:
            errors["base"] = "cannot_connect"
        except LoginFailed:
            errors["base"] = "invalid_auth"
        except SunwaysClientException as ex:
            _LOGGER.error("Unexpected API error: %s", ex)
            errors["base"] = "unknown"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        return None
