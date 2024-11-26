import pymysql
import os
from dotenv import load_dotenv
import bcrypt

# 환경 변수 로드
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')


def get_db_connection():
    """
    MySQL 데이터베이스에 연결합니다.
    """
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to the database: {e}")
        return None


def insert_movie_list(movie_data):
    """영화 데이터를 movie_list 테이블에 삽입합니다."""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return
    try:
        with conn.cursor() as cur:
            # **변경 사항: 실제 genre_id를 사용하도록 수정**
            sql = """
            INSERT INTO movie_list (movie_name, genre_id, tmdb_id, original_title, release_date, runtime, overview, director, cast, production_company)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                movie_name = VALUES(movie_name),
                genre_id = VALUES(genre_id),
                original_title = VALUES(original_title),
                release_date = VALUES(release_date),
                runtime = VALUES(runtime),
                overview = VALUES(overview),
                director = VALUES(director),
                cast = VALUES(cast),
                production_company = VALUES(production_company)
            """
            try:
                cur.execute(sql, (
                    movie_data['title'],
                    movie_data['genre_id'],
                    movie_data['tmdb_id'],
                    movie_data['original_title'],
                    movie_data['release_date'],
                    movie_data['runtime'],
                    movie_data['overview'],
                    movie_data['director'],
                    movie_data['cast'],
                    movie_data['production_company']
                ))
                conn.commit()
                print(f"Inserted/Updated movie in movie_list: {movie_data['title']}")
            except pymysql.MySQLError as e:
                print(f"Error inserting movie '{movie_data['title']}' into movie_list: {e}")
    finally:
        conn.close()


def insert_movie_if_not_exists(tmdb_data=None, tmdb_credits=None):
    """영화가 존재하지 않을 경우 MOVIE 테이블에 삽입합니다."""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return
    try:
        with conn.cursor() as cur:
            # 영화가 이미 존재하는지 확인
            tmdb_id = tmdb_data.get('id')
            if not tmdb_id:
                print("TMDB ID가 없습니다.")
                return None

            sql_check = "SELECT movie_id FROM MOVIE WHERE tmdb_id = %s"
            cur.execute(sql_check, (tmdb_id,))
            result = cur.fetchone()
            if result:
                # 영화가 이미 존재하면 아무 작업도 수행하지 않음
                return result['movie_id']

            # 영화가 존재하지 않을 경우 삽입
            genre_names = [genre['name'] for genre in tmdb_data['genres']] if tmdb_data and 'genres' in tmdb_data else []

            # GENRE 테이블에서 genre_id 찾기
            genre_id = 'UNKNOWN'
            if genre_names:
                first_genre = genre_names[0]
                sql_genre = "SELECT genre_id FROM GENRE WHERE genre_name = %s"
                cur.execute(sql_genre, (first_genre,))
                genre_result = cur.fetchone()
                if genre_result:
                    genre_id = genre_result['genre_id']
                else:
                    # 장르 추가
                    new_genre_id = first_genre[:3].upper()  # 장르 ID를 첫 세 글자로 생성
                    try:
                        sql_insert_genre = "INSERT INTO GENRE (genre_id, genre_name) VALUES (%s, %s)"
                        cur.execute(sql_insert_genre, (new_genre_id, first_genre))
                        genre_id = new_genre_id
                        print(f"Inserted new genre: {first_genre} with ID {new_genre_id}")
                    except pymysql.MySQLError as e:
                        print(f"Error inserting new genre '{first_genre}': {e}")
                        genre_id = 'UNKNOWN'  # 장르 삽입 실패 시 'UNKNOWN'으로 설정

            # 영화 삽입, 기본값 추가
            movie_name = tmdb_data.get('title', 'N/A')
            original_title = tmdb_data.get('original_title', 'N/A')
            release_date = tmdb_data.get('release_date', '0000-00-00')  # 기본값 설정
            runtime = tmdb_data.get('runtime', 0)
            overview = tmdb_data.get('overview', 'N/A')
            director = ', '.join([crew['name'] for crew in tmdb_credits.get('crew', []) if crew['job'] == 'Director']) if tmdb_credits else 'N/A'
            cast = ', '.join([cast['name'] for cast in tmdb_credits.get('cast', [])[:5]]) if tmdb_credits else 'N/A'
            production_company = ', '.join([company['name'] for company in tmdb_data.get('production_companies', [])]) if tmdb_data else 'N/A'

            sql_insert = """
            INSERT INTO MOVIE (movie_name, genre_id, tmdb_id, original_title, release_date, runtime, overview, director, cast, production_company)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            try:
                cur.execute(sql_insert, (
                    movie_name,
                    genre_id,
                    tmdb_id,
                    original_title,
                    release_date,
                    runtime,
                    overview,
                    director,
                    cast,
                    production_company
                ))
                conn.commit()
                print(f"Inserted movie into MOVIE table: {movie_name}")
                return cur.lastrowid
            except pymysql.MySQLError as e:
                print(f"Error inserting movie '{movie_name}' into MOVIE table: {e}")
                return None
    finally:
        conn.close()


def save_review(user_id, movie_id, review_text, sentiment):
    """사용자의 리뷰를 데이터베이스에 저장"""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return
    try:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO REVIEW (user_id, movie_id, review_text, sentiment)
            VALUES (%s, %s, %s, %s)
            """
            try:
                cur.execute(sql, (user_id, movie_id, review_text, sentiment))
                conn.commit()
                print(f"Saved review for user {user_id} on movie ID {movie_id}")
            except pymysql.MySQLError as e:
                print(f"Error saving review: {e}")
    finally:
        conn.close()


