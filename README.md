# Monitor your Sunways Solar production in Home Assistant

The [sunways-portal.com](https://sunways-portal.com) allows you to monitor your Solar Panels and Inverter(s) energy production. This integration allows you you to monitor a subset of the availabe data in Home Assistant.

This integration is currently under development.

## Glossary

- Station: a PV system installation at an address
- Inverter: converting DC input from the PV strings to AC (110/230) - `device` in the Sunways API

## Features

The current implementation periodically fetching the single station overview, providing the following data:

Static:
- Installed

Total increasing:
- Daily Solar energy production
- Montly...
- Yearly...
- Total...

Live:
- Current Solar energy production
- Efficiency
- Grid consumption
- Grid return


## Future plans

- I wonder if a component could provide an integral sensor (for the grid consumption and return)
- The "single station overview" polling could be replaced by websocket


# Warning
This integration is currently under development, preparing for HACS.

Tested with one Sunways STH-6KTL and one Smart Meter providing info to the Sunways API

- Home Assistant 
    - 2024.10.2

# Disclaimer
THIS PROJECT IS NOT IN ANY WAY ASSOCIATED WITH OR RELATED TO SUNWAYS. The information here and online is for educational and resource purposes only and therefore the developers do not endorse or condone any inappropriate use of it, and take no legal responsibility for the functionality or security of your devices.
