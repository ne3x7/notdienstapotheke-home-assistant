# Notdienstapotheke (emergency pharmacy) integration for Home Assistant

Custom integration that displays closest emergency pharmacies to a defined PLZ, address or GPS location.

## Installation

### Install via HACS (recommended)

HACS installation is recommended as it allows you to be notified of any updates or new releases of the component.

1. In Home Assistant, go to **Settings → Devices & Services → HACS → Integrations**.
2. Click **+ Explore & Download Repositories**.
3. Click the three dots in the top-right and choose **Custom Repositories**.
4. Add the [URL of this repository](./dist) and set the category to **Integration**.
5. Go to **Settings → Devices & Services**.
6. Search for **Notdienstapotheke** and add it.
7. You will be asked to provide the name for the sensor and PLZ/Ort. These values are required. PLZ/Ort value is
   validated against the Aponet website.
8. You can additionally provide date, street, GPS coordinates and/or search radius. These values are not required.

### Install manually

1. Copy the [notdienstapotheke](./custom_components) directory to the `custom_components` folder of your Home Assistant
   installation (located at the same level as `configuration.yaml` file). If `custom_components` folder does not exist,
   create it.
2. Add a new sensor in `configuration.yaml` or `sensors.yaml` (see [below](#configuration)).
3. Restart Home Assistant from **Developer Tools**.

## Configuration

This integration can be configured from Home Assistant UI. If you want to configure the Notdienstapotheke
using `configuration.yaml` instead, you can use the YAML snippet below:

```yaml
platform: notdienstapotheke
...
```