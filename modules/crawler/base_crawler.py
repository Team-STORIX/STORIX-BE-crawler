import time
import random
import pickle

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class BaseCrawler:
    def __init__(self):
        self.driver = None

    def start_driver(self):
        if self.driver is not None: return
        print("🔧 브라우저를 시작합니다...")
        options = Options()
        options.add_argument("--window-size=1600,900")
        options.add_argument("--lang=ko-KR")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"""
        })
    
    def close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def human_pause(self, min_s=1.0, max_s=2.0):
        time.sleep(random.uniform(min_s, max_s))