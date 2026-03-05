import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class IDXAutomationTest:
    def __init__(self, download_folder="Keterbukaan Informasi IDX", selected_options=None):
        """
        Initialize the automation test
        
        Args:
            download_folder: Folder name to save downloaded files
            selected_options: List of option indices to select (e.g., [0, 1, 2])
        """
        self.url = "https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi"
        self.download_folder = download_folder
        self.selected_options = selected_options or [0]  # Default to first option
        self.driver = None
        self.last_clicked_option = None
        self.state_file = os.path.join(download_folder, ".download_state.json")
        
        # Create download folder
        os.makedirs(self.download_folder, exist_ok=True)
        
    def setup_driver(self):
        """Setup Chrome WebDriver with download preferences"""
        chrome_options = Options()
        
        # Configure download folder
        prefs = {
            "download.default_directory": os.path.abspath(self.download_folder),
            "download.prompt_for_download": False,
            "profile.default_content_settings.popups": 0,
            "plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}],
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.pdfs": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Disable extensions and plugins
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--headless") 
        
        # Optional: Uncomment for headless mode
        # chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        
    def get_today_date(self):
        """Get today's date in ISO format (YYYY-MM-DD)"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def load_state(self):
        """Load the state of last downloaded items"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return {"downloaded_items": []}
        return {"downloaded_items": []}
    
    def save_state(self, state):
        """Save the state of downloaded items"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
    
    def go_to_page(self, page_num):
        """Navigate to a specific page using the page input field"""
        try:
            page_input = self.driver.find_element(By.XPATH, "//input[@type='number'][@min][@max]")
            
            # Clear the input and set new value
            page_input.click()
            page_input.clear()
            page_input.send_keys(str(page_num))
            
            # Press Enter to go to the page
            page_input.send_keys(Keys.RETURN)
            
            print(f"  ✓ Navigating to page {page_num}...")
            time.sleep(3)  # Wait for page to load
            return True
        except Exception as e:
            print(f"  ✗ Error navigating to page {page_num}: {e}")
            return False
    
    def parse_date_string(self, date_str):
        """Parse date string and return as datetime object"""
        try:
            # Handle common date formats
            date_str = date_str.strip()
            # Try ISO format first
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                pass
            
            # Try other common formats
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
            # If no format matches, return None
            print(f"Warning: Could not parse date string: {date_str}")
            return None
        except Exception as e:
            print(f"Error parsing date: {e}")
            return None
    
    def is_date_today_or_newer(self, date_str):
        """Check if date is within the last 14 days"""
        try:
            parsed_date = self.parse_date_string(date_str)
            if parsed_date is None:
                return False
                
            # Allow dates from the last 14 days
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=14)
            cutoff = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
            parsed_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            return parsed_date >= cutoff
        except Exception as e:
            print(f"Error checking date: {e}")
            return False
    
    def click_combobox(self):
        """Click the combobox element to expand options"""
        try:
            wait = WebDriverWait(self.driver, 10)
            combobox = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@id,'vs6__combobox')]"))
            )
            combobox.click()
            print("✓ Combobox clicked successfully")
            time.sleep(1)  # Wait for options to appear
        except Exception as e:
            print(f"✗ Error clicking combobox: {e}")
            raise
    
    def select_options(self):
        """Select specified options from the combobox"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            for option_idx in self.selected_options:
                try:
                    option_xpath = f"//div[contains(@id,'vs6__option-{option_idx}')]"
                    option = wait.until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )
                    
                    # Get option text before clicking
                    option_text = option.text
                    option.click()
                    self.last_clicked_option = option_text
                    
                    print(f"✓ Selected option {option_idx}: {option_text}")
                    time.sleep(1)  # Wait between selections
                    
                except Exception as e:
                    print(f"✗ Error selecting option {option_idx}: {e}")
            
            print(f"\nLast clicked option: {self.last_clicked_option}")
        except Exception as e:
            print(f"✗ Error in select_options: {e}")
            raise
    
    def process_documents(self):
        """Process documents: download all files from first 5 pages"""
        try:
            wait = WebDriverWait(self.driver, 10)
            state = self.load_state()
            previously_downloaded = set(state.get("downloaded_items", []))
            
            print(f"✓ Previously downloaded: {len(previously_downloaded)} items")
            
            total_downloaded = 0
            max_pages = 5
            pages_with_no_new_items = 0
            
            for page_num in range(1, max_pages + 1):
                print(f"\n{'='*60}")
                print(f"Processing Page {page_num}/{max_pages}")
                print(f"{'='*60}")
                
                # Navigate to page
                if page_num == 1:
                    # First page - just scroll to load
                    print("→ Scrolling to load page content...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)  # Longer wait for first page
                else:
                    # Navigate to next page
                    if not self.go_to_page(page_num):
                        print("✓ Could not navigate to page, stopping")
                        break
                    
                    # Scroll to load content
                    print("→ Scrolling to load page content...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)  # Longer wait
                
                # Wait for time elements to be present (longer timeout)
                try:
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//time[@class='text-small']")))
                except:
                    print("✗ No time elements found on this page")
                    break
                
                # Get all document rows on this page
                time_elements = self.driver.find_elements(By.XPATH, "//time[@class='text-small']")
                
                print(f"✓ Found {len(time_elements)} documents on page {page_num}")
                
                if len(time_elements) == 0:
                    print("✗ No documents found, stopping")
                    break
                
                page_downloaded = 0
                
                for idx, time_elem in enumerate(time_elements, 1):
                    try:
                        # Get the date text
                        date_text = time_elem.text
                        print(f"Document {idx}: Date = {date_text}")
                        
                        # Create a unique identifier for this item
                        item_id = f"{idx}_{date_text}_{page_num}"
                        
                        # Skip if already downloaded
                        if item_id in previously_downloaded:
                            print(f"  → Already downloaded, skipping")
                            continue
                        
                        print(f"  → New item, attempting download...")
                        
                        # Try to find the download button
                        try:
                            row = time_elem.find_element(By.XPATH, "ancestor::div[@class or @role][1]")
                            
                            # Scroll the row into view first
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                            time.sleep(0.5)
                            
                            # Try different selectors
                            download_btn = None
                            selectors = [
                                ".//span[contains(@class, 'bzi-attachment')]/following-sibling::small",
                                ".//span[contains(@class, 'bzi-attachment')]",
                                ".//a[contains(@href, '.pdf') or contains(@href, '.xls') or contains(@href, '.doc')]",
                                ".//button[contains(@class, 'attachment') or contains(@aria-label, 'download')]",
                                ".//*[@class='bzi-attachment']/parent::a",
                                ".//*[@class='bzi-attachment']/parent::button"
                            ]
                            
                            for selector in selectors:
                                try:
                                    download_btn = row.find_element(By.XPATH, selector)
                                    print(f"  ✓ Found button with selector: {selector}")
                                    break
                                except:
                                    continue
                            
                            if not download_btn:
                                links = row.find_elements(By.XPATH, ".//a | .//button")
                                print(f"  Found {len(links)} links/buttons in row")
                                for link in links:
                                    try:
                                        link_html = link.get_attribute("outerHTML")
                                        print(f"    Checking: {link_html[:100]}...")
                                        if 'bzi' in link_html or 'attachment' in link_html or 'download' in link_html.lower():
                                            download_btn = link
                                            print(f"  ✓ Found matching button")
                                            break
                                    except:
                                        continue
                            
                            if not download_btn:
                                print(f"  ✗ Could not find download button")
                                continue
                            
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", download_btn)
                            time.sleep(0.5)
                            
                            print(f"  → Attempting to click button...")
                            try:
                                download_btn.click()
                                print(f"  ✓ Download button clicked")
                            except:
                                print(f"  → Click failed, trying JavaScript click...")
                                self.driver.execute_script("arguments[0].click();", download_btn)
                                print(f"  ✓ Download button clicked (JavaScript)")
                            
                            print(f"  ✓ Download initiated")
                            total_downloaded += 1
                            page_downloaded += 1
                            previously_downloaded.add(item_id)
                            time.sleep(2)
                            
                        except Exception as e:
                            print(f"  ✗ Error finding button: {e}")
                        
                    except Exception as e:
                        print(f"✗ Error processing document {idx}: {e}")
                
                print(f"\n✓ Downloaded {page_downloaded} files on page {page_num}")
                
                # Stop early if page has no new items (already downloaded everything)
                if page_downloaded == 0:
                    print("✓ No new files on this page, stopping pagination")
                    break
            
            # Update state
            state["downloaded_items"] = list(previously_downloaded)
            state["last_updated"] = datetime.now().isoformat()
            self.save_state(state)
            
            print(f"\n{'='*60}")
            print(f"✓ COMPLETED")
            print(f"  → Downloaded {total_downloaded} new files in this session")
            print(f"  → Total downloaded so far: {len(previously_downloaded)} items")
            print(f"{'='*60}")
            return total_downloaded
            
        except Exception as e:
            print(f"✗ Error in process_documents: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def run(self):
        """Run the complete automation test"""
        try:
            print("=" * 60)
            print("IDX Automation Test")
            print("=" * 60)
            
            # Setup
            print("\n[1/3] Setting up WebDriver...")
            self.setup_driver()
            print("✓ WebDriver ready")
            
            # Navigate
            print("\n[2/3] Navigating to URL...")
            self.driver.get(self.url)
            print(f"✓ Navigated to {self.url}")
            time.sleep(3)  # Wait for page to load
            
            # Process documents
            print("\n[3/3] Processing documents...")
            downloaded = self.process_documents()
            
            print("\n" + "=" * 60)
            print("✓ Automation test completed successfully!")
            print(f"  → Downloaded {downloaded} files")
            print(f"  → Files saved to: {os.path.abspath(self.download_folder)}")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ Automation test failed: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                print("\n✓ WebDriver closed")


if __name__ == "__main__":
    # Example usage
    # You can modify the selected_options list to choose different options
    # Options available: 0, 1, 2, 3, 4, 5
    
    automation = IDXAutomationTest(
        download_folder="Keterbukaan Informasi IDX",
        selected_options=[0, 1, 2]  # Select options 0, 1, and 2
    )
    
    automation.run()
