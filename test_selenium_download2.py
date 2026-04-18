import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

download_folder = os.path.abspath("test_downloads")
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
prefs = {
    "download.default_directory": download_folder,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
})

driver.get("https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/")
time.sleep(5)

url = "https://www.idx.co.id/StaticData/NewsAndAnnouncement/ANNOUNCEMENTSTOCK/From_EREP/202204/20260418163129-61276-0/FinancialStatement-2022-III-SKYB.pdf"
filename = "test_custom_name.pdf"

driver.set_script_timeout(60)

js = f"""
var callback = arguments[arguments.length - 1];
fetch('{url}')
    .then(response => {{
        if (!response.ok) throw new Error('status: ' + response.status);
        return response.blob();
    }})
    .then(blob => {{
        var url = window.URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = '{filename}';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        callback('success');
    }})
    .catch(error => callback(error.toString()));
"""

result = driver.execute_async_script(js)
print("JS result:", result)

for _ in range(10):
    if os.path.exists(os.path.join(download_folder, filename)):
        print("File downloaded successfully!")
        break
    time.sleep(1)
else:
    print("Download timeout")

driver.quit()
