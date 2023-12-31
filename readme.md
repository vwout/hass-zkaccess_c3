# C3/inBio Access Control Panel integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)

This integration adds support for ZKTEco ZKAccess C3 and inBio Door Access Control panels to Home Assistant as custom component via HACS.
It relies on my [native Python library](https://github.com/vwout/zkaccess-c3-py/) for communicating with the panels.

This integration creates a devices for each panel and adds the following entities:
- a Lock representing each doorlock
- a Switch representing each (resetable) alarm, one per door
- a Binary sensor representing each auxiliary input
- a Switch representing each auxiliary output

The integration support the ZKAccess C3-100, C3-200, C3-400 and inBio 160/260/460 panels.

## Installation

### HACS installation

This integration is planned to become part of the default HACS store.
For now, add it as [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) or perform a manual installation.

### Manual installation

To add the C3 Access Control Panel integration to your installation, create a folder in your Home Assistant  `/config/` directory named `custom_components`.
In this folder, copy the folder [custom_components/zkaccess_c3](custom_components/zkaccess_c3) with all its contents.

Restart Home Assistant.

### Configuration
To add the C3 Access Control Panel integration to your installation, do the following:
- Go to *Configuration* and *Integrations*
- Click the `+ ADD INTEGRATION` button in the lower right corner.
- Search for 'C3 Access Control Panel' and click the integration.

After the integration and its dependencies are installed, a configuration dialog is opened.
In this dialog, provide a logical name for the panel, the IP-address and optionally the port (when non-standard).
Click *Submit* and the integration will connect and create all entities.

The integration works by polling the panel.
In the device configuration options, the poll interval can be changed.
The configuration options also allow modification of the activation duration used when unlocking a door, or activating an auxiliary output.

## Usage
The states of the devices (lock, auxiliaries) are automatically updated.
The status however is not in all cases directly available from the panel.
In case a sensor is connected and configured for each door, the lock represents the actual status of the door.
When no sensor is configured, the open (unlocked) and closed (locked) state is derived based on commands send and events received.
For configuration of the panel (door sensor, alarm, card and access control configuration), use the ZKAccess C3 software.

## Troubleshooting

The protocol for communication with the ZKAccess panels is not documented.
All functionality relies on reverse engineering and the experience is that there is quite some variation on how the different products behave.

In case of issues, perform these steps:
- Add the following to configuration.yaml:
  ```
  logger:
    logs:
      C3: debug
  ```
- Restart Homeassistant
- Go to Settings > Devices & Services and enable 'debug logging' for the ZKAccess C3 device.
- Interact with the C3 device (which may generate errors) and disable 'debug logging' afterward.
- Create an issue for this repository, including:
  - The device type (e.g. C3-400)
  - The firmware version
  - The log that is gathered from HomeAssistant