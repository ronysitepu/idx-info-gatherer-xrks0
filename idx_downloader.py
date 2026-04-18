import os
import csv
import time
import requests
import subprocess
import re
import schedule
import json
import pandas as pd
from openpyxl import load_workbook, Workbook
from urllib.parse import unquote
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class IDXDownloader:
    def __init__(self, default_download_folder="IDX_Downloads"):
        self.url = "https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/"
        self.output_excel = "idx_metadata.xlsx"
        self.config_file = "config.json"
        self.driver = None
        
        # Load config
        self.config = self.load_config()
        
        # Determine download folder: prioritize config.json, then fallback to default
        self.download_folder = self.config.get("download_folder", default_download_folder)
        
        # Determine the date limit from config (default 7 days)
        initial_days = self.config.get("initial_days", 7)
        self.cutoff_date = datetime.now() - timedelta(days=initial_days)
        self.cutoff_date = self.cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        self.duplicate_limit = self.config.get("duplicate_limit", 5)
        self.polite_delay_seconds = self.config.get("polite_delay_seconds", 3)
        
        # Create download folder
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
            
        # Load previously downloaded URLs to avoid duplicates
        self.downloaded_urls = self.load_tracker()

    def load_config(self):
        """Load exclusion and priority keywords from config.json"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {"exclude_keywords": [], "high_priority_keywords": []}

    def load_tracker(self):
        """Load already downloaded URLs from the Excel tracker"""
        downloaded = set()
        if os.path.exists(self.output_excel):
            try:
                wb = load_workbook(self.output_excel, read_only=True)
                ws = wb.active
                # Assuming 'file link' is now the 5th column (E) due to Priority column
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if len(row) >= 5 and row[4]:
                        downloaded.add(row[4])
                wb.close()
            except Exception as e:
                print(f"Warning: Could not load tracker {self.output_excel}: {e}")
        return downloaded

    def append_to_tracker(self, data):
        """Append a single record to the Excel file"""
        file_exists = os.path.exists(self.output_excel)
        try:
            if file_exists:
                wb = load_workbook(self.output_excel)
                ws = wb.active
            else:
                wb = Workbook()
                ws = wb.active
                ws.append(["Date", "Ticker Code", "Priority", "file title", "file link"])
                
            ws.append([
                data["Date"], 
                data["Ticker Code"], 
                data["Priority"], 
                data["file title"], 
                data["file link"]
            ])
            wb.save(self.output_excel)
            wb.close()
        except Exception as e:
            print(f"Error saving to Excel tracker: {e}")
            
    def setup_driver(self):
        try:
            import undetected_chromedriver as uc
            print("Using undetected_chromedriver to bypass Cloudflare...")
            options = uc.ChromeOptions()
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-popup-blocking")
            
            # Set download directory for the browser and disable images for speed
            prefs = {
                "download.default_directory": os.path.abspath(self.download_folder),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "profile.managed_default_content_settings.images": 2, # Disable images
                "profile.default_content_setting_values.automatic_downloads": 1, # Allow multiple downloads
                "safebrowsing.enabled": False,
                "safebrowsing.disable_download_protection": True
            }
            options.add_experimental_option("prefs", prefs)
            
            try:
                # Try with version 145 since the user's Chrome is 145
                self.driver = uc.Chrome(options=options, version_main=145)
            except Exception as e:
                print(f"Failed with version 145: {e}. Trying default...")
                self.driver = uc.Chrome(options=options)
            
        except ImportError:
            print("undetected_chromedriver not found. Falling back to standard Selenium...")
            chrome_options = Options()
            
            # Cloudflare/Detection bypass settings
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Important stealth flags
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User Agent
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            
            # Set download directory for the browser
            prefs = {
                "download.default_directory": os.path.abspath(self.download_folder),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "profile.default_content_setting_values.automatic_downloads": 1, # Allow multiple downloads
                "safebrowsing.enabled": False,
                "safebrowsing.disable_download_protection": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute script to remove navigator.webdriver property
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })
        
    def download_file(self, url, filename):
        try:
            filepath = os.path.join(self.download_folder, filename)
            
            # Escape single quotes and backslashes for JS string
            js_url = url.replace('\\', '\\\\').replace("'", "\\'")
            js_filename = filename.replace('\\', '\\\\').replace("'", "\\'")
            
            # Execute JS to fetch the file and trigger download via blob
            # This bypasses Cloudflare because it runs entirely inside the browser's context
            js = f"""
            var callback = arguments[arguments.length - 1];
            fetch('{js_url}')
                .then(response => {{
                    if (!response.ok) throw new Error('status: ' + response.status);
                    return response.blob();
                }})
                .then(blob => {{
                    var windowUrl = window.URL || window.webkitURL;
                    var blobUrl = windowUrl.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = blobUrl;
                    a.download = '{js_filename}';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    windowUrl.revokeObjectURL(blobUrl);
                    callback('success');
                }})
                .catch(error => callback(error.toString()));
            """
            
            # Set a timeout for the async script to allow large file downloads
            self.driver.set_script_timeout(120)
            result = self.driver.execute_async_script(js)
            
            if result != 'success':
                print(f"Error downloading {url} via JS: {result}")
                return False
                
            # Wait for the file to be saved to disk
            max_wait = 60
            waited = 0
            while waited < max_wait:
                if os.path.exists(filepath):
                    # Give it a short moment to ensure the file handles are released by the OS
                    import time
                    time.sleep(0.5)
                    return True
                import time
                time.sleep(1)
                waited += 1
                
            print(f"Error: Timeout waiting for {filename} to be saved to {self.download_folder}")
            return False
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False

    def sync_to_rclone(self):
        """Push all downloaded files to GDrive using rclone copy"""
        target = self.config.get("rclone_target")
        if not target:
            return
            
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Batch syncing to GDrive ({target})...")
        try:
            # Use rclone copy to push the entire folder
            subprocess.run(["rclone", "copy", self.download_folder, target], check=True)
            print(f"    ✓ Batch sync complete.")
        except Exception as e:
            print(f"    ✗ Batch sync failed: {e}")

    def parse_date_string(self, date_str):
        """Safely parse Indonesian datetime string to Python datetime object"""
        date_str = date_str.strip()
        if "Hari ini" in date_str or "Today" in date_str:
            return datetime.now()
            
        id_months = {
            'Januari': '01', 'Februari': '02', 'Maret': '03', 'April': '04',
            'Mei': '05', 'Juni': '06', 'Juli': '07', 'Agustus': '08',
            'September': '09', 'Oktober': '10', 'November': '11', 'Desember': '12'
        }
        for name, num in id_months.items():
            if name in date_str:
                date_str = date_str.replace(name, num)
                break
                
        date_str = re.sub(r'\s+', ' ', date_str)
        for fmt in ["%d %m %Y %H:%M:%S", "%d %m %Y %H:%M", "%d %m %Y", "%Y-%m-%d"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def go_to_page(self, page_num):
        """Navigate to specific page using the input field"""
        try:
            page_input = self.driver.find_element(By.XPATH, "//input[@type='number'][@min][@max]")
            page_input.click()
            page_input.clear()
            page_input.send_keys(str(page_num))
            page_input.send_keys(Keys.RETURN)
            print(f"Waiting for page {page_num} to load...")
            time.sleep(4) # Polite delay for pagination to avoid rate limits
            return True
        except Exception as e:
            print(f"Could not navigate to page {page_num}: {e}")
            return False

    def run_job(self):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting IDX Downloader job...")
        
        # Refresh config
        self.config = self.load_config()
        initial_days = self.config.get("initial_days", 7)
        self.duplicate_limit = self.config.get("duplicate_limit", 5)
        self.polite_delay_seconds = self.config.get("polite_delay_seconds", 3)
        
        self.cutoff_date = datetime.now() - timedelta(days=initial_days)
        self.cutoff_date = self.cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_downloaded = 0
        consecutive_duplicates = 0
        try:
            self.setup_driver()
            print(f"Navigating to {self.url}...")
            self.driver.get(self.url)
            
            print("Waiting for initial page content to load...")
            time.sleep(5) 
            
            # --- Apply Saham Filter Robustly ---
            def ensure_saham_filter():
                try:
                    # Check if already selected
                    try:
                        selected_elem = self.driver.find_element(By.CSS_SELECTOR, "#vs1__combobox .vs__selected")
                        if "Saham" in selected_elem.text:
                            print("Filter 'Saham' is already active.")
                            return True
                    except:
                        pass

                    print("Applying 'Saham' filter...")
                    # Wait for combo box to be clickable
                    dropdown = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@id='vs1__combobox']"))
                    )
                    dropdown.click()
                    time.sleep(1)
                    
                    saham_option = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'vs__dropdown-option') and normalize-space()='Saham']"))
                    )
                    saham_option.click()
                    
                    # Wait for selection to appear and loading to complete
                    WebDriverWait(self.driver, 15).until(
                        EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#vs1__combobox .vs__selected"), "Saham")
                    )
                    print("Filter applied successfully.")
                    time.sleep(4) # Allow page to refresh
                    return True
                except Exception as e:
                    print(f"Warning: Attempt to apply 'Saham' filter failed: {e}")
                    return False

            if not ensure_saham_filter():
                print("CRITICAL: Failed to apply 'Saham' filter. The script may download unintended files.")
            
            page_num = 1
            stop_pagination = False
            
            while not stop_pagination:
                print(f"\n{'='*40}\nProcessing Page {page_num}\n{'='*40}")
                
                if page_num > 1:
                    if not self.go_to_page(page_num):
                        break
                    # Verify filter still active after navigation
                    try:
                        selected_elem = self.driver.find_element(By.CSS_SELECTOR, "#vs1__combobox .vs__selected")
                        if "Saham" not in selected_elem.text:
                            print(f"[!] Warning: Filter reset on page {page_num}! Re-applying...")
                            if not ensure_saham_filter():
                                print("[!] Re-application failed. Continuing with caution.")
                    except:
                        pass
                
                # Scroll to ensure elements render
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                records = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'disclosure-list__item')]")
                if not records:
                    records = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'disclosure-item')]")
                
                if not records:
                    print("DEBUG: Specific record classes not found. Attempting tag-based extraction...")
                    time_tags = self.driver.find_elements(By.TAG_NAME, "time")
                    records = [t.find_element(By.XPATH, "./ancestor::div[contains(@class, 'mb-') or contains(@class, 'py-') or @class!=''][1]") for t in time_tags if t.is_displayed()]
                    
                if not records:
                    print(f"DEBUG: No records found on page {page_num}. Page structure might have changed.")
                    
                    # Dump page source to a file so the user can inspect it and share it with us
                    debug_file = f"debug_empty_page_{page_num}.html"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print(f"DEBUG: Saved DOM source to {debug_file} for analysis.")
                    
                    break
                
                print(f"Found {len(records)} records on page {page_num}.")
                
                for idx, record in enumerate(records, 1):
                    try:
                        # 1. Date
                        date_elem = record.find_elements(By.TAG_NAME, "time")
                        date_text = date_elem[0].text.strip() if date_elem else "N/A"
                        doc_date = self.parse_date_string(date_text)
                        
                        # Stop if we've reached documents older than 7 days
                        if doc_date and doc_date < self.cutoff_date:
                            print(f"\n[!] Reached document from {doc_date.strftime('%Y-%m-%d')} (> 7 days ago). Stopping completely.")
                            stop_pagination = True
                            break
                        
                        # 2. Ticker & Title
                        title_elem = record.find_elements(By.TAG_NAME, "a")
                        if not title_elem:
                            continue
                        
                        main_link = title_elem[0]
                        full_text = main_link.text.strip()
                        
                        ticker_match = re.search(r'\[\s*([A-Z0-9]{4,6})\s*\]', full_text)
                        ticker = ticker_match.group(1) if ticker_match else "N/A"
                        title = full_text.replace(f"[{ticker}]", "").strip() if ticker != "N/A" else full_text
                        
                        # --- Filtering and Priority Logic ---
                        title_lower = title.lower()
                        
                        # Exclusion Check
                        should_skip = False
                        for kw in self.config["exclude_keywords"]:
                            if kw.lower() in title_lower:
                                print(f"  → Skipping excluded item: {title[:40]}...")
                                should_skip = True
                                break
                        if should_skip: continue
                        
                        # Priority Check
                        priority = "Normal"
                        for kw in self.config["high_priority_keywords"]:
                            if kw.lower() in title_lower:
                                priority = "High"
                                break
                        
                        # 3. Attachments
                        attachment_links = record.find_elements(By.XPATH, ".//a[contains(@href, '.pdf') or contains(@href, '.zip') or contains(@href, '.xls') or contains(@href, 'download')]")
                        
                        for link in attachment_links:
                            url = link.get_attribute("href")
                            if not url: continue
                            
                            # SKIP if already downloaded
                            if url in self.downloaded_urls:
                                print(f"  → Skipped (already downloaded): [{ticker}] {title[:30]}...")
                                consecutive_duplicates += 1
                                if consecutive_duplicates >= self.duplicate_limit:
                                    print(f"\n[!] Found {consecutive_duplicates} consecutive already-downloaded files. Catch-up complete? Stopping.")
                                    stop_pagination = True
                                    break
                                continue
                            
                            # If we reached here, it's a new file, reset duplicate counter
                            consecutive_duplicates = 0
                            
                            # FORMAT: YYYYMMDD_Ticker_[HIGH]_Title.ext
                            if doc_date:
                                clean_date_ymd = doc_date.strftime('%Y%m%d')
                            else:
                                raw_nums = str(re.sub(r'[^\d]', '', str(date_text)))
                                clean_date_ymd = raw_nums[:8]
                                
                            clean_ticker = ticker if ticker != "N/A" else "UNKNOWN"
                            # Add HIGH to filename if priority
                            priority_tag = "_HIGH" if priority == "High" else ""
                            
                            # Clean title for filename, take first 50 chars to avoid OS limits
                            clean_title_raw = re.sub(r'[\\/*?:"<>|]', '_', title)
                            clean_title = clean_title_raw[:50].strip()
                            
                            base_filename = unquote(url.split('/')[-1])
                            ext = ".pdf"
                            if "." in base_filename and "download" not in base_filename.lower():
                                ext = "." + base_filename.split('.')[-1]
                            elif ".zip" in url.lower(): ext = ".zip"
                            elif ".xls" in url.lower(): ext = ".xlsx"
                                
                            filename = f"{clean_date_ymd}_{clean_ticker}{priority_tag}_{clean_title}{ext}"
                            
                            print(f"  → Downloading new file ({priority}): {filename}")
                            
                            if self.download_file(url, filename):
                                print(f"    ✓ Success.")
                                data_row = {
                                    "Date": date_text,
                                    "Ticker Code": ticker,
                                    "Priority": priority,
                                    "file title": title,
                                    "file link": url
                                }
                                self.append_to_tracker(data_row)
                                self.downloaded_urls.add(url)
                                total_downloaded += 1
                                print(f"    Polite delay ({self.polite_delay_seconds}s)...")
                                time.sleep(self.polite_delay_seconds) # Configurable delay to avoid triggering firewall
                            else:
                                print(f"    ✗ Failed.")
                                time.sleep(1)
                                
                    except Exception as e:
                        print(f"Error processing record {idx}: {e}")
                        time.sleep(1)
                        continue
                
                if not stop_pagination:
                    page_num += 1

            print(f"\n✓ Session complete. Downloaded {total_downloaded} new files.")
            
            # Batch sync to GDrive
            if total_downloaded > 0:
                self.sync_to_rclone()

        except Exception as e:
            print(f"An error occurred during execution: {e}")
        finally:
            if self.driver:
                print("Closing browser...")
                self.driver.quit()

    def run_scheduler(self):
        self.config = self.load_config() # Reload for latest settings
        interval = self.config.get("interval_minutes", 60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduler started. Interval: {interval} minutes.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polite delay: {self.polite_delay_seconds} seconds.")
        print("Press Ctrl+C to exit.")
        
        # Run once immediately on startup
        self.run_job()
            
        # Schedule based on config
        schedule.every(interval).minutes.do(self.run_job)
        
        while True:
            # Calculate next run time for display
            next_run = datetime.now() + timedelta(minutes=interval)
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Job completed. Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            while True:
                schedule.run_pending()
                time.sleep(1)
                # Add a Heartbeat every 10 seconds to terminal for visibility
                if int(time.time()) % 10 == 0:
                    print(".", end="", flush=True)
                
                # Check if the job just ran and reset to calculate the next interval
                # This is a bit simplified; in a production script we'd check the schedule job object
                # but for this specific flow, recalculating after a run is what's requested.
                if not schedule.jobs or (schedule.next_run() and schedule.next_run() > next_run):
                    break

if __name__ == "__main__":
    downloader = IDXDownloader()
    # To run just once immediately, use downloader.run_job()
    # To run continuously on a schedule, use downloader.run_scheduler()
    downloader.run_scheduler()
