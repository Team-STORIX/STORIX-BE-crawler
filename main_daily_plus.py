import time
import random
from config import MYSQL_CONFIG, DAILY_PLUS_URL
import traceback
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from modules.db_handler import connect_database, save_one_row
from modules.crawler import WebtoonCrawler

# 2차 크롤링: 매일+ 
def main():
    conn = connect_database(MYSQL_CONFIG)
    if not conn:
        return
    cursor = conn.cursor()

    crawler = WebtoonCrawler()
    try:
        crawler.start_driver()
        if not crawler.login():
            raise Exception("로그인 실패로 프로그램을 종료합니다.")

        print("\n🚀 [매일+] 크롤링을 시작합니다...")
        
        while True:
            try:
                if not crawler.driver:
                    print("🔄 브라우저 재시작 중...")
                    crawler.start_driver()
                    crawler.login()

                # 매일+ URL에서 작품 목록 가져오기
                target_urls = crawler.get_genre_urls(DAILY_PLUS_URL)
                print(f"📊 [매일+] 수집 대상: 총 {len(target_urls)}개 작품")
                break

            except (InvalidSessionIdException, WebDriverException):
                print("⚠️ [오류] 목록 수집 중 세션 끊김. 5초 후 재시도...")
                crawler.close_driver()
                time.sleep(5)
                continue

            # 3. 상세 페이지 순회
        total_saved = 0
        for i, url in enumerate(target_urls, 1):
            print(f"[{i}/{len(target_urls)}] 진행 중...", end='\r')
            
            try:
                data = crawler.crawl_detail(url)
                
                if data:
                    if save_one_row(conn, cursor, data):
                        total_saved += 1

            except (InvalidSessionIdException, WebDriverException):
                print(f"\n⚠️ [오류] 상세 페이지({url}) 수집 중 세션 끊김. 재연결 시도...")
                crawler.close_driver()
                crawler.start_driver()
                crawler.login()
                continue
            
            time.sleep(random.uniform(1.5, 3.5))

    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단되었습니다.")
    except Exception as e:
        traceback.print_exc()
        print(f"\n❌ 치명적 오류 발생: {e}")
    finally:
        if 'crawler' in locals():
            crawler.close_driver()
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print(f"🎉 [매일+] 작업 종료. 총 {total_saved}개 작품 처리 완료.")

if __name__ == "__main__":
    main()