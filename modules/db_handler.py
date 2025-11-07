import mysql.connector
from mysql.connector import Error as MySQLError
import csv
import os
from config import FAILED_CSV

def connect_database(config):
    
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print("✅ 데이터베이스 연결 성공")

            return conn
        
    except MySQLError as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")

    return None

def normalize_age(age_text: str) -> str:

    t = (age_text or "").replace(" ", "").strip()

    if t in ('전체연령가', '전체이용가', '전체'): return '전체연령가'
    if '12' in t: return '12세 이용가'
    if '15' in t: return '15세 이용가'
    if any(x in t for x in ['18', '19', '청불', '성인']): return '18세 이용가'

    return '전체연령가'


def backup_failed_row(row, err_msg):
   
    file_exists = os.path.isfile(FAILED_CSV)
    with open(FAILED_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["platform", "works_name", "error_msg", "data_dump"])
        writer.writerow([row.get('platform'), row.get('works_name'), err_msg, str(row)])

def save_one_row(connection, cursor, data):
    
    INSERT_SQL = """
    INSERT INTO works
    (platform, works_name, artist_name, age_classification, description, genre, thumbnail_url, `type`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      artist_name = VALUES(artist_name),
      age_classification = VALUES(age_classification),
      description = VALUES(description),
      genre = VALUES(genre),
      thumbnail_url = VALUES(thumbnail_url),
      `type` = VALUES(`type`)
    """
    

    db_age = normalize_age(data.get('age_classification'))
    db_genre = data.get('genre').strip().lstrip('#')

    vals = (
        data.get('platform'), data.get('works_name'), data.get('artist_name'),
        db_age, data.get('description'), db_genre, data.get('thumbnail_url'), data.get('type')
    )

    try:
        cursor.execute(INSERT_SQL, vals)
        connection.commit()
        print(f"✅ [DB 저장] {data.get('works_name')}")
        return True
    
    except Exception as e:
        print(f"❌ [DB 에러] {data.get('works_name')} -> {e}")
        connection.rollback()
        backup_failed_row(data, str(e))
        return False