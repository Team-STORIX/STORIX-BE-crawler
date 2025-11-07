# Selenium WebDriver
from selenium import webdriver

# Service, Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    InvalidSessionIdException, WebDriverException
)


# MySQL connector
import mysql.connector
from mysql.connector import Error as MySQLError

# Others
import time
import csv
import random
import pathlib
import getpass
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# ---- 크롤링 URL 설정 ----
BASE_URL = 'https://comic.naver.com/webtoon?tab=genre&genre='
GENRES = ["PURE", "FANTASY", "DAILY", "로판", "HISTORICAL"]

PROFILE_DIR = pathlib.Path(os.path.expanduser("~/chrome-scrape-profile"))  # 세션/쿠키 재사용
FAILED_CSV  = pathlib.Path("./failed_rows.csv")
DB_COMMIT_BATCH_SIZE = 25


# ---- Selenium WebDriver 설정 ----
def create_driver():

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    customService = Service()
    customOptions = Options()

    customOptions.add_argument("--window-size=1400,1000")
    customOptions.add_argument("--lang=ko-KR")
    customOptions.add_argument(f"--user-data-dir={PROFILE_DIR}")
    customOptions.add_argument("--profile-directory=Default")

    driver = webdriver.Chrome(service=customService, options=customOptions)

    driver.implicitly_wait(5)


    return driver

# 드라이버 헬스체크
def is_driver_alive(driver):
    try:
        driver.execute_script("return 1")
        return True
    except (InvalidSessionIdException, WebDriverException):
        return False

# 자동화 탐지 회피용
def human_pause(min_s=0.8, max_s=1.6):
    time.sleep(random.uniform(min_s, max_s))

# 네이버 로그인 
def naver_login(driver, list_url):
    
    print(f"로그인 세션을 얻기 위해 {list_url}로 이동합니다.")
    driver.get(list_url)

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

# 스크롤 대상 탐색
def find_scroll_target(driver):

    js = """
    const all = Array.from(document.querySelectorAll('body *'));
    for (const el of all) {
      const st = getComputedStyle(el);
      if ((st.overflowY === 'auto' || st.overflowY === 'scroll') &&
          el.scrollHeight > el.clientHeight &&
          el.getBoundingClientRect().height > 0) {
        return el;
      }
    }
    return null;
    """
     
    return driver.execute_script(js)

def _at_bottom(driver, container):
    if container:
        return driver.execute_script(
            "return Math.ceil(arguments[0].scrollTop + arguments[0].clientHeight) >= arguments[0].scrollHeight - 2;",
            container)
    return driver.execute_script(
        "return Math.ceil(window.scrollY + window.innerHeight) >= document.body.scrollHeight - 2;"
    )


DETAIL_LOCATORS = {
    "title": [
        (By.CSS_SELECTOR, "#content h2"),
        (By.XPATH, "//div[@id='content']//h2"),
        (By.XPATH, "//*[@id='content']/div[1]/div/h2")
    ],
    "artist": [
        (By.CSS_SELECTOR, "#content span[class*='Author'], #content span[class*='author']"),
        (By.XPATH, "//div[@id='content']//span[contains(@class,'Author')]"),
        (By.XPATH, "//*[@id='content']/div[1]/div/div[1]/span")
    ],
    "description": [
        (By.CSS_SELECTOR, "#content p"),
        (By.XPATH, "//div[@id='content']//p"),
        (By.XPATH, "//*[@id='content']/div[1]/div/div[2]/p")
    ],
    "genre": [
        (By.CSS_SELECTOR, "#content a[href*='genre'], #content a[class*='Tag'], #content a[class*='Genre']"),
        (By.XPATH, "//div[@id='content']//a[contains(@class,'Tag') or contains(@class,'genre')]"),
        (By.XPATH, "//*[@id='content']/div[1]/div/div[2]/div/div/a[1]")
    ],
    "age": [
        (By.CSS_SELECTOR, "#content em"),
        (By.XPATH, "//div[@id='content']//em[contains(text(),'세') or contains(text(),'전체')]"),
        (By.XPATH, "//*[@id='content']/div[1]/div/div[1]/em")
    ]
}


def extract_text_with_fallback(driver, locators, timeout=10):
    last_error = None
    for locator in locators:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            text = element.text.strip()
            if text:
                return text
        except (TimeoutException, NoSuchElementException) as exc:
            last_error = exc
    raise last_error or NoSuchElementException("요소를 찾을 수 없습니다.")

