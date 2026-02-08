import os
import time
from selenium import webdriver
from threading import Thread
from dotenv import load_dotenv

# ← IMPORT YOUR ORIGINAL SCRAPER
from elpais_scraper import ElPaisScraper

load_dotenv()

BROWSERSTACK_USERNAME = os.getenv('BROWSERSTACK_USERNAME')
BROWSERSTACK_ACCESS_KEY = os.getenv('BROWSERSTACK_ACCESS_KEY')

BS_HUB_URL = f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"

BROWSER_CONFIGS = [
    {
        'name': 'Chrome_Windows_10',
        'bstack:options': {
            'os': 'Windows',
            'osVersion': '10',
            'browserVersion': 'latest',
            'userName': BROWSERSTACK_USERNAME,
            'accessKey': BROWSERSTACK_ACCESS_KEY,
            'projectName': 'El País Scraper',
            'buildName': 'Opinion Section Scraper - Parallel Test',
            'sessionName': 'Chrome on Windows 10',
        },
        'browserName': 'Chrome',
    },
    {
        'name': 'Firefox_Windows_11',
        'bstack:options': {
            'os': 'Windows',
            'osVersion': '11',
            'browserVersion': 'latest',
            'userName': BROWSERSTACK_USERNAME,
            'accessKey': BROWSERSTACK_ACCESS_KEY,
            'projectName': 'El País Scraper',
            'buildName': 'Opinion Section Scraper - Parallel Test',
            'sessionName': 'Firefox on Windows 11',
        },
        'browserName': 'Firefox',
    },
    {
        'name': 'Safari_MacOS',
        'bstack:options': {
            'os': 'OS X',
            'osVersion': 'Ventura',
            'browserVersion': 'latest',
            'userName': BROWSERSTACK_USERNAME,
            'accessKey': BROWSERSTACK_ACCESS_KEY,
            'projectName': 'El País Scraper',
            'buildName': 'Opinion Section Scraper - Parallel Test',
            'sessionName': 'Safari on macOS',
        },
        'browserName': 'Safari',
    },
    {
        'name': 'Chrome_Samsung_Galaxy',
        'bstack:options': {
            'deviceName': 'Samsung Galaxy S23',
            'osVersion': '13.0',
            'realMobile': True,
            'userName': BROWSERSTACK_USERNAME,
            'accessKey': BROWSERSTACK_ACCESS_KEY,
            'projectName': 'El País Scraper',
            'buildName': 'Opinion Section Scraper - Parallel Test',
            'sessionName': 'Chrome on Samsung Galaxy S23',
        },
        'browserName': 'chrome',
    },
    {
        'name': 'Safari_iPhone_14',
        'bstack:options': {
            'deviceName': 'iPhone 14',
            'osVersion': '16',
            'realMobile': True,
            'userName': BROWSERSTACK_USERNAME,
            'accessKey': BROWSERSTACK_ACCESS_KEY,
            'projectName': 'El País Scraper',
            'buildName': 'Opinion Section Scraper - Parallel Test',
            'sessionName': 'Safari on iPhone 14',
        },
        'browserName': 'safari',
    }
]


class BrowserStackTest:
    def __init__(self, config):
        self.config = config
        self.driver = None
    
    def run_test(self):
        try:
            print(f"\n{'='*60}")
            print(f"🚀 Starting: {self.config['name']}")
            print(f"{'='*60}")
            
            browser_name = self.config.get('browserName', 'chrome').lower()
            
            if browser_name == 'chrome':
                from selenium.webdriver.chrome.options import Options
                options = Options()
            elif browser_name == 'firefox':
                from selenium.webdriver.firefox.options import Options
                options = Options()
            elif browser_name == 'safari':
                from selenium.webdriver.safari.options import Options
                options = Options()
            else:
                from selenium.webdriver.chrome.options import Options
                options = Options()
            
            for key, value in self.config.items():
                options.set_capability(key, value)
            
            # Create BrowserStack remote driver
            self.driver = webdriver.Remote(
                command_executor=BS_HUB_URL,
                options=options
            )
            
            print(f"[{self.config['name']}] ✓ Browser session started")
            
            # ← USE YOUR ORIGINAL SCRAPER with BrowserStack driver
            scraper = ElPaisScraper(driver=self.driver)
            success = scraper.run(close_driver=False)  # Don't let scraper close our driver
            
            if success:
                self.driver.execute_script(
                    'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"passed", "reason": "Scraping completed successfully"}}'
                )
                print(f"\n✅ [{self.config['name']}] TEST PASSED")
            else:
                self.driver.execute_script(
                    'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": "Scraping failed"}}'
                )
                print(f"\n❌ [{self.config['name']}] TEST FAILED")
            
        except Exception as e:
            print(f"\n❌ [{self.config['name']}] ERROR: {str(e)}")
            if self.driver:
                try:
                    self.driver.execute_script(
                        'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": "' + str(e).replace('"', "'") + '"}}'
                    )
                except:
                    pass
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print(f"[{self.config['name']}] ✓ Session closed")
                except:
                    pass


def run_parallel_tests():
    print("\n" + "🌐"*30)
    print("BROWSERSTACK PARALLEL TESTS")
    print("🌐"*30)
    
    if not BROWSERSTACK_USERNAME or not BROWSERSTACK_ACCESS_KEY:
        print("\n⚠️  ERROR: BrowserStack credentials missing in .env!")
        print("Add BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY to .env")
        return
    
    print(f"\nRunning full scraper across {len(BROWSER_CONFIGS)} browsers:")
    for i, config in enumerate(BROWSER_CONFIGS, 1):
        print(f"  {i}. {config['name']}")
    print()
    
    threads = []
    for config in BROWSER_CONFIGS:
        test = BrowserStackTest(config)
        thread = Thread(target=test.run_test)
        threads.append(thread)
    
    for thread in threads:
        thread.start()
        time.sleep(1)
    
    for thread in threads:
        thread.join()
    
    print("\n" + "="*60)
    print("✅ ALL PARALLEL TESTS COMPLETED!")
    print("="*60)
    print(f"\n📊 View at: https://automate.browserstack.com/dashboard")


if __name__ == "__main__":
    run_parallel_tests()