import mysql.connector
from mysql.connector import Error as MySQLError
import csv
import os
from config import FAILED_CSV

# 장르 우선순위
GENRE_PRIORITY = {
    '로판': 5,
    '무협/사극': 1,
    '판타지': 1,
    '액션': 1,
    '드라마': 1,
    '로맨스': 1,
    '일상': 1,
    '개그': 1,
    '스릴러': 1,
}

def connect_database(config):
    
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print("✅ 데이터베이스 연결 성공")

            return conn
        
    except MySQLError as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")

    return None

def parse_artists(artist_name_raw):

    author, illustrator, original_author = None, None, None
    
    if not artist_name_raw:
        return None, None, None

    # 정규화
    text = artist_name_raw.replace('∙', ' ').replace(':', ' ')
    text = text.replace('글/그림', '글 그림').replace('글/원작', '글 원작')

    parts = [p.strip() for p in text.split('/') if p.strip()]

    for part in parts:
        part = part.strip()
        if not part: continue

        has_author = '글' in part or '각색' in part
        has_illustrator = '그림' in part
        has_original = '원작' in part
        
        # 이름만 추출
        name = part.replace('원작', '').replace('글', '').replace('각색', '').replace('그림', '').strip()

        if not name:
            continue

        if not has_author and not has_illustrator and not has_original:
            if not author:
                author = name
            elif not illustrator:
                illustrator = name
        
        if has_author: author = name
        if has_illustrator: illustrator = name
        if has_original: original_author = name

    if len(parts) == 1 and author and not illustrator and not original_author:
        illustrator = author

    return author, illustrator, original_author


def normalize_data(data):

    # 장르 
    genre = data.get('genre', '').strip().lstrip('#')
    genre = genre.replace('무협 / 사극', '무협/사극')
    
    # 연령
    age_raw = data.get('age_classification', '').replace(' ', '')
    if any(x in age_raw for x in ['18', '19', '청불']): age = '18세 이용가'
    elif '15' in age_raw: age = '15세 이용가'
    elif '12' in age_raw: age = '12세 이용가'
    else: age = '전체연령가'

    # 작가
    author, illustrator, original_author = parse_artists(data.get('artist_name', ''))

    # 해시태그
    hashtag_list = data.get('hashtags', [])
    hashtag_string = ",".join(tag for tag in hashtag_list if tag)

    return {
        **data,
        'genre': genre,
        'age_classification': age,
        'author': author,
        'illustrator': illustrator,
        'original_author': original_author,
        'priority': GENRE_PRIORITY.get(genre, 0),
        'hashtag_string': hashtag_string
    }


def save_one_row(connection, cursor, raw_data):
    
    data = normalize_data(raw_data)
    
    INSERT_SQL = """
    INSERT INTO works
    (platform, works_name, artist_name, author, illustrator, original_author, 
     age_classification, description, genre, hashtag, thumbnail_url, `type`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        artist_name = VALUES(artist_name),
        author = VALUES(author),
        illustrator = VALUES(illustrator),
        original_author = VALUES(original_author),
        age_classification = VALUES(age_classification),
        hashtag = VALUES(hashtag),
        description = VALUES(description),
        thumbnail_url = VALUES(thumbnail_url),
        `type` = VALUES(`type`),
        genre = CASE 
            WHEN %s >= (
                SELECT CASE genre
                    WHEN '로판' THEN 10
                    WHEN '판타지' THEN 1
                    WHEN '무협/사극' THEN 1
                    WHEN '로맨스' THEN 1
                    WHEN '일상' THEN 1
                    WHEN '개그' THEN 1
                    WHEN '스릴러' THEN 1
                    ELSE 0
                END
            ) THEN VALUES(genre)
            ELSE genre
        END
    """
    vals = (
        data['platform'], data['works_name'], data['artist_name'],
        data['author'], data['illustrator'], data['original_author'],
        data['age_classification'], data['description'], data['genre'],
        data['hashtag_string'],
        data['thumbnail_url'], data['type'],
        data['priority']
    )

    try:
        cursor.execute(INSERT_SQL, vals)
        connection.commit()
        
        if cursor.rowcount == 1:
            print(f"  ✅ [신규] {data['works_name']}")
        elif cursor.rowcount == 2:
            print(f"  🔄 [업데이트] {data['works_name']}")
        else:
            print(f"  ➖ [변경없음] {data['works_name']}")
        return True
    
    except Exception as e:
        print(f"❌ [DB 에러] {data.get('works_name')} -> {e}")
        connection.rollback()
        backup_failed_row(data, str(e))
        return False
    

def backup_failed_row(data, err_msg):
    file_exists = os.path.isfile(FAILED_CSV)
    with open(FAILED_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["works_name", "error", "data_dump"])
        writer.writerow([data.get('works_name'), err_msg, str(data)])