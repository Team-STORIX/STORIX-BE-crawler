import os
from dotenv import load_dotenv
import pathlib

load_dotenv()

# 디렉토리 및 파일 경로
BASE_DIR = pathlib.Path(__file__).parent
COOKIE_FILE = BASE_DIR / "naver_cookies.pkl"
FAILED_CSV = BASE_DIR / "failed_rows.csv"

# 네이버 웹툰 설정
BASE_URL = 'https://comic.naver.com/webtoon?tab=genre&genre='
GENRES = ["PURE", "FANTASY", "DAILY", "로판", "HISTORICAL"]

# 데이터베이스 설정 
MYSQL_CONFIG = {
    'host': os.getenv("MYSQL_DATABASE_HOST", "localhost"),
    'user': os.getenv("MYSQL_DATABASE_USER", "root"),
    'password': os.getenv("MYSQL_DATABASE_PASSWORD", ""),
    'database': os.getenv("MYSQL_DATABASE_NAME", "webtoon_db"),
    'charset': 'utf8mb4',
}