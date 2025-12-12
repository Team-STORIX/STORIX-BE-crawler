import time
import random
from config import MYSQL_CONFIG, WEBTOON_TOP_300_URL, WEBTOON_FANTASY_URL, WEBTOON_ROFAN_URL, NOVEL_TOP_300_URL, NOVEL_ROFAN_URL, NOVEL_FANTASY_URL
from modules.db_handler import connect_database, save_one_row
from modules.crawler.kakao_crawler import KakaoCrawler 

# 카카오페이지 타겟 URL (요일별/전체 등)

def main():
    conn = connect_database(MYSQL_CONFIG)
    if not conn: return
    cursor = conn.cursor()

    crawler = KakaoCrawler()
    
    try:
        crawler.start_driver()
        if not crawler.login(): return
        
        print(f"\n🚀 [카카오페이지] 크롤링 시작: {WEBTOON_ROFAN_URL}")
        
        urls = crawler.get_list_urls(WEBTOON_ROFAN_URL)

        total_saved = 0
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] 진행 중...", end='\r')
            
            data = crawler.crawl_detail(url)
            if data:
                save_one_row(conn, cursor, data)
                total_saved += 1
            
            time.sleep(random.uniform(1.5, 3.0))

    except KeyboardInterrupt:
        print("\n🛑 중단됨")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        if 'crawler' in locals():
            crawler.close_driver()
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print(f"🎉 [카카오페이지] 작업 종료. 총 {total_saved}개 작품 처리 완료.")

if __name__ == "__main__":
    main()