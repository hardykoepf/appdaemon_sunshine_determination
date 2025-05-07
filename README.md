# AppDaemon Sunshine Determination App

A dynamic brightness threshold calculator for Home Assistant that adjusts thresholds based on time of day and season.

## Description

This AppDaemon app calculates dynamic brightness thresholds throughout the day using a sine curve and adjusts the maximum threshold based on the distance to summer solstice. Perfect for use with automated blinds or lighting controls that need varying brightness thresholds.

## Features

* Dynamic threshold calculation using sine curve
* Seasonal adjustment based on summer solstice
* Smooth transitions between day/night
* Configurable minimum/maximum thresholds
* Sunrise/sunset buffer zones
* Real-time updates to Home Assistant sensor

## Requirements

* Home Assistant with AppDaemon 4.x
* Home Assistant template sensor
* Home Assistant 'sun.sun' integration

## Installation

1. Copy sunshine.py to your AppDaemon apps directory
2. Configure the app in your `apps.yaml`
3. Add the required template sensor to Home Assistant
4. Restart AppDaemon

## Configuration

### Home Assistant Configuration

Add this template sensor to your `configuration.yaml`:

````yaml
template:
  sensor:
    - name: "Sunshine Threshold"
      unique_id: sunshine_threshold
      unit_of_measurement: "lx"
      device_class: illuminance
      state_class: measurement
      icon: mdi:brightness-7
      state: >
        {{ states('sensor.sunshine_threshold') | float(default=0) }}
````

### AppDaemon Configuration

Add this configuration to your `apps.yaml`:

````yaml
sunshine:
  module: sunshine
  class: Sunshine
  priority: 10                         # Should be higher than dependent apps
  entity: sensor.sunshine_threshold    # Entity to update in Home Assistant
  floor: 40000                        # Minimum threshold (winter)
  cap: 70000                          # Maximum threshold (summer)
  buffer: 5000                        # Threshold at sunrise/sunset
  DEBUG: False                        # Enable debug logging
````

### Configuration Options

| Option   | Required | Description                           | Default |
|----------|----------|---------------------------------------|---------|
| entity   | Yes      | Entity ID for threshold storage       | -       |
| floor    | No       | Minimum threshold (winter)            | 10000   |
| cap      | No       | Maximum threshold (summer)            | 70000   |
| buffer   | No       | Sunrise/sunset threshold              | 10000   |
| DEBUG    | No       | Enable debug logging                  | False   |

The threshold parameters cap and floor meaning following:
floor: The floor is the brightness threshold (lx) between cloudy and sunny in winter when the sun is on it's lowest position (northern hemisphere on 21th Dec)
cap: The floor is the brightness threshold (lx) between cloudy and sunny in summer when the sun is on it's highest position (northern hemisphere on 21th June)
buffer: This is the minimum brightness which has to be reached as minimum. It is for dawn and dusk because threshold for dusk and dawn is hard to detect.

The app calculates a sinus curve between sunrise and sunset for every day where the highest point of curve is calculated by actual date and the floor and cap thresholds.
It's pretty more acurate than defining a static threshold. With this dynamic threshold based on actual date and time you can 'feed' my other AppDaemon app for Blinds automation.
The solar heating will be more acurate and Blinds are not opening when sun doesn't shine.

## Technical Details

### Threshold Calculation
* Uses sine curve for smooth day/night transitions
* Peak at solar noon
* Drops to buffer value outside daylight hours
* Adjusts maximum based on distance to summer solstice

### Update Triggers
* Sun attribute changes
* Initial startup
* Real-time updates to Home Assistant sensor

### Error Handling
* Validates configuration values
* Ensures floor < cap
* Ensures buffer >= 0
* Provides warning messages for invalid configurations

## Debugging

Enable debug logging by setting `DEBUG: true` to see:
* Calculated thresholds
* Timing information
* Error messages
* Configuration warnings

## Notes

* All thresholds are in lux (lx)
* Floor must be lower than cap
* Buffer should be greater than 0
* Set priority higher than apps using the threshold

## License

MIT License - See LICENSE file for details

## Support

For bug reports and feature requests, please open an issue on GitHub.
