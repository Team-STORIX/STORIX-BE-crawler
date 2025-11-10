import time
import random
from config import MYSQL_CONFIG, GENRES, BASE_URL
from modules.db_handler import connect_database, save_one_row
from modules.crawler import WebtoonCrawler

def main():
    # 1. DB 연결
    conn = connect_database(MYSQL_CONFIG)
    if not conn:
        return
    cursor = conn.cursor()

    # 2. 크롤러 시작
    crawler = WebtoonCrawler()
    try:
        crawler.start_driver()
        if not crawler.login():
            raise Exception("로그인 실패로 프로그램을 종료합니다.")

        # 3. 장르별 순회
        for genre in GENRES:
            genre_url = BASE_URL + genre
            print(f"\n=== [장르 시작: {genre}] ===")
            
            target_urls = crawler.get_genre_urls(genre_url)
            
            for i, url in enumerate(target_urls, 1):
                print(f"[{i}/{len(target_urls)}] 처리 중...", end="\r")
                
                # 상세 페이지 크롤링
                data = crawler.crawl_detail(url)
                if data:
                    # DB 저장
                    save_one_row(conn, cursor, data)
                
                # 봇 탐지 회피를 위한 랜덤 대기
                crawler.human_pause(1.0, 2.5)

    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 치명적 오류 발생: {e}")
    finally:
        # 리소스 정리
        if 'crawler' in locals():
            crawler.close_driver()
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("데이터베이스 연결이 안전하게 종료되었습니다.")

if __name__ == "__main__":
    main()