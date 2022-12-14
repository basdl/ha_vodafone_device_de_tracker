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


import sjcl
from Crypto.Hash import SHA256


def doPbkdf2NotCoded(passwd, saltLocal):
    derivedKey = sjcl.sjcl.PBKDF2(passwd, saltLocal, hmac_hash_module=SHA256)
    hexdevkey = derivedKey.hex()
    return hexdevkey


def get_router_data(host, username, password):
    import requests

    s = requests.Session()

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'de',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'PHPSESSID=e8cf047f0844ea48dd255a6b58c8a146',
        'DNT': '1',
        'Origin': 'http://' + host + '',
        'Referer': 'http://' + host + '/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'X-CSRF-TOKEN': '',
        'X-Requested-With': 'XMLHttpRequest',
    }

    data = {
        'username': username,
        'password': 'seeksalthash',
        'logout': "true"
    }

    response = s.post('http://' + host + '/api/v1/session/login',
                      data=data, headers=headers, verify=False)
    salt = response.json()["salt"]
    saltwebui = response.json()["saltwebui"]

    h1 = doPbkdf2NotCoded(password, salt)
    pwd = doPbkdf2NotCoded(h1, saltwebui)

    data = {
        'username': username,
        'password': pwd
    }
    response = s.post('http://' + host + '/api/v1/session/login',
                      data=data, headers=headers, verify=False)
    #response.cookies["cwd"] = "No"
    s.cookies = response.cookies
    s.cookies["cwd"] = "No"

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'de',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Referer': 'http://' + host + '/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        "Accept-Language": "de,en-GB;q=0.9,en;q=0.8,de-DE;q=0.7,en-US;q=0.6",
    }

    response = s.get(
        'http://' + host + '/api/v1/session/menu?_=1667331451901', headers=headers, verify=False)
    response = s.get(
        'http://' + host + '/api/v1/sta_status?_=1667331451904', headers=headers, verify=False)
    response = s.get(
        'http://' + host + '/api/v1/CheckTimeOut?_=1667331451907', headers=headers, verify=False)
    response = s.get('http://' + host + '/api/v1/host/hostTbl,WPSEnable1,WPSEnable2,RadioEnable1,RadioEnable2,SSIDEnable1,SSIDEnable2,SSIDEnable3,operational,call_no,call_no2,LineStatus1,LineStatus2,DeviceMode,ScheduleEnable,dhcpLanTbl,dhcpV4LanTbl,lpspeed_1,lpspeed_2,lpspeed_3,lpspeed_4,AdditionalInfos1,AdditionalInfos2?_=1667331451911', headers=headers, verify=False)
    return response.text


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

        devices = {}
        try:
            data = get_router_data(
                self.host, self.username, self.password)
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
