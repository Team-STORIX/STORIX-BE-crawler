import time
import random
from config import MYSQL_CONFIG, GENRES, BASE_URL, GENRE_MAP
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

        print("\n🚀 크롤링을 시작합니다...")
        total_saved = 0

        # 3. 장르별 순회
        for genre_code in GENRES:
            target_genre_ko = GENRE_MAP.get(genre_code, genre_code)
            print(f"\n=== [장르 수집 시작: {genre_code} ({target_genre_ko})] ===")
            
            urls = crawler.get_genre_urls(BASE_URL + genre_code)
            print(f"📊 수집 대상: 총 {len(urls)}개 작품")

            for i, url in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}] 진행 중...", end='\r')
                
                data = crawler.crawl_detail(url)
                if data:
                    # [핵심 수정] '로판' 장르 수집 시에만 강제로 장르명 고정
                    # 다른 장르는 상세 페이지에 적힌 원래 장르를 그대로 사용
                    if genre_code == '로판':
                        data['genre'] = '로판'
                    
                    if save_one_row(conn, cursor, data):
                        total_saved += 1
                        #print(f"✅ [저장완료] {data['works_name']}" + " "*20)
                
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