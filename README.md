# Home Assistant Device Tracker for Vodafone Commscope Router

This is a Home Assistant Device Tracker that works with the german version of Vodafone Power Station.
The device meant to work with this plugin is: `https://kabel.vodafone.de/static/media/Bedienungsanleitung_Vodafone_Station_Wi-Fi_6_Commscope.pdf`

It extracts the list of connected devices and expose them to Home Assistant.

## Installation

### Option 1

Use [HACS](https://hacs.xyz/) and add this repo: `https://github.com/basdl/ha_vodafone_device_de_tracker`.

### Option 2

Manually copy the content of this repo in your `custom_components/` folder.


## Configuration

Add this tracker to your `device_tracker` section:

```yaml
- platform: vodafone_power_station_de
  interval_seconds: 60
  host: XX.XX.XX.XX
  username: your_username_here
  password: 'your_password_here'
  new_device_defaults:
    track_new_devices: False
```

To enable logging:

```yaml
logger:
  default: info
  logs:
    custom_components.vodafone_power_station.device_tracker: info
```

The discovered devices will be listed in the `known_devices.yaml` file.

