import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

download_folder = os.path.abspath("test_downloads")
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

options = uc.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
prefs = {
    "download.default_directory": download_folder,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
}
options.add_experimental_option("prefs", prefs)

driver = uc.Chrome(options=options)
driver.get("https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/")
time.sleep(5)

url = "https://www.idx.co.id/StaticData/NewsAndAnnouncement/ANNOUNCEMENTSTOCK/From_EREP/202204/20260418163129-61276-0/FinancialStatement-2022-III-SKYB.pdf"
filename = "test_custom_name.pdf"

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

# wait for download
for _ in range(10):
    if os.path.exists(os.path.join(download_folder, filename)):
        print("File downloaded successfully!")
        break
    time.sleep(1)
else:
    print("Download timeout")

driver.quit()
