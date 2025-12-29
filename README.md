# Alectra Utilities Green Button
Export [Green Button](https://green-button.github.io/) ([ESPI](https://www.naesb.org//ESPI_Standards.asp)) energy usage data from your [Alectra Utilities](https://www.alectrautilities.com/) account. 

Alectra Utilities offers a Green Button XML export through the [Savage Data Green Button Data Portal](https://alectrautilitiesgbportal.savagedata.com/), but does not offer programmatic API access to end users. This script logs into the portal with [Selenium](https://selenium.dev/) and downloads the energy usage report.

# Standalone Installation

The script can be run standalone without any integration or appdaemon configuration, but requires the following requirements to be accessible.

## Requirements
* An [Alectra Utilities](https://www.alectrautilities.com/) account
* Python 3.9+
* Firefox and geckodriver, or Google Chrome and ChromeDriver

## Configuration
Create a `.venv` and install dependencies with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your credentials: 

```bash
cp .env.example .env
```

```dotenv
SE_AVOID_STATS=true              # disable selenium telemetry
ALECTRA_ACCOUNT_NAME=JOHN E DOE  # name from your bill
ALECTRA_ACCOUNT_ID=0000000000    # 10 digit ID from your bill
ALECTRA_PHONE_NUMBER=4165551234  # phone number from your bill, no spaces or dashes
OUTPUT_PATH=/tmp/                # the output directory
```

## Usage
> **Note:** Only the required settings that are not populated from the `.env` file configured in the previous step will be prompted at run-time. 

```
Export Green Button (ESPI) energy usage data from your Alectra Utilities Hydro account.

usage: alectra_utilities_green_button.py [-h] [--version] [--account-name ACCOUNT_NAME]
                                         [--account-id ACCOUNT_ID] [--phone PHONE]
                                         [--output-path OUTPUT_PATH] [--browser {firefox,chrome}]
                                         [--driver DRIVER]
options:
  -h, --help                      show this help message and exit
  --version, -v                   show program's version number and exit
  --account-name, -n ACCOUNT_NAME Alectra Utilities Account Name. [ALECTRA_ACCOUNT_NAME]
  --account-id, -i ACCOUNT_ID     Alectra Utilities Account ID.[ALECTRA_ACCOUNT_ID]
  --phone, -p PHONE               Alectra Utilities Phone Number. [ALECTRA_PHONE_NUMBER]
  --output-path, -o OUTPUT_PATH   Output path used to store the output files [OUTPUT_PATH]
  --browser, -b {firefox,chrome}  Headless browser to use (default: firefox).
  --driver, -d DRIVER             Path to web driver (geckodriver or chromedriver).
```

## Examples

### with Python
```bash
source .venv/bin/activate
python alectra_utilities_green_button.py
```
### with Bash wrapper
```bash
./alectra_utilities_green_button.sh
```

## Home Assistant Integration

Want to automate energy data collection with Home Assistant? See [homeassistant.md](homeassistant.md) for detailed instructions on setting up: 
- AppDaemon add-on configuration
- Scheduled and manual triggers
- Folder watcher automation
- Green Button data import into the energy dashboard

## License
[MIT License](LICENSE)  
Many thanks to [Evan Cooper](https://github.com/EvanCooper9) and [Ben Webber](https://github.com/benwebber) for their original work on this!