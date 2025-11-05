# Selenium WebDriver
from selenium import webdriver

# Service, Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ( TimeoutException, NoSuchElementException )
from selenium.common.exceptions import StaleElementReferenceException

# MySQL connector
import mysql.connector
from mysql.connector import Error as MySQLError

# Others
import time
import random
import getpass


# ---- 크롤링 URL 설정 ----
BASE_URL = 'https://comic.naver.com/webtoon?tab=genre&genre='
GENRES = ["PURE", "FANTASY", "DAILY", "로판", "HISTORICAL"]


# ---- Selenium WebDriver 설정 ----
def create_driver():

    customService = Service()
    customOptions = Options()

    driver = webdriver.Chrome(service=customService, options=customOptions)

    return driver

# 데이터 전처리

# 네이버 로그인 
def naver_login(driver, list_url):
    
    print(f"로그인 세션을 얻기 위해 {list_url}로 이동합니다.")
    driver.get(list_url)

    driver.implicity_wait(10)

    try: 
        
        print("---- 로그인을 위해 리스트의 첫 번째 작품 클릭 ----")

        first_webtoon_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='content']/div[1]/ul/li[1]/a"))
        )

        first_webtoon_link.click()

        print("\n" + "---" * 10)
        print("자동 로그인 시도: 터미널에 ID / PW를 입력")

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="id"]'))
        )

        # ID / PW 입력
        user_id = input("아이디: ")
        user_pw = getpass.getpass("비밀번호: ")

        # ID / PW 필드에 값 입력 & 로그인 버튼 클릭
        driver.find_element(By.XPATH, '//*[@id="id"]').send_keys(user_id)
        driver.find_element(By.XPATH, '//*[@id="pw"]').send_keys(user_pw)
        driver.find_element(By.XPATH, '//*[@id="log.login"]').click()
        
        # 로그인 성공 시, 첫 번째 작품 페이지 로드 대기
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[1]/div/h2')) 
        )
        
        print("✅ 로그인 성공")

        # 전체 리스트 페이지로 이동 후 로드 대기
        driver.get(list_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='content']/div[1]/ul"))
        )

        return True


    except TimeoutException:
        print("❌ 로그인 실패: timeout 또는 페이지 로드 실패")
        return False
    
    except Exception as e:
        print(f"❌ 로그인 실패: 예외 발생 ({e})")
        return False


# 세부 크롤링 URL 리스트화 (무한 스크롤 처리)

# 세부 페이지 정보 크롤링

# 데이터베이스 연동

# 데이터베이스에 데이터 저장

# 메인 실행 로직

# 스크립트 실행