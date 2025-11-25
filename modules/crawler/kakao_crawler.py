import time
import random
import pickle

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from .base_crawler import BaseCrawler

from config import KAKAO_COOKIE_FILE

class KakaoCrawler(BaseCrawler):

    def login(self):
        self.driver.get("https://page.kakao.com/")
        time.sleep(1)

        if KAKAO_COOKIE_FILE.exists():
            print(f"🍪 기존 쿠키 파일을 적용합니다.")
            try:
                cookies = pickle.load(open(KAKAO_COOKIE_FILE, "rb"))
                for c in cookies:
                    if 'expiry' in c: del c['expiry']
                    c['domain'] = '.kakao.com'
                    self.driver.add_cookie(c)
                self.driver.get("https://page.kakao.com/")
                time.sleep(2)
                
                try:
                    profile_img = self.driver.find_elements(By.XPATH, "//img[@alt='프로필' or contains(@src, 'profile')]")
                    if len(profile_img) > 0:
                        print("✅ 쿠키 로그인 성공")
                        return True
                except:
                    pass
                    
                    
            except Exception as e:
                print(f"⚠️ 쿠키 적용 실패: {e}")

        print("\n" + "="*40)
        print("🚨 [중요] 브라우저에서 수동 로그인을 진행해주세요!")
        print("1. 카카오페이지 로그인 & 성인 인증까지 완료하세요.")
        print("2. 페이지가 정상적으로 보이는 상태에서 아래 엔터를 누르세요.")
        print("="*40)

        self.driver.get("https://accounts.kakao.com/login/?continue=https%3A%2F%2Fkauth.kakao.com%2Foauth%2Fauthorize%3Fclient_id%3D49bbb48c5fdb0199e5da1b89de359484%26state%3Dhttps%25253A%25252F%25252Fpage.kakao.com%25252Fmenu%25252F10010%25252Fscreen%25252F93%26redirect_uri%3Dhttps%253A%252F%252Fpage.kakao.com%252Frelay%252Flogin%26response_type%3Dcode%26auth_tran_id%3DW3lvNUKSoQz6HLrxqft_Qn0McwWmXpOWQ7Zo.f_58sE5Hx7anOVDmu5vgoIS%26ka%3Dsdk%252F2.1.0%2520os%252Fjavascript%2520sdk_type%252Fjavascript%2520lang%252Fko-KR%2520device%252FMacIntel%2520origin%252Fhttps%25253A%25252F%25252Fpage.kakao.com%26is_popup%3Dfalse%26through_account%3Dtrue&talk_login=hidden#login")
        input("👉 준비가 다 되면 여기를 클릭하고 [Enter] 키를 누르세요...")

        time.sleep(2)
        try:
            # 탭 재연결 시도
            handles = self.driver.window_handles
            if handles: self.driver.switch_to.window(handles[-1])
        except: pass

        print("✅ 확인되었습니다. 현재 로그인 상태를 쿠키로 저장합니다.")
        pickle.dump(self.driver.get_cookies(), open(KAKAO_COOKIE_FILE, "wb"))
        return True