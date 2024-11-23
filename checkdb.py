import pymysql
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME') 

def get_db_connection():
    """MySQL 데이터베이스에 연결"""
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

def get_genre_by_movie(movie_id):
    """주어진 영화 ID의 장르 ID를 가져옴"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = "SELECT genre_id FROM MOVIE WHERE movie_id = %s"
            cur.execute(sql, (movie_id,))
            result = cur.fetchone()
            if result:
                return result['genre_id']
            return None
    finally:
        conn.close()

def get_movies_by_genre(genre_id, exclude_movie_id, limit=5):
    """주어진 장르 ID로 같은 장르의 영화 5개를 랜덤으로 추천"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
            SELECT movie_id, movie_name 
            FROM MOVIE 
            WHERE genre_id = %s AND movie_id != %s
            ORDER BY RAND()
            LIMIT %s
            """
            cur.execute(sql, (genre_id, exclude_movie_id, limit))
            results = cur.fetchall()
            return [row['movie_name'] for row in results]
    finally:
        conn.close()

def save_review(user_id, movie_id, review_text, sentiment):
    """사용자의 리뷰를 데이터베이스에 저장"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO REVIEW (user_id, movie_id, review_text, sentiment)
            VALUES (%s, %s, %s, %s)
            """
            cur.execute(sql, (user_id, movie_id, review_text, sentiment))
            conn.commit()
    finally:
        conn.close()

def create_user(username, password, name):
    """새로운 사용자를 생성하고 비밀번호를 해싱하여 저장"""
    import bcrypt
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = """
            INSERT INTO USER (username, password, name)
            VALUES (%s, %s, %s)
            """
            cur.execute(sql, (username, hashed_pw, name))
            conn.commit()
    finally:
        conn.close()

def verify_user(username, password):
    """사용자 이름과 비밀번호를 검증"""
    import bcrypt
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = "SELECT user_id, password FROM USER WHERE username = %s"
            cur.execute(sql, (username,))
            user = cur.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return user['user_id']
            return None
    finally:
        conn.close()

def insert_movie(movie_data, tmdb_data=None, tmdb_credits=None):
    """영화 데이터를 MOVIE 테이블에 삽입합니다."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 장르 매핑
            genre_names = []
            if tmdb_data and 'genres' in tmdb_data:
                genre_names = [genre['name'] for genre in tmdb_data['genres']]
            
            # GENRE 테이블에서 genre_id 찾기 (여러 장르가 있을 수 있으므로 첫 번째 장르 사용)
            genre_id = None
            if genre_names:
                first_genre = genre_names[0]
                sql_genre = "SELECT genre_id FROM GENRE WHERE genre_name = %s"
                cur.execute(sql_genre, (first_genre,))
                genre_result = cur.fetchone()
                if genre_result:
                    genre_id = genre_result['genre_id']
                else:
                    # GENRE 테이블에 장르가 없으면 추가
                    sql_insert_genre = "INSERT INTO GENRE (genre_id, genre_name) VALUES (%s, %s)"
                    # 간단하게 첫 세 글자로 genre_id 생성
                    new_genre_id = first_genre[:3].upper()
                    cur.execute(sql_insert_genre, (new_genre_id, first_genre))
                    genre_id = new_genre_id
            
            # 감독 및 배우 정보 파싱
            if tmdb_credits:
                directors = [crew['name'] for crew in tmdb_credits.get('crew', []) if crew['job'] == 'Director']
                director = ', '.join(directors) if directors else 'N/A'
                
                cast = [cast_member['name'] for cast_member in tmdb_credits.get('cast', [])[:5]]  # 상위 5명
                cast_str = ', '.join(cast) if cast else 'N/A'
            else:
                director = 'N/A'
                cast_str = 'N/A'
    
            # 제작사 정보 파싱
            if tmdb_data:
                production_companies = [company['name'] for company in tmdb_data.get('production_companies', [])]
                production_company = ', '.join(production_companies) if production_companies else 'N/A'
            else:
                production_company = 'N/A'
    
            # MOVIE 테이블에 삽입 또는 업데이트
            sql = """
            INSERT INTO MOVIE (movie_name, genre_id, tmdb_id, original_title, release_date, runtime, overview, director, cast, production_company)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                tmdb_id = VALUES(tmdb_id),
                original_title = VALUES(original_title),
                release_date = VALUES(release_date),
                runtime = VALUES(runtime),
                overview = VALUES(overview),
                director = VALUES(director),
                cast = VALUES(cast),
                production_company = VALUES(production_company)
            """
            cur.execute(sql, (
                tmdb_data.get('title') if tmdb_data else 'N/A',
                genre_id,
                tmdb_data.get('id') if tmdb_data else None,
                tmdb_data.get('original_title') if tmdb_data else None,
                tmdb_data.get('release_date') if tmdb_data else None,
                tmdb_data.get('runtime') if tmdb_data else None,
                tmdb_data.get('overview') if tmdb_data else None,
                director,
                cast_str,
                production_company
            ))
            conn.commit()
    finally:
        conn.close()
