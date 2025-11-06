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
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

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


# 모든 웹툰 아이템 로드 ....?
def load_all_webtoon_items():
    return

# 세부 크롤링 URL 리스트화 ....?
def get_webtoon_urls(driver, list_url):

    print(f"작품 리스트 페이지로 이동: {list_url}")
    driver.get(list_url)
    driver.implicity_wait(10)

    # URL 리스트 초기화
    webtoon_urls = []


    return 


# 세부 페이지 정보 크롤링
def crawl_webtoon_details(driver, url):
    return

# 데이터베이스 연동
def connect_database(config):

    try:

        connection = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'], 
            database=config['database'], 
            charset='utf8mb4'
        )
        print("✅ 데이터베이스 연결 성공")
        return connection
    
    except MySQLError as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

# 데이터베이스에 데이터 저장
def save_to_database(connection, cursor, data):

    try:
        # 데이터 전처리
        db_genre = data['genre'].lstrip('#').strip()
        db_age_classification = data['age_classification'].replace(' ', '').strip()
        
        if db_age_classification in ['전체이용가', '전체연령가', '전체']:
            db_age_classification = '전체연령가'
        elif db_age_classification in ['12세이용가', '12']:
            db_age_classification = '12세 이용가'
        elif db_age_classification in ['15세이용가', '15']:
            db_age_classification = '15세 이용가'
        elif db_age_classification in ['18세이용가', '19세이상', '19']:
            db_age_classification = '18세 이용가'
        else:
            db_age_classification = '전체연령가'

        # 데이터 삽입 쿼리
        insert_query = """
        INSERT INTO works 
        (platform, works_name, artist_name, age_classification, 
         description, genre, thumbnail_url, `type`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        insert_values = (
            data['platform'], data['works_name'], data['artist_name'],
            db_age_classification, data['description'], db_genre,
            data['thumbnail_url'], data['type']
        )
        
        cursor.execute(insert_query, insert_values)
        connection.commit()

        print(f"✅ [DB 저장 성공] {data['works_name']}] - {data['artist_name']}")
        return True
    
    except MySQLError as e:
        error_code = e.errno

        if error_code == 1062: # 중복
            print(f"❌ [중복] 이미 존재하는 작품입니다: {data['works_name']}")
        elif error_code == 1265: # ENUM 불일치
            print(f"❌ [DB 오류] ENUM 값 불일치 (genre='{db_genre}', age='{db_age_classification}')")
        else:
            print(f"❌ [DB 오류] {data['works_name']} 저장 실패: {e}")

        connection.rollback()
        return False
    
    except Exception as e:
        print(f"❌ [Python 오류] DB 처리 중 예외 발생: {e}")
        connection.rollback()
        return False

# 메인 실행 로직
def main():

    db_host = os.getenv("MYSQL_DATABASE_HOST")
    db_user = os.getenv("MYSQL_DATABASE_USER")
    db_password = os.getenv("MYSQL_DATABASE_PASSWORD")
    db_name = os.getenv("MYSQL_DATABASE_NAME")

    MYSQL_CONFIG = {
        'host': db_host,
        'user': db_user,
        'password': db_password,
        'database': db_name
    }

    connection = None
    cursor = None
    driver = None
    
    try:
        # 데이터베이스 연결
        connection = connect_database(MYSQL_CONFIG)

        if connection is None:
            raise Exception("❌ 데이터베이스 연결 실패")
        
        cursor = connection.cursor()

        # Selenium WebDriver 설정
        driver = create_driver()

        # 네이버 로그인
        first_webtoon_link = BASE_URL + GENRES[0]

        if not naver_login(driver, first_webtoon_link):
            raise Exception("❌ 네이버 로그인 실패")
        

        # 장르별 URL 수집
        all_unique_urls = set()
        print("\n" + "---" * 10 + "\n[1] 전체 URL 수집 시작\n" + "---" * 10)

        for genre in GENRES:
            current_list_url = BASE_URL + genre
            print(f"\n--- [ {genre} ] 장르 페이지 URL 수집 중... ---")
            genre_urls = get_webtoon_urls(driver, current_list_url)
            all_unique_urls.update(genre_urls)
            print(f"[ {genre} ] 완료. (현재 총 {len(all_unique_urls)}개 고유 URL)")
            time.sleep(random.uniform(1.0, 2.0)) 

        urls_to_scrape = list(all_unique_urls)

        if not urls_to_scrape:
            raise Exception("수집할 URL이 없습니다.")
            
        # 장르 URL 순회해 세부 정보 크롤링 및 DB 저장
        print("\n" + "---" * 10 + f"\n[2] 총 {len(urls_to_scrape)}개 세부 정보 스크래핑 및 DB 저장 시작\n" + "---" * 10)

        all_scraped_data_count = 0

        for i, url in enumerate(urls_to_scrape):
            print(f"\n({i+1}/{len(urls_to_scrape)}) 스크래핑 중: {url}")
            data = crawl_webtoon_details(driver, url)
            
            if data:
                print(f"  > [스크래핑 성공] {data['works_name']} ({data['artist_name']})")
                if save_to_database(connection, cursor, data):
                    all_scraped_data_count += 1
            
            time.sleep(random.uniform(1.2, 2.5))

            print("\n" + "---" * 10 + "\n[3] 전체 크롤링 완료!\n" + "---" * 10)
        print(f"✅ 총 {all_scraped_data_count}개의 작품 데이터를 DB에 성공적으로 저장했습니다.")

    except Exception as e:
        print(f"❌ 메인 로직 실행 중 오류 발생: {e}")

    finally:
        # 모든 리소스 종료
        if driver:
            driver.quit()
            print("Selenium 드라이버를 종료했습니다.")
        if cursor:
            cursor.close()
            print("MySQL 커서를 닫았습니다.")
        if connection:
            connection.close()
            print("MySQL 연결을 종료했습니다.")

# 스크립트 실행
if __name__ == "__main__":
    main()
