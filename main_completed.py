import time
import random
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# config 및 모듈 임포트
from config import MYSQL_CONFIG, COMPLETED_URL
from modules.db_handler import connect_database, save_one_row
from modules.crawler import WebtoonCrawler

TARGET_LIMIT = 1000

def scroll_and_collect_urls(driver, limit=1000):
    """
    Footer가 커도 확실하게 로딩하는 '바닥 찍고 흔들기' 전략
    """
    print(f"📜 목표 {limit}개까지 스크롤을 시작합니다...")
    item_xpath = "//div[@id='content']/div[1]/ul/li/a"
    
    # 초기 아이템 수 확인
    prev_count = len(driver.find_elements(By.XPATH, item_xpath))
    stuck_count = 0  

    while True:
        if prev_count >= limit:
            print(f"\n✅ 목표 개수 도달 ({prev_count}개). 스크롤 중단.")
            break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.0) # 1차 대기

        # 3. 현재 아이템 수 체크
        elems = driver.find_elements(By.XPATH, item_xpath)
        curr_count = len(elems)
        
        print(f"  └─ 현재 {curr_count}개 로딩됨...", end='\r')

        if curr_count > prev_count:
            prev_count = curr_count
            stuck_count = 0 
        else:
            stuck_count += 1
            
            if stuck_count >= 3:
                print(f"\n⚠️ 더 이상 로딩되지 않습니다. (총 {curr_count}개)")
                break
            
            # footer 높이 처리
            driver.execute_script("window.scrollBy(0, -1500);")
            time.sleep(0.7)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # 다시 바닥으로
            time.sleep(1.5) 

    # URL 추출 및 반환
    urls = []
    elems = driver.find_elements(By.XPATH, item_xpath)
    for el in elems[:limit]:
        href = el.get_attribute('href')
        if href and 'titleId=' in href:
            urls.append(href)
            
    return list(dict.fromkeys(urls))

def main():
    conn = connect_database(MYSQL_CONFIG)
    if not conn: return
    cursor = conn.cursor()

    crawler = WebtoonCrawler()
    
    try:
        crawler.start_driver()
        if not crawler.login(): return
        
        print(f"\n🚀 [완결 웹툰] 페이지로 이동합니다: {COMPLETED_URL}")
        crawler.driver.get(COMPLETED_URL)
        time.sleep(2)

        # === [1단계] 인기순 ===
        print("\n=== [1단계] 인기순 정렬 선택 ===")
        try:
            # 인기순 버튼 클릭
            btn_popular = WebDriverWait(crawler.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="content"]/div[1]/div/div[2]/button[1]'))
            )
            btn_popular.click()
            time.sleep(2)
            
            popular_urls = scroll_and_collect_urls(crawler.driver, limit=TARGET_LIMIT)
            print(f"📊 [인기순] 수집 대상: {len(popular_urls)}개")

            for i, url in enumerate(popular_urls, 1):
                print(f"[인기순 {i}/{len(popular_urls)}] 진행 중...", end='\r')
                data = crawler.crawl_detail(url)
                if data:
                    save_one_row(conn, cursor, data)
                time.sleep(random.uniform(0.8, 1.5))

        except Exception as e:
            print(f"❌ [인기순] 진행 중 오류 발생: {e}")
            traceback.print_exc()

        # === [2단계] 별점순 ===
        print("\n\n=== [2단계] 별점순 정렬 선택 ===")
        try:
            # 메모리/DOM 초기화
            print("🔄 페이지를 새로고침하여 상태를 초기화합니다...")
            crawler.driver.get(COMPLETED_URL)
            time.sleep(3) # 페이지 로딩 대기

            print("👉 '별점순' 버튼 클릭 시도...")
            btn_star = WebDriverWait(crawler.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="content"]/div[1]/div/div[2]/button[4]'))
            )
            btn_star.click()
            time.sleep(2) # 리스트 갱신 대기

            # URL 수집
            star_urls = scroll_and_collect_urls(crawler.driver, limit=TARGET_LIMIT)
            print(f"📊 [별점순] 수집 대상: {len(star_urls)}개")

            # 상세 페이지 순회
            for i, url in enumerate(star_urls, 1):
                print(f"[별점순 {i}/{len(star_urls)}] 진행 중...", end='\r')
                data = crawler.crawl_detail(url)
                if data:
                    save_one_row(conn, cursor, data)
                time.sleep(random.uniform(0.8, 1.5))

        except Exception as e:
            print(f"❌ [별점순] 진행 중 오류 발생: {e}")
            traceback.print_exc()

    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 치명적 오류 발생: {e}")
    finally:
        crawler.close_driver()
        if conn and conn.is_connected():
            conn.close()
            print("\n🎉 [완결 웹툰] 모든 작업이 종료되었습니다.")

if __name__ == "__main__":
    main()