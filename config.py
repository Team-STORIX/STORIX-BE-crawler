import os
from dotenv import load_dotenv
import pathlib

load_dotenv()

# 디렉토리 및 파일 경로
BASE_DIR = pathlib.Path(__file__).parent
COOKIE_FILE = BASE_DIR / "naver_cookies.pkl"
FAILED_CSV = BASE_DIR / "failed_rows.csv"

# ---- 네이버 웹툰 설정 ----

# 1차 크롤링 URL 및 장르 목록
BASE_URL = 'https://comic.naver.com/webtoon?tab=genre&genre='
GENRES = ["PURE", "FANTASY", "DAILY", "로판", "HISTORICAL"]

# 2차 크롤링 URL (daily - 인기순)
DAILY_PLUS_URL = 'https://comic.naver.com/webtoon?tab=dailyPlus'

GENRE_MAP = {
    "PURE": "로맨스",
    "FANTASY": "판타지",
    "DAILY": "일상",
    "로판": "로판",
    "HISTORICAL": "무협/사극" 
}

# 데이터베이스 설정 
MYSQL_CONFIG = {
    'host': os.getenv("MYSQL_DATABASE_HOST", "localhost"),
    'user': os.getenv("MYSQL_DATABASE_USER", "root"),
    'password': os.getenv("MYSQL_DATABASE_PASSWORD", ""),
    'database': os.getenv("MYSQL_DATABASE_NAME", "storix"),
    'charset': 'utf8mb4',
}