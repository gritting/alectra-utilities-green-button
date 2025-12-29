# Home Assistant Integration
This guide explains how to run the Alectra Utilities Green Button exporter Python Script automatically using the AppDaemon add-on in Home Assistant OS.

## Prerequisites
* An [Alectra Utilities](https://www.alectrautilities.com/) account
* [Home Assistant OS](https://github.com/home-assistant/operating-system) Installed
* The [AppDaemon add-on](https://github.com/hassio-addons/addon-appdaemon) Installed  
  [![Open your Home Assistant instance and show the dashboard of an add-on.](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=a0d7b954_appdaemon)
* The [Home Assistant Green Button HACS Integration](https://github.com/rhounsell/home-assistant-green-button) Installed (I had success with v1.0.2)  
  [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=home-assistant-green-button&category=Integration&owner=rhounsell)

## Setup
### **1.** Summary of the general flow is:

1. Home Assistant automation fires event to `alectra_utilities_green_button` event topic (a time-based trigger and/or button, whatever triggers you want!)
2. AppDaemon `apps.yaml` and `call_script.py` are configured to run the `alectra_utilities_green_button.py` script when an event on this topic is received.
3. Selenium script runs in AppDaemon environment, downloads the data, then outputs the files to a directory under `/share`.
4. Folder Watcher Integration watches the output directory and triggers the automation to run the Import ESPI XML action provided by the **Green Button HACS Integration** on each file, which ingests the data into the energy dashboard.

### **2.** Configure the AppDaemon add-on
In the AppDaemon add-on configuration tab, add the required system and Python packages.

```yaml
system_packages:
  - firefox
  - geckodriver
python_packages:
  - python-dotenv
  - selenium
init_commands:  []
```

Restart the AppDaemon add-on after saving. 

### **3.** Clone this repo to AppDaemon apps directory and setup structure
```bash
# change into your appdaemon apps directory
cd /addon_configs/*_appdaemon/apps/

#clone this repo into your AppDaemon apps directory
git clone https://github.com/gritting/alectra-utilities-green-button.git

# move apps.yaml, call_script.py and alectra_utilities_green_button.py
mv alectra-utilities-green-button/*.{py,yaml} .

#copy env.example to env file
cp alectra-utilities-green-button/.env.example .env

# discard the rest
rm -rf ./alectra-utilities-green-button/
```

### **4.** Configure environment variables

In the previous step, you copied the `.env.example` to `.env`. Now you can fill in your Alectra Utilities credentials, output directory, and optionally any [selenium env var options.](https://www.selenium.dev/documentation/selenium_manager/#:~:text=Env%20variable) you want.

```dotenv
SE_AVOID_STATS=true                    # disable selenium telemetry
ALECTRA_ACCOUNT_NAME=JOHN E DOE        # name from your bill
ALECTRA_ACCOUNT_ID=0000000000          # 10 digit ID from your bill
ALECTRA_PHONE_NUMBER=4165551234        # phone number from your bill, no spaces or dashes
OUTPUT_PATH=/share/alectra_energy_data # the output directory 
```

> **Note:** The `/share` directory is accessible by both AppDaemon and Home Assistant Core. It is recommended to configure a folder under this directory as your `OUTPUT_PATH`. Make sure the path exists. Create it if it doesn't.


### **5.** Create an input_button helper (Optional)
For manual triggering, create a button helper in Home Assistant under **Settings → Devices & Services → Helpers → Create Helper → Button**.

[![Open your Home Assistant instance and show your helper entities.](https://my.home-assistant.io/badges/helpers.svg)](https://my.home-assistant.io/redirect/helpers/)
```yaml
- name: "Download Green Button Data"
- icon: mdi:home-lightning-bolt-outline`
```

### **6.** Configure Folder Watcher Integration
Add the [Folder Watcher](https://www.home-assistant.io/integrations/folder_watcher/) integration via the UI config flow button to monitor for new downloads in your configured `OUTPUT_PATH`. This will trigger the import process once the file is created.

> **Note:** Make sure to follow the directions for the Folder Watcher integration and add the `OUTPUT_PATH` to your `allowlist_external_dirs` in your `configuration.yaml` first!

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=folder_watcher)
```yaml
folder_watcher:
  - folder: /share/alectra_energy_data
    patterns:
      - "*.xml"
```

### **7.** Create Download/Import Automation
Add an automation to handle firing the events to trigger the the appdaemon script to start the download as well as import the Green Button data when the files are detected:

[![Open your Home Assistant instance and show your automations.](https://my.home-assistant.io/badges/automations.svg)](https://my.home-assistant.io/redirect/automations/)

```yaml
alias: Download/Import Alectra Utilities Green Button Data
description: >-
  Trigger AppDaemon to use the Selenium script to download the latest Green
  Button Data. Then, use Green Button Integration to import into Energy
  dashboard when new XML files are created in the specified folder.
triggers:
  - trigger: time_pattern
    hours: "4"
    id: scheduled_download
  - trigger: state
    entity_id:
      - input_button.download_green_button_data
    from: null
    to: null
    id: instant_download
  - trigger: state
    entity_id:
      - event.folder_watcher_share_alectra_energy_data
    attribute: event_type
    to:
      - created
    id: file_created
conditions: []
actions:
  - alias: Set up variables for the actions
    variables:
      action_dismiss: "{{ 'DISMISS' ~ context.id }}"
  - choose:
      - conditions:
          - condition: trigger
            id:
              - scheduled_download
              - instant_download
        sequence:
          - if:
              - condition: trigger
                id:
                  - scheduled_download
            then:
              - delay:
                  minutes: "{{ range(2,240)|random }}"
                alias: Delay for a random amount of minutes between 2 and 240
            alias: If triggered by scheduled_download, add randomness to the time
          - event: alectra_utilities_green_button
            event_data: {}
      - conditions:
          - condition: trigger
            id:
              - file_created
        sequence:
          - delay:
              hours: 0
              minutes: 0
              seconds: 5
              milliseconds: 0
          - action: green_button.import_espi_xml
            metadata: {}
            data:
              xml_file_path: "{{ trigger.to_state.attributes.path }}"
            enabled: true
          - action: notify.mobile_app_your_phone
            data:
              data:
                tag: import-done
                notification_icon: mdi:home-lightning-bolt-outline
                clickAction: /energy/electricity
                actions:
                  - action: URI
                    title: View
                    uri: /energy/electricity
                  - action: "{{ action_dismiss }}"
                    title: Dismiss
              title: Energy dashboard updated
              message: >-
                {%- set raw = trigger.to_state.attributes.file |
                regex_replace('^Alectra_Electric_', '') |
                regex_replace('(\\(\\d+\\))?\\.xml$', '') -%} {%- set parts =
                raw.split('-') -%} {%- set start = strptime(parts[0] ~ '-' ~
                parts[1] ~ '-' ~ parts[2], '%Y-%m-%d') -%} {%- set end   =
                strptime(parts[3] ~ '-' ~ parts[4] ~ '-' ~ parts[5], '%Y-%m-%d')
                -%} {%- macro ord(d) -%}
                  {%- set s = d | int -%}
                  {%- if s % 100 in [11,12,13] -%}{{ s }}th
                  {%- elif s % 10 == 1 -%}{{ s }}st
                  {%- elif s % 10 == 2 -%}{{ s }}nd
                  {%- elif s % 10 == 3 -%}{{ s }}rd
                  {%- else -%}{{ s }}th
                  {%- endif -%}
                {%- endmacro -%} {%- set sm = start. strftime('%b') -%} {%- set
                em = end.strftime('%b') -%} {%- set sd = ord(start.day) -%} {%-
                set ed = ord(end.day) -%} {%- if sm == em -%}
                  New data imported: {{ sm }} {{ sd }} to {{ ed }}
                {%- else -%}
                  New data imported: {{ sm }} {{ sd }} to {{ em }} {{ ed }}
                {%- endif -%}
          - wait_for_trigger:
              - event_type: mobile_app_notification_action
                event_data:
                  action: "{{ action_dismiss }}"
                trigger: event
                context: {}
            continue_on_timeout: false
          - alias: clear_notification on import-done
            action: notify.mobile_app_your_phone
            metadata: {}
            data:
              message: clear_notification
              data:
                tag: import-done
mode: parallel
max: 10

```

## Troubleshooting
### Script not running: 
  > **Tip:** Check the **AppDaemon** logs for errors under **Settings → Add-ons → AppDaemon → Logs**. Script-specific logs are written to `alectra.log` in the AppDaemon `apps` directory.  

### Firefox binary not found:
> **Tip:** Ensure the `firefox` and `geckodriver` packages are listed in the AppDaemon add-on configuration and the add-on has been restarted. You can check the AppDaemon logs as described above to ensure the requirements are being installed properly.

### Download directory not accessible:
> **Tip:** Use `/share/` as the base directory since it's accessible by both AppDaemon and Home Assistant Core. Other directories may be sandboxed and won't be accessible by one of the two.

### Verifying the event fires:
> **Tip:** Go to **Developer Tools → Events**, subscribe to `alectra_utilities_green_button`, then trigger your automation to confirm the event is being fired. 

### Out of memory errors:
> **Tip:** Headless Firefox with Selenium can consume 500MB+ of RAM. If you see crashes or oom/killed messages in the logs, try increasing the memory allocation for the host and ensuring the add-on has enough memory available to run.

### Selenium Manager errors (code: -9):
> **Tip:** This usually indicates Selenium is being killed due to resource constraints. See "Out of memory errors" above. 

### Login failure/timeouts:
> **Tip:**  Check if you can log in manually at the [Savage Data Portal](https://alectrautilitiesgbportal.savagedata.com). If you aren't able to log in with your credentials manually, you may need to find the correct values from your bill in order to log in.