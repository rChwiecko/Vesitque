from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Your Sauce Labs credentials
USERNAME = "oauth-hungqdang0510-e5eae"
ACCESS_KEY = "7f1ec0b5-ca25-403e-88ed-e9541c6bc911"

# Sauce Labs hub URL
URL = "ondemand.saucelabs.com:443/wd/hub"
command_executor = f"https://{USERNAME}:{ACCESS_KEY}@{URL}"

# Set up the options for Sauce Labs
options = Options()
options.browser_version = "latest"
options.platform_name = "Windows 10"
sauce_options = {
    "build": "Sauce Labs Example",
    "name": "My First Test"
}
options.set_capability("sauce:options", sauce_options)

# Connect to Sauce Labs
driver = webdriver.Remote(
    command_executor=command_executor,
    options=options
)

# Run your test
try:
    # Navigate to a website
    driver.get("https://ripple.hackutd.co")
    
    # Wait for the page title to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "title"))
    )
    
    # Debug: Print the page title
    print("Page Title:", driver.title)
    
    # Verify the page title contains "HackUTD"
    assert "HackUTD" in driver.title, "Title does not contain 'HackUTD'"
    print("Test Passed!")
except Exception as e:
    print("Test Failed:", e)
finally:
    # Close the browser
    driver.quit()
