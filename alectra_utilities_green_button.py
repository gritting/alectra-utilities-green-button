#!/usr/bin/env python
"""
Export Green Button (ESPI) energy usage data from your Alectra Utilities Hydro account.
"""
import argparse
import enum
import logging
import os
import shutil
import sys
import time
from typing import List, Optional

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.service import Service

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

__version__ = '0.2.7'

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s:  %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'alectra.log'))
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
class Browser(str, enum.Enum):
    FIREFOX = 'firefox'
    CHROME = 'chrome'


def get_web_driver(browser: Browser, driver_path: Optional[str] = None, output_path: Optional[str] = None) -> WebDriver:
    if browser == Browser.FIREFOX:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")

        firefox_paths = [
            "/usr/bin/firefox",
            "/usr/bin/firefox-esr",
            shutil.which("firefox"),
            shutil.which("firefox-esr"),
        ]

        for path in firefox_paths:
            if path and os.path.isfile(path):
                logger.debug(f"Setting Firefox binary location to:  {path}")
                options.binary_location = path
                break
        else:
            raise FileNotFoundError("Could not find Firefox binary")

        logger.info(f"Download directory set to: {output_path}")
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.download.dir", output_path)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/plain,application/xml,text/xml")

        geckodriver_path = driver_path or shutil.which("geckodriver")
        if geckodriver_path: 
            logger.debug(f"Using geckodriver at: {geckodriver_path}")
            service = Service(executable_path=geckodriver_path)
        else:
            logger.debug("Letting Selenium find geckodriver automatically")
            service = None

        try:
            logger.debug("Attempting to create Firefox WebDriver...")
            if service:
                driver = webdriver.Firefox(service=service, options=options)
            else:
                driver = webdriver.Firefox(options=options)
            logger.info("Firefox WebDriver created successfully!")
            return driver
        except Exception as e:
            logger.error(f"Failed to create Firefox WebDriver: {e}")
            raise

    else: 
        # Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-modal-animations")
        options.add_argument("--disable-login-animations")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_experimental_option("prefs", {
            "download.default_directory":  output_path,
            "download.prompt_for_download":  False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        chromedriver_path = driver_path or shutil.which("chromedriver")
        if chromedriver_path:
            logger.info(f"Using chromedriver at: {chromedriver_path}")
            service = webdriver.ChromeService(executable_path=chromedriver_path)
            return webdriver.Chrome(options=options, service=service)
        else:
            return webdriver.Chrome(options=options)


def login_and_download_green_button_xml(
    driver: WebDriver,
    account_name: str,
    account_id: str,
    phone: str,
    ) -> None:
    """Log into the Alectra Utilities Savage Data GBD Portal and download Green Button XML."""
    logger.info("Navigating to Alectra login page...")
    driver.get('https://alectrautilitiesgbportal.savagedata.com/Connect/Authorize?returnUrl=https%3A%2F%2Falectrautilitiesgbportal.savagedata.com%2FDownloadMyData')
    logger.debug(f"Page loaded.  Current URL: {driver.current_url}")

    wait = WebDriverWait(driver, 10)

    time.sleep(1)
    logger.debug("Looking for phone field...")
    phone_field = wait.until(EC.visibility_of_element_located((By.NAME, 'Phone')))
    phone_field.send_keys(phone)
    logger.debug("Phone field filled")

    logger.debug("Looking for account name field...")
    account_name_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#account-name')))
    account_name_field.send_keys(account_name)
    logger.debug("Account name field filled")

    logger.debug("Looking for account ID field...")
    account_id_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#idAccountNumber')))
    account_id_field.send_keys(account_id)
    logger.debug("Account ID field filled")

    logger.debug("Looking for login button...")
    login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn')))
    login_button.click()
    logger.debug("Login button clicked")

    logger.debug("Looking for checkbox...")
    checkbox = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="chkElectUsageData"]')))
    driver.execute_script("arguments[0].click();", checkbox)
    logger.debug("Checkbox clicked")

    logger.debug("Looking for download button...")
    download_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn')))
    driver.execute_script("arguments[0].click();", download_button)
    logger.debug("Download button clicked")

    logger.debug("Waiting for download to complete...")
    time.sleep(5)
    logger.debug("Download wait complete")


def get_default_browser() -> Browser:
    if shutil.which('chromedriver'):
        return Browser.CHROME
    else: 
        return Browser.FIREFOX


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--version', '-v', action='version', version='%(prog)s ' + __version__,
    )
    parser.add_argument(
        '--account-name', '-n',
        default=os.getenv('ALECTRA_ACCOUNT_NAME'),
        help='Alectra Utilities Account Name. [ALECTRA_ACCOUNT_NAME]',
    )
    parser.add_argument(
        '--account-id', '-i',
        default=os.getenv('ALECTRA_ACCOUNT_ID'),
        help='Alectra Utilities Account ID.[ALECTRA_ACCOUNT_ID]',
    )
    parser.add_argument(
        '--phone', '-p',
        default=os.getenv('ALECTRA_PHONE_NUMBER'),
        help='Alectra Utilities Phone Number. [ALECTRA_PHONE_NUMBER]',
    )
    parser.add_argument(
        '--output-path', '-o',
        default=os.getenv('OUTPUT_PATH'),
        help='Output path used to store the output files [OUTPUT_PATH]'
    ),
    parser.add_argument(
        '--browser', '-b',
        choices=[browser.value for browser in Browser],
        default=get_default_browser().value,
        help='Headless browser to use (default: %(default)s).',
        type=Browser,
    )
    parser.add_argument(
        '--driver', '-d',
        help='Path to web driver (geckodriver or chromedriver).',
        type=str,
        default=None,
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    account_name = args.account_name or input('Account Name:  ')
    account_id = args.account_id or input('Account ID: ')
    phone = args.phone or input('Phone Number: ')
    output_path = args.output_path or os.path.dirname(__file__)

    if not account_name or not account_id or not phone:
        logger.error("Missing required credentials. Check your .env file or provide arguments.")
        logger.error(f"account_name: {'set' if account_name else 'MISSING'}")
        logger.error(f"account_id:  {'set' if account_id else 'MISSING'}")
        logger.error(f"phone: {'set' if phone else 'MISSING'}")
        return

    logger.info("=" * 50)
    logger.info("Alectra Green Button Data Export - Starting")
    logger.info("=" * 50)
    logger.debug(f"Account Name: {account_name[:1]}***")
    logger.debug(f"Account ID:  {account_id[:1]}***")
    logger.debug(f"Phone:  {phone[:1]}***")
    logger.debug(f"Script directory: {os.path.dirname(__file__)}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    driver = None

    try:
        logger.debug('Starting Selenium web driver browser (%s, %s, %s)', args.browser, args.driver, output_path)
        driver = get_web_driver(browser=args.browser, driver_path=args.driver, output_path=output_path)
        driver.set_page_load_timeout(10)
        logger.debug("Page load timeout set to 10 seconds")

        login_and_download_green_button_xml(
            driver=driver,
            account_name=account_name,
            account_id=account_id,
            phone=phone,
        )
        logger.info("Script completed successfully!")

    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    finally:
        if driver: 
            logger.debug("Closing WebDriver...")
            driver.quit()
            logger.debug("WebDriver closed")


if __name__ == '__main__':
    main()