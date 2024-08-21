"""Constants for the Citura integration."""

from typing import Final

DOMAIN = "citura"
CONF_START: Final = "from"
CONF_LINE: Final = "line"
CONF_DIRECTION: Final = "direction"

DEFAULT_UPDATE_TIME = 90

CONNECTIONS_COUNT = 3
CONNECTIONS_MAX = 15

ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"
ATTR_LIMIT: Final = "limit"

SERVICE_FETCH_CONNECTIONS = "fetch_connections"
