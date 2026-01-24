import os
import sys
import stat
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def run_e2e_test():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = None

    try:
        # 1. Install and locate driver
        driver_path = ChromeDriverManager().install()
        if "THIRD_PARTY_NOTICES" in driver_path:
            driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver")
        
        # 2. FORCE PERMISSIONS (Fixes 'wrong permissions' error)
        st = os.stat(driver_path)
        os.chmod(driver_path, st.st_mode | stat.S_IEXEC)
        print(f"✅ Driver ready and executable: {driver_path}")
        
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 3. App Interaction logic
        wait = WebDriverWait(driver, 15)
        driver.get("http://localhost:80")

        # Verify Modern UI
        logo = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        if "CNNCT" not in logo.text:
            print(f"❌ Stale UI error. Found: {logo.text}")
            sys.exit(1)

        target_input = wait.until(EC.presence_of_element_located((By.ID, "target-input")))
        print("⌨️  Submitting target 8.8.8.8...")
        target_input.send_keys("8.8.8.8")
        target_input.send_keys(Keys.ENTER)

        # 4. Results Check
        print("⏳ Waiting for backend...")
        wait.until(EC.text_to_be_present_in_element((By.ID, "results-area"), "Service Port"))
        
        results = driver.find_element(By.ID, "results-area").text
        if "ONLINE" in results or "OFFLINE" in results:
            print("✨ E2E SUCCESS: Results rendered correctly.")
        else:
            print("❌ Results container found but data missing.")
            sys.exit(1)

    except Exception as e:
        print(f"🔥 Test Error: {str(e)}")
        if driver:
            driver.save_screenshot("e2e_error.png")
            print("📸 Error screenshot saved.")
        sys.exit(1)
        
    finally:
        if driver:
            print("🛑 Closing browser.")
            driver.quit()

if __name__ == "__main__":
    run_e2e_test()