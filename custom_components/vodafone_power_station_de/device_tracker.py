"""Support for Vodafone Power Station."""
import datetime
import hashlib
import hmac
import html
import logging
import re
import urllib.parse
import json

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from aiohttp.hdrs import CONTENT_TYPE
from homeassistant.components.device_tracker import (
    DOMAIN,
    PLATFORM_SCHEMA,
    DeviceScanner,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


def get_scanner(hass, config):
    """Return the Vodafone Power Station device scanner."""
    scanner = VodafonePowerStationDeviceScanner(config[DOMAIN])

    return scanner if scanner.success_init else None


class VodafonePowerStationDeviceScanner(DeviceScanner):
    """This class queries a router running Vodafone Power Station firmware."""

    def __init__(self, config):
        """Initialize the scanner."""
        self.host = config[CONF_HOST]
        self.username = config[CONF_USERNAME]
        self.password = config[CONF_PASSWORD]
        self.password = urllib.parse.quote(self.password)
        self.password = html.unescape(self.password)
        self.last_results = {}

        # Test the router is accessible.
        data = self.get_router_data()
        self.success_init = data is not None

    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()
        return [client["mac"] for client in self.last_results]

    def get_device_name(self, device):
        """Return the name of the given device or None if we don't know."""
        if not self.last_results:
            return None
        for client in self.last_results:
            if client["mac"] == device:
                return client["name"]
        return None

    def _update_info(self):
        """Ensure the information from the Vodafone Power Station is up to date.

        Return boolean if scanning successful.
        """
        if not self.success_init:
            return False

        _LOGGER.debug("Loading data from Vodafone Power Station")
        data = self.get_router_data()
        if not data:
            return False

        active_clients = [
            client for client in data.values() if client["status"] == "on"
        ]
        self.last_results = active_clients
        return True

    def get_router_data(self):
        """Retrieve data from Vodafone Power Station and return parsed result."""
        import helper

        devices = {}
        try:
            data = helper.get_router_data(self.host, self.username, self.password)
            jdata = json.loads(data)
            dvs = jdata["data"]["hostTbl"]

            for device_fields in dvs:
                devices[device_fields["alias"]] = {
                    "ip": device_fields["ipaddress"],
                    "mac": device_fields["physaddress"],
                    "status": "on" if device_fields["active"] else "off",
                    "name": device_fields["alias"]}
        except:
            pass

        return devices
