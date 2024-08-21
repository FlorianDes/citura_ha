"""Helper functions for citura."""

from types import MappingProxyType
from typing import Any

from .const import CONF_DIRECTION, CONF_LINE, CONF_START


def unique_id_from_config(config: MappingProxyType[str, Any] | dict[str, Any]) -> str:
    """Build a unique id from a config entry."""
    return f"{config[CONF_START]} {config[CONF_LINE]} {"reverse" if config[CONF_DIRECTION] else ""}"
