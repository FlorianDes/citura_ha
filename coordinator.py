"""DataUpdateCoordinator for the swiss_public_transport integration."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from . import CituraAPI
from .const import CONNECTIONS_COUNT, DEFAULT_UPDATE_TIME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DataConnection(TypedDict):
    """A connection data class."""

    departure: datetime | None
    # platform: str
    # remaining_time: str
    # start: str
    destination: str
    realtime: bool
    # train_number: str
    # transfers: int
    # delay: int


# def calculate_duration_in_seconds(duration_text: str) -> int | None:
#     """Transform and calculate the duration into seconds."""
#     # Transform 01d03:21:23 into 01 days 03:21:23
#     duration_text_pg_format = duration_text.replace("d", " days ")
#     duration = dt_util.parse_duration(duration_text_pg_format)
#     return duration.seconds if duration else None


class CituraDataUpdateCoordinator(DataUpdateCoordinator[list[DataConnection]]):
    """A Citura Data Update Coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, citura: CituraAPI.CituraAPI) -> None:
        """Initialize the Citura data coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_TIME),
        )
        self._citura = citura

    async def _async_update_data(self) -> list[DataConnection]:
        return await self.fetch_connections(limit=CONNECTIONS_COUNT)

    async def fetch_connections(self, limit: int) -> list[DataConnection]:
        """Fetch connections using the opendata api."""
        self._citura.limit = limit
        try:
            await self._citura.async_get_data()

        except Exception as e:
            _LOGGER.warning(
                "Connection to catp-reims.airweb.fr cannot be established")
            raise UpdateFailed from e

        connections = self._citura.data
        return [
            DataConnection(
                departure=dt_util.parse_datetime(
                    connections[i]["expectedDepartureTime"]
                ),
                realtime=connections[i]["realtime"],
                destination=connections[i]["destinationName"],
            )
            for i in range(limit)
            if len(connections) > i and connections[i] is not None
        ]
        # return [
        #     DataConnection(
        #         # departure=self.nth_departure_time(i),
        #         # train_number=connections[i]["number"],
        #         # platform=connections[i]["platform"],
        #         # transfers=connections[i]["transfers"],
        #         # duration=calculate_duration_in_seconds(connections[i]["duration"]),
        #         # start=self._citura.from_name,
        #         # destination=self._citura.to_name,
        #         # remaining_time=str(self.remaining_time(connections[i]["departure"])),
        #         # delay=connections[i]["delay"],
        #     )
        #     for i in range(limit)
        #     if len(connections) > i and connections[i] is not None
        # ]
