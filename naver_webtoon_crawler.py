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

# 세부 크롤링 URL 리스트화 (무한 스크롤 처리))

# 세부 페이지 정보 크롤링

# 데이터베이스 연동

# 데이터베이스에 데이터 저장

# 메인 실행 로직

# 스크립트 실행