# 모든 웹툰 아이템 로드 (무한 스크롤 로더))
def load_all_webtoon_items_by_scroll(
        driver, item_xpath,
        max_rounds=200, idle_rounds=3,
        wait_per_round=4.0, pause_range=(0.25, 0.5)):
    """작게-여러번 스크롤 + 증가 폴링. 최하단 도착 시 종료."""
    try:
        driver.set_window_size(1400, 1000)
    except Exception:
        pass

    container = find_scroll_target(driver)

    def count_items():
        try:
            return len(driver.find_elements(By.XPATH, item_xpath))
        except Exception:
            return 0

    prev_count = count_items()
    stagnant = 0
    bottom_hits = 0

    for _ in range(max_rounds):
        # 마지막 li 가시화 (IntersectionObserver 트리거)
        try:
            items = driver.find_elements(By.XPATH, item_xpath)
            if items:
                driver.execute_script("arguments[0].scrollIntoView({block:'end'});", items[-1])
        except StaleElementReferenceException:
            pass

        # 한 스텝만 내리기
        if container:
            driver.execute_script(
                "arguments[0].scrollTop = Math.min(arguments[0].scrollTop + Math.floor(window.innerHeight*0.85), arguments[0].scrollHeight);",
                container)
        else:
            driver.execute_script("window.scrollBy(0, Math.floor(window.innerHeight*0.85));")

        time.sleep(random.uniform(*pause_range))

        # 증가 폴링
        grew = False
        start = time.time()
        while time.time() - start < wait_per_round:
            cur = count_items()
            if cur > prev_count:
                prev_count = cur
                grew = True
                break
            time.sleep(0.2)

        # 바닥 감지: 증가 없고 바닥이면 종료(2회 확인)
        if not grew and _at_bottom(driver, container):
            bottom_hits += 1
            if bottom_hits >= 2:
                break
        else:
            bottom_hits = 0

        if grew:
            stagnant = 0
            continue
        else:
            stagnant += 1
            if stagnant >= idle_rounds:
                break

    return prev_count

# 세부 크롤링 URL 리스트화
def get_webtoon_urls(driver, list_url):
    print(f"작품 리스트 페이지로 이동합니다: {list_url}")
    driver.get(list_url)

    try:
        # 리스트 UL 로드 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='content']/div[1]/ul"))
        )
        # 네이버 장르 페이지 기준 li/a
        item_xpath = "//div[@id='content']/div[1]/ul/li/a"

        total = load_all_webtoon_items_by_scroll(driver, item_xpath)
        print(f"무한 스크롤 로딩 완료. 감지된 항목 수: {total}")

        urls = []
        for a in driver.find_elements(By.XPATH, item_xpath):
            href = a.get_attribute("href")
            if href and "list?titleId=" in href:
                urls.append(href)

        unique_urls = list(dict.fromkeys(urls))
        print(f"총 {len(unique_urls)}개의 고유 작품 URL 수집.")
        return unique_urls

    except Exception as e:
        print(f"❌ 작품 URL 수집 중 오류 발생: {e}")
        return []

# 썸네일 이미지 정보 추출
def get_thumbnail_url(driver):

    # 1) og:image (가장 안정)
    try:
        og = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']")
        content = og.get_attribute("content")
        if content:
            return content
    except NoSuchElementException:
        pass

    # 2) Poster 구조
    try:
        thumb_img = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//*[@id='content']//button[contains(@class,'Poster__link')]"
                "//div[contains(@class,'Poster__thumbnail_area')]"
                "//img[contains(@class,'Poster__image')]"
            ))
        )
        src = thumb_img.get_attribute("src")
        if src:
            return src
    except TimeoutException:
        pass


    # 3) 기타 이미지 백업
    xpaths = [
        "//*[@id='content']//div[contains(@class,'Poster__thumbnail_area')]//img",
        "//*[@id='content']//img"
    ]
    for xp in xpaths:
        for el in driver.find_elements(By.XPATH, xp):
            src = el.get_attribute("src") or el.get_attribute("data-src")
            if src and ('image-comic' in src or 'webtoon' in src or src.endswith(('.jpg','.jpeg','.png','.webp'))):
                return src
    return None


