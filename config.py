# IDX Automation Test - Configuration File

# URL to scrape
URL = "https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi"

# Folder to save downloaded files
DOWNLOAD_FOLDER = "Keterbukaan Informasi IDX"

# Options to select (0-5)
# You can modify this list to select different options
# Example: [0] - select only first option
#          [0, 1, 2] - select first three options
#          [0, 1, 2, 3, 4, 5] - select all options
SELECTED_OPTIONS = [0, 1, 2]

# Selenium settings
IMPLICITLY_WAIT = 10
PAGE_LOAD_TIMEOUT = 30
DOWNLOAD_WAIT = 2  # Time to wait after download starts

# XPath selectors
COMBOBOX_XPATH = "//div[contains(@id,'vs6__combobox')]"
OPTION_XPATH_TEMPLATE = "//div[contains(@id,'vs6__option-{}')]"
TIME_XPATH = "//time[@class='text-small']"
DOWNLOAD_BUTTON_XPATH = "//span[contains(@class, 'bzi-attachment')]"
