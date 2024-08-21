"""Citura API."""

import asyncio
import logging
from pprint import pprint
import urllib.parse

import aiohttp

_LOGGER = logging.getLogger(__name__)
_RESOURCE_URL = "http://catp-reims.airweb.fr/feed/"


class CituraAPI:
    """CituraAPI class."""

    def __init__(
        self,
        line: str | None = None,
        stop_point: str | None = None,
        direction=False,
        session=None,
    ) -> None:
        """Init cituraAPI."""
        self._session = session
        self.line = line
        self.stop_point = stop_point
        self.station = None
        self.station_id = None
        self.direction = "aller" if direction else "retour"
        self.data: list[dict] = []
        self.limit = 3

    def get_url(self, resource, params):
        """Get URL."""
        param = urllib.parse.urlencode(params, True)
        url = f"{_RESOURCE_URL}{resource}"
        if param:
            url += f"?{param}"
        return url

    async def async_get_all_stations(self):
        """Get all stations."""
        params = {}
        url = self.get_url("Station/getAllStations.json", params)
        try:
            response = await self._session.get(url, raise_for_status=True)
            _LOGGER.debug(
                "Response from catp-reims.airweb.fr: %s", response.status)
            data = await response.json()
            data = data["response"]["stations"]
            return [
                {"stop_id": station["stop_id"], "stop_name": station["name"]}
                for station in data
            ]
        except TimeoutError:
            _LOGGER.error("Can not load data")
        except aiohttp.ClientError as aiohttpClientError:
            _LOGGER.error("Response: %s", aiohttpClientError)

    async def async_get_all_line(self):
        """Get all lines."""
        params = {}
        url = self.get_url("Line/getAllLines.json", params)
        try:
            response = await self._session.get(url, raise_for_status=True)
            _LOGGER.debug(
                "Response from catp-reims.airweb.fr: %s", response.status)
            data = await response.json()
            data = data["response"]["lines"]
            return [
                {"line_id": line["line_id"], "line_name": line["name"]} for line in data
            ]
        except TimeoutError:
            _LOGGER.error("Can not load data")
        except aiohttp.ClientError as aiohttpClientError:
            _LOGGER.error("Response: %s", aiohttpClientError)

    async def async_get_line_by_station(self, station):
        """Get all lines passing by station."""
        params = {}
        params["station"] = station
        url = self.get_url("Line/getStationLines.json", params)
        try:
            response = await self._session.get(url, raise_for_status=True)
            _LOGGER.debug(
                "Response from catp-reims.airweb.fr: %s", response.status)
            data = await response.json()
            data = data["response"]["lines"]
            return [
                {"line_id": line["line_id"], "line_name": line["name"]} for line in data
            ]
        except TimeoutError:
            _LOGGER.error("Can not load data")
        except aiohttp.ClientError as aiohttpClientError:
            _LOGGER.error("Response: %s", aiohttpClientError)

    async def async_get_station(self):
        """Get station id from name."""
        params = {}
        params["line"] = self.line
        params["station"] = self.stop_point
        url = self.get_url("Station/getBoardingIDs.json", params)
        try:
            response = await self._session.get(url, raise_for_status=True)
            _LOGGER.debug(
                "Response from catp-reims.airweb.fr: %s", response.status)
            data = await response.json()
            data = data["response"]
            if len(data["boarding_ids"]["retour"]):
                self.station_id = data["boarding_ids"][self.direction][0]
                self.station = data["stop_id"]
        except TimeoutError:
            _LOGGER.error("Can not load data")
        except aiohttp.ClientError as aiohttpClientError:
            _LOGGER.error("Response: %s", aiohttpClientError)

    async def async_get_data(self):
        """."""
        if not self.station_id:
            await self.async_get_station()
        params = {}
        params["line"] = self.line
        params["stopPoint"] = self.station_id
        params["max"] = self.limit
        url = self.get_url("SIRI/getSIRIWithErrors.json", params)
        try:
            response = await self._session.get(url, raise_for_status=True)
            _LOGGER.debug(
                "Response from catp-reims.airweb.fr: %s", response.status)
            data = await response.json()
            if data["response"]["realtime_empty"] or data["response"]["realtime_error"]:
                _LOGGER.debug("Response empty")
                self.data = []
                return

            data = data["response"]["realtime"]
            data_formated = [
                {
                    "destinationName": elem["destinationName"],
                    "aimedDepartureTime": elem["aimedDepartureTime"],
                    "expectedDepartureTime": elem["expectedDepartureTime"],
                    "departureStatus": elem["departureStatus"],
                    "realtime": elem["realtime"],
                }
                for elem in data
            ]
            self.data = data_formated
        except TimeoutError:
            _LOGGER.error("Can not load data")
        except aiohttp.ClientError as aiohttpClientError:
            _LOGGER.error("Response: %s", aiohttpClientError)


async def main():
    """."""
    async with aiohttp.ClientSession() as session:
        # api = CituraAPI(
        #     line="03", stop_point="BRIAND", direction=False, session=session
        # )
        api = CituraAPI(session=session)
        line = await api.async_get_line_by_station("BRIAND")
        pprint(line)  # noqa: T203
        # await api.async_get_data()
        # pprint(api.data)  # noqa: T203


if __name__ == "__main__":
    asyncio.run(main())