# 세부 페이지 정보 크롤링
def crawl_webtoon_details(driver, url):

    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "content"))
        )

        works_name = extract_text_with_fallback(driver, DETAIL_LOCATORS["title"])
        artist_name = extract_text_with_fallback(driver, DETAIL_LOCATORS["artist"])
        description = extract_text_with_fallback(driver, DETAIL_LOCATORS["description"]).replace("\n", " ").strip()
        genre = extract_text_with_fallback(driver, DETAIL_LOCATORS["genre"]).lstrip('#').strip()

        age_raw = extract_text_with_fallback(driver, DETAIL_LOCATORS["age"])
        age_classification = age_raw.strip().split('∙')[-1].strip()
        
        thumbnail_url = get_thumbnail_url(driver)
        
        webtoon_data = {
            "platform": "네이버 웹툰", 
            "works_name": works_name,
            "artist_name": artist_name, 
            "age_classification": age_classification,
            "description": description, 
            "genre": genre,
            "thumbnail_url": thumbnail_url, 
            "type": "웹툰",
            "source_url": url
        }

        return webtoon_data
    
    except Exception as e:
        print(f"❌ [오류] {url} 스크래핑 중 문제 발생: {e}")
        return None

# DB 연결 & 저장 (멱등 + 항목 단위 커밋 + 실패 백업)
def connect_database(cfg):
    try:
        conn = mysql.connector.connect(
            host=cfg['host'], user=cfg['user'], password=cfg['password'],
            database=cfg['database'], charset='utf8mb4'
        )
        try:
            conn.autocommit = False
        except AttributeError:
            pass
        print("✅ 데이터베이스 연결 성공")
        return conn
    except MySQLError as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def ensure_failed_csv_header():
    if not FAILED_CSV.exists():
        with open(FAILED_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                "platform","works_name","artist_name","age_classification",
                "description","genre","thumbnail_url","type","source_url","error"
            ])

def backup_row(row, err_msg):
    ensure_failed_csv_header()
    with open(FAILED_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            row.get("platform"), row.get("works_name"), row.get("artist_name"),
            row.get("age_classification"), row.get("description"),
            row.get("genre"), row.get("thumbnail_url"), row.get("type"),
            row.get("source_url"), err_msg
        ])

def normalize_age(age_text: str) -> str:
    t = (age_text or "").replace(" ", "").strip()
    if t in ('전체연령가','전체이용가','전체'): return '전체연령가'
    if t in ('12세이용가','12'):               return '12세 이용가'
    if t in ('15세이용가','15'):               return '15세 이용가'
    if t in ('18세이용가','19세이상','19','청불','성인'): return '18세 이용가'
    return '전체연령가'

GENRE_EN_TO_KO = {
    "PURE": "로맨스",
    "ROMANCE": "로맨스",
    "FANTASY": "판타지",
    "DAILY": "일상",
    "SLICEOFLIFE": "일상",
    "HISTORICAL": "사극",
    "HISTORY": "사극",
    "ACTION": "무협",
    "MARTIALARTS": "무협",
}

def normalize_genre_for_enum(g: str) -> str:
    s = (g or "").strip().lstrip('#')
    english_key = s.replace(" ", "").upper()
    if english_key in GENRE_EN_TO_KO:
        s = GENRE_EN_TO_KO[english_key]
    for v in ['무협 / 사극','무협·사극','무협∙사극','무협ㆍ사극','무협／사극','무협,사극']:
        s = s.replace(v, '무협/사극')
    allowed = {'로맨스','판타지','일상','로판','무협','사극','무협/사극'}
    return s if s in allowed else '일상'

INSERT_SQL = """
INSERT INTO works
(platform, works_name, artist_name, age_classification, description, genre, thumbnail_url, `type`)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
  artist_name = VALUES(artist_name),
  age_classification = VALUES(age_classification),
  description = VALUES(description),
  genre = VALUES(genre),
  thumbnail_url = VALUES(thumbnail_url),
  `type` = VALUES(`type`)
"""


