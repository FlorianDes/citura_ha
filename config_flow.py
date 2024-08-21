"""Config flow for Citura integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import CituraAPI
from .const import CONF_DIRECTION, CONF_LINE, CONF_START, DOMAIN
from .helper import unique_id_from_config

_LOGGER = logging.getLogger(__name__)


class CituraConfigFlow(ConfigFlow, domain=DOMAIN):
    """Citura config flow."""

    VERSION = 1
    MINOR_VERSION = 0

    _user_inputs: dict = {}

    def __init__(self):
        """Init the config flow."""
        self._line: list[dict] = []
        self._stations: list[dict] = []
        self._client: CituraAPI.CituraAPI = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """First step."""
        errors: dict[str, str] = {}

        if self._client is None:
            session = async_get_clientsession(self.hass)
            self._client = CituraAPI.CituraAPI(session=session)

        if user_input is None:
            self._stations = await self._client.async_get_all_stations()
            data_schema = vol.Schema(
                {
                    vol.Required("from"): vol.In(
                        [station["stop_name"] for station in self._stations]
                    ),
                }
            )
            return self.async_show_form(
                step_id="user",
                data_schema=data_schema,
                errors=errors,
            )

        self._user_inputs.update(user_input)
        return await self.async_step_line()

    async def async_step_line(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Async user step to set up the connection."""
        errors: dict[str, str] = {}

        if user_input is None:
            self._line = await self._client.async_get_line_by_station(
                self._user_inputs[CONF_START]
            )
            data_schema = vol.Schema(
                {
                    vol.Required("line"): vol.In(
                        [line["line_id"] for line in self._line]
                    ),
                    vol.Required("direction"): bool,
                }
            )
            return self.async_show_form(
                step_id="line",
                data_schema=data_schema,
                errors=errors,
            )

        self._user_inputs.update(user_input)
        unique_id = unique_id_from_config(self._user_inputs)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        session = async_get_clientsession(self.hass)
        citura = CituraAPI.CituraAPI(
            self._user_inputs[CONF_LINE],
            self._user_inputs[CONF_START],
            self._user_inputs[CONF_DIRECTION],
            session,
        )
        try:
            await citura.async_get_data()
        except Exception as e:  # noqa: BLE001, F841
            errors["base"] = "cannot_connect"

        return self.async_create_entry(
            title=unique_id,
            data=self._user_inputs,
        )
