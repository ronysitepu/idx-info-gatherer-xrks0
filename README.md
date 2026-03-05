# IDX Automation Test - README

## Overview
This automation test suite visits the IDX Keterbukaan Informasi (Information Disclosure) page and downloads documents based on their publication date.

## Features
- Visits the IDX website page
- Automatically downloads new documents
- Tracks downloaded files to avoid duplicates
- Saves all files to a dedicated folder

## System Requirements

- **Python**: 3.8 or higher
- **Chrome/Chromium**: Latest version installed on your system
- **Operating System**: Windows 10/11

## Installation

### 1. Install Python 3.8+

- Download from https://www.python.org/downloads/
- During installation, **check "Add Python to PATH"**
- Verify installation:
```bash
python --version
```

### 2. Install Google Chrome

- Download from https://www.google.com/chrome/
- Run the installer and follow the prompts

### 3. Clone/Setup Project

Navigate to your project folder:
```bash
cd path\to\idx-info
```

### 4. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 5. Install Required Packages

```bash
pip install -r requirements.txt
```

The required packages are:
- **selenium** (4.15.2): Browser automation framework
- **webdriver-manager** (4.0.1): Automatic ChromeDriver management

## Usage

### Basic Usage

```bash
python automation_test.py
```

### Custom Configuration
Edit `config.py` to customize:
- **SELECTED_OPTIONS**: Choose which options to select (0-5)
  - Example: `[0]` - select only first option
  - Example: `[0, 1, 2]` - select first three options
  - Example: `[0, 1, 2, 3, 4, 5]` - select all options

- **DOWNLOAD_FOLDER**: Change the folder name for downloads

### Programmatic Usage
```python
from automation_test import IDXAutomationTest

# Create instance with custom settings
automation = IDXAutomationTest(
    download_folder="Keterbukaan Informasi IDX",
    selected_options=[0, 1, 2, 3]  # Select specific options
)

# Run the automation
automation.run()
```

## Output
The script will:
1. Create the download folder if it doesn't exist
2. Open Chrome browser and navigate to the page
3. Display publication dates of all documents
4. Download only NEW files (tracks previously downloaded files)
5. Display a summary of downloaded files

## Tracking System

The script uses a `.download_state.json` file to track downloaded documents:
- **First run**: Downloads all documents from the first 5 pages
- **Subsequent runs**: Only downloads NEW documents that haven't been seen before
- **Automatic stopping**: Stops early if no new files found on first page

## XPath Selectors Used
- Time elements: `//time[@class='text-small']`
- Download buttons: `//span[contains(@class, 'bzi-attachment')]/following-sibling::small`
- Page input field: `//input[@type='number'][@min][@max]`

## Troubleshooting

### Chrome Driver Issues

**Error: "chromedriver not found"**

The `webdriver-manager` should handle this automatically, but if issues persist:

- Download from https://chromedriver.chromium.org/
- Place in the project directory or add the folder to your PATH

### Downloads Not Saving
- Ensure the script has write permissions in the current directory
- Check that the DOWNLOAD_FOLDER path is valid
- On Windows: Use forward slashes or double backslashes in paths

### Elements Not Found
- The website structure may have changed
- Update the XPath selectors in `config.py` if needed
- Use browser developer tools (F12) to inspect elements

### Permission Issues

- Right-click script → Properties → Uncheck "Read-only"

### Virtual Environment Issues

If `python` command doesn't work, try:
```bash
py automation_test.py
```

Or ensure Python is added to PATH and restart your terminal.

## Notes
- The script tracks downloaded files in `.download_state.json`
- Chrome will remain open during execution (useful for monitoring)
- The script automatically handles page navigation via input field
- All files are saved to "Keterbukaan Informasi IDX" folder by default
- PDF downloads are automatically saved instead of opened in the browser