class BatchedDBWriter:
    def __init__(self, connection, cursor, batch_size=DB_COMMIT_BATCH_SIZE):
        self.connection = connection
        self.cursor = cursor
        self.batch_size = max(1, batch_size)
        self.pending_values = []

    def save(self, data):
        db_genre = normalize_genre_for_enum(data.get('genre'))
        db_age = normalize_age(data.get('age_classification'))
        vals = (
            data.get('platform'), data.get('works_name'), data.get('artist_name'),
            db_age, data.get('description'), db_genre, data.get('thumbnail_url'), data.get('type')
        )
        normalized_row = {**data, "genre": db_genre, "age_classification": db_age}

        try:
            self.cursor.execute(INSERT_SQL, vals)
            self.pending_values.append(vals)
            if len(self.pending_values) >= self.batch_size:
                self._commit_pending()
            print(f"✅ [DB] {data.get('works_name')}")
            return True
        except Exception as e:
            print(f"❌ [DB] {data.get('works_name')} -> {e}")
            backup_row(normalized_row, str(e))
            self.connection.rollback()
            self._reinsert_pending_after_rollback()
            return False

    def flush(self):
        self._commit_pending()

    def _commit_pending(self):
        if not self.pending_values:
            return
        try:
            self.connection.commit()
            self.pending_values.clear()
        except Exception as e:
            print(f"⚠️ [DB] 커밋 실패, 재시도: {e}")
            self.connection.rollback()
            self._reinsert_pending_after_rollback()

    def _reinsert_pending_after_rollback(self):
        if not self.pending_values:
            return
        snapshot = list(self.pending_values)
        self.pending_values.clear()
        try:
            self.cursor.executemany(INSERT_SQL, snapshot)
            self.connection.commit()
        except Exception as replay_err:
            print(f"❌ [DB] 배치 재적재 실패: {replay_err}")
            self.connection.rollback()
            for vals in snapshot:
                try:
                    self.cursor.execute(INSERT_SQL, vals)
                    self.connection.commit()
                except Exception as item_err:
                    print(f"❌ [DB] 단건 재적재 실패: {item_err}")
                    break

# 장르 단위 처리 (세션 자동 복구 + 주기적 재시작) 
def process_one(driver, url, db_writer):
    
    data = crawl_webtoon_details(driver, url)

    if not data:
        # 재시도 
        time.sleep(random.uniform(0.7, 1.2))
        data = crawl_webtoon_details(driver, url)
        if not data:
            return False

    return db_writer.save(data)

def crawl_one_genre(driver, db_writer, list_url, restart_every=200):
    print(f"\n--- 장르 시작: {list_url} ---")
    urls = get_webtoon_urls(driver, list_url)
    print(f"  URL {len(urls)}개")

    processed = 0
    for idx, url in enumerate(urls, 1):
        # 세션 죽었거나 주기 도달 시 재시작
        if (idx % restart_every == 0) or (not is_driver_alive(driver)):
            try: driver.quit()
            except: pass
            driver = create_driver()

        try:
            ok = process_one(driver, url, db_writer)
            if ok: processed += 1
        except (InvalidSessionIdException, WebDriverException) as e:
            print(f"⚠️ 세션 이슈 재시작: {e}")
            try: driver.quit()
            except: pass
            driver = create_driver()
            # 같은 URL 한 번 재시도
            try:
                ok = process_one(driver, url, db_writer)
                if ok: processed += 1
            except Exception as e2:
                print(f"❌ 재시도 실패: {url} -> {e2}")


        human_pause(0.8, 1.6)

        time.sleep(random.uniform(0.6, 1.2))

    db_writer.flush()

    print(f"--- 장르 완료: {list_url} (성공 {processed}/{len(urls)}) ---")
    return processed


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
    db_writer = None
    driver = None
    
    try:
        # 데이터베이스 연결
        connection = connect_database(MYSQL_CONFIG)

        if connection is None:
            raise Exception("❌ 데이터베이스 연결 실패")
        
        cursor = connection.cursor()
        db_writer = BatchedDBWriter(connection, cursor, batch_size=DB_COMMIT_BATCH_SIZE)

        # Selenium WebDriver 설정
        driver = create_driver()

        # 네이버 로그인
        first_webtoon_link = BASE_URL + GENRES[0]

        if not naver_login(driver, first_webtoon_link):
            raise Exception("❌ 네이버 로그인 실패")
        

        total_saved = 0

        print("\n" + "---"*10 + "\n[1] 장르별 수집/저장 시작\n" + "---"*10)
        for genre in GENRES:
            list_url = BASE_URL + genre
            saved = crawl_one_genre(driver, db_writer, list_url, restart_every=200)
            total_saved += saved
            print(f"✔️ {genre} 장르 저장 완료 (누적 {total_saved})")
            time.sleep(random.uniform(1.0, 2.0))

        if db_writer:
            db_writer.flush()

        print("\n" + "---"*10 + "\n[3] 전체 크롤링 완료!\n" + "---"*10)
        print(f"✅ 총 {total_saved}개의 작품을 저장했습니다.")

        
    except Exception as e:
        print(f"❌ 메인 로직 실행 중 오류 발생: {e}")

    finally:
        # 모든 리소스 종료
        if driver:
            driver.quit()
            print("Selenium 드라이버를 종료했습니다.")
        if db_writer:
            db_writer.flush()
        if cursor:
            cursor.close()
            print("MySQL 커서를 닫았습니다.")
        if connection:
            connection.close()
            print("MySQL 연결을 종료했습니다.")

# 스크립트 실행
if __name__ == "__main__":
    main()
