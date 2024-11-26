import pymysql
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv
import bcrypt
import random

# 환경 변수 로드
load_dotenv(dotenv_path="C:\\Users\\you0m\\Desktop\\movie\\env_example.env")

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
                    movie_data['genre_id'],  # 장르 ID 저장
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
    """영화와 장르 데이터를 MOVIE 테이블에 저장"""
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
                return result['movie_id']

            # TMDB 데이터에서 장르 ID 가져오기
            genres = tmdb_data.get('genres', [])
            genre_id = genres[0]['id'] if genres else 'UNKNOWN'

            # 영화 데이터 삽입
            movie_name = tmdb_data.get('title', 'N/A')
            original_title = tmdb_data.get('original_title', 'N/A')
            release_date = tmdb_data.get('release_date', '0000-00-00')
            runtime = tmdb_data.get('runtime', 0)
            overview = tmdb_data.get('overview', 'N/A')
            director = ', '.join([crew['name'] for crew in tmdb_credits.get('crew', []) if crew['job'] == 'Director']) if tmdb_credits else 'N/A'
            cast = ', '.join([cast['name'] for cast in tmdb_credits.get('cast', [])[:5]]) if tmdb_credits else 'N/A'
            production_company = ', '.join([company['name'] for company in tmdb_data.get('production_companies', [])]) if tmdb_data else 'N/A'

            sql_insert = """
            INSERT INTO MOVIE (movie_name, genre_id, tmdb_id, original_title, release_date, runtime, overview, director, cast, production_company)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql_insert, (
                movie_name,
                genre_id,  # 장르 ID 저장
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
            print(f"Inserted movie: {movie_name}")
            return cur.lastrowid
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
    try:
        with conn.cursor() as cur:
            # user_id가 이미 존재하는지 확인
            check_sql = "SELECT user_id FROM USER WHERE user_id = %s"
            cur.execute(check_sql, (user_id,))
            existing_user = cur.fetchone()
            if existing_user:
                raise ValueError("이미 존재하는 사용자 아이디입니다.")

            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = """
            INSERT INTO USER (user_id, password, username)
            VALUES (%s, %s, %s)
            """
            cur.execute(sql, (user_id, hashed_pw, username))
            conn.commit()
            print(f"Created new user: {user_id}")
    except Exception as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        raise e  # 오류가 발생하면 다시 예외를 던짐
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


def recommend_movies_based_on_tfidf(selected_movie_id, limit=5):
    """선택한 영화와 같은 장르에서 TF-IDF를 기준으로 유사한 영화를 추천"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 선택한 영화의 장르 ID 가져오기
            cur.execute("SELECT genre_id FROM MOVIE WHERE movie_id = %s", (selected_movie_id,))
            genre_result = cur.fetchone()
            if not genre_result:
                return []
            genre_id = genre_result['genre_id']

            # 같은 장르의 영화 가져오기
            cur.execute("""
                SELECT movie_id, movie_name, overview, tmdb_id
                FROM MOVIE
                WHERE genre_id = %s AND movie_id != %s
            """, (genre_id, selected_movie_id))
            movies = cur.fetchall()

            if not movies:
                return []

            # TF-IDF 계산
            overviews = [movie['overview'] for movie in movies]
            tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = tfidf_vectorizer.fit_transform(overviews)

            # 선택한 영화의 overview 가져오기
            cur.execute("SELECT overview FROM MOVIE WHERE movie_id = %s", (selected_movie_id,))
            selected_movie = cur.fetchone()
            if not selected_movie or not selected_movie['overview']:
                return []

            selected_tfidf = tfidf_vectorizer.transform([selected_movie['overview']])
            cosine_sim = cosine_similarity(selected_tfidf, tfidf_matrix).flatten()

            # 유사도 기준 정렬
            similarity_scores = list(enumerate(cosine_sim))
            similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

            # 가장 유사한 영화 추천
            recommended_movies = []
            for idx, score in similarity_scores[:limit]:
                recommended_movies.append(movies[idx]) 
            return recommended_movies
    finally:
        conn.close()

def recommend_random_movies(limit=5):
    """영화 목록에서 평점 높은 영화 중 랜덤으로 5개를 추천"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 평점이 높은 영화 중 5개를 랜덤으로 추천
            cur.execute("""
                SELECT movie_id, movie_name, tmdb_id
                FROM movie_list
                ORDER BY RAND()
                LIMIT %s
            """, (limit,))
            movies = cur.fetchall()
            return movies
    finally:
        conn.close()