def verify_user(user_id, password):
    """사용자 ID와 비밀번호를 검증"""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return None
    try:
        with conn.cursor() as cur:
            sql = "SELECT user_id, password FROM USER WHERE user_id = %s"
            cur.execute(sql, (user_id,))
            user = cur.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return user['user_id']
            return None
    finally:
        conn.close()


def create_user(user_id, password, username):
    """새로운 사용자를 생성하고 비밀번호를 해싱하여 저장"""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return
    try:
        with conn.cursor() as cur:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = """
            INSERT INTO USER (user_id, password, user_name)
            VALUES (%s, %s, %s)
            """
            try:
                cur.execute(sql, (user_id, hashed_pw, username))
                conn.commit()
                print(f"Created new user: {user_id}")
            except pymysql.MySQLError as e:
                print(f"Error creating user '{user_id}': {e}")
    finally:
        conn.close()


def check_review_exists(user_id, movie_id):
    """특정 사용자가 특정 영화에 대해 이미 리뷰를 작성했는지 확인"""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return False
    try:
        with conn.cursor() as cur:
            sql = "SELECT 1 FROM REVIEW WHERE user_id = %s AND movie_id = %s"
            cur.execute(sql, (user_id, movie_id))
            result = cur.fetchone()
            return result is not None
    finally:
        conn.close()


def recommend_movies_based_on_reviews(user_id, limit=5):
    """사용자의 리뷰 감정을 기반으로 영화 추천"""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return []
    try:
        with conn.cursor() as cur:
            # 리뷰 기반으로 장르 선호도 계산 (긍정 리뷰가 많은 장르 순)
            sql = """
            SELECT genre_id 
            FROM MOVIE
            JOIN REVIEW ON MOVIE.movie_id = REVIEW.movie_id
            WHERE REVIEW.user_id = %s AND REVIEW.sentiment = 'positive'
            GROUP BY genre_id
            ORDER BY COUNT(*) DESC
            LIMIT %s
            """
            cur.execute(sql, (user_id, limit))
            results = cur.fetchall()
            genre_ids = [row['genre_id'] for row in results]

            if not genre_ids:
                print("사용자의 긍정 리뷰에 기반한 장르가 없습니다.")
                return []

            # movie_list에서 동일한 장르의 영화 추천
            recommended_movies = []
            for genre_id in genre_ids:
                cur.execute("""
                    SELECT movie_name 
                    FROM movie_list 
                    WHERE genre_id = %s
                    ORDER BY RAND()
                    LIMIT 3
                """, (genre_id,))
                fetched = cur.fetchall()
                recommended_movies += [row['movie_name'] for row in fetched]
            return recommended_movies
    finally:
        conn.close()
