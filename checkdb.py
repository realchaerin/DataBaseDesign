import pymysql
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv
import bcrypt
import random

# 환경 변수 로드
## 지현
load_dotenv(dotenv_path="C:\\Users\\you0m\\Desktop\\movie\\env_example.env")
## 채린
# load_dotenv()

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
    """
    영화와 장르 데이터를 MOVIE 및 movie_genre 테이블에 저장
    """
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
                movie_id = result['movie_id']
                genres = tmdb_data.get('genres', [])
                insert_movie_genres(movie_id, genres)  # 장르 업데이트
                return movie_id

            # 영화 데이터 삽입
            sql_insert = """
            INSERT INTO MOVIE (movie_name, tmdb_id, original_title, release_date, runtime, overview, director, cast, production_company)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql_insert, (
                tmdb_data.get('title', 'N/A'),
                tmdb_id,
                tmdb_data.get('original_title', 'N/A'),
                tmdb_data.get('release_date', '0000-00-00'),
                tmdb_data.get('runtime', 0),
                tmdb_data.get('overview', 'N/A'),
                ', '.join([crew['name'] for crew in tmdb_credits.get('crew', []) if crew['job'] == 'Director']),
                ', '.join([cast['name'] for cast in tmdb_credits.get('cast', [])[:5]]),
                ', '.join([company['name'] for company in tmdb_data.get('production_companies', [])])
            ))
            movie_id = cur.lastrowid
            genres = tmdb_data.get('genres', [])
            insert_movie_genres(movie_id, genres)  # 장르 삽입
            conn.commit()
            return movie_id
    finally:
        conn.close()




def save_review(user_id, movie_id, review_text, sentiment):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # SQL 쿼리 확인
            print(f"Executing: INSERT INTO REVIEW (user_id, movie_id, review_text, sentiment) VALUES ({user_id}, {movie_id}, {review_text}, {sentiment})")
            cur.execute("""
                INSERT INTO REVIEW (user_id, movie_id, review_text, sentiment)
                VALUES (%s, %s, %s, %s)
            """, (user_id, movie_id, review_text, sentiment))
        conn.commit()  # 꼭 필요
    except Exception as e:
        print(f"Error saving review: {e}")  # 디버깅 로그
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


def recommend_movies_based_on_genre_and_overview(selected_movie_id, limit=5):
    """
    선택한 영화와 같은 장르와 유사한 overview를 가진 영화를 추천
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 선택한 영화의 장르 ID 가져오기
            cur.execute("""
                SELECT genre_id
                FROM movie_genre
                WHERE movie_id = %s
            """, (selected_movie_id,))
            genres = cur.fetchall()
            if not genres:
                return []

            # 선택한 영화의 overview 가져오기
            cur.execute("SELECT overview FROM MOVIE WHERE movie_id = %s", (selected_movie_id,))
            selected_movie = cur.fetchone()
            if not selected_movie or not selected_movie['overview']:
                return []

            genre_ids = [genre['genre_id'] for genre in genres]
            genre_placeholders = ', '.join(['%s'] * len(genre_ids))

            # 장르에 해당하는 영화 목록 가져오기
            cur.execute(f"""
                SELECT DISTINCT m.movie_id, m.movie_name, m.overview, m.tmdb_id
                FROM MOVIE m
                JOIN movie_genre mg ON m.movie_id = mg.movie_id
                WHERE mg.genre_id IN ({genre_placeholders}) AND m.movie_id != %s
            """, (*genre_ids, selected_movie_id))
            movies = cur.fetchall()
            if not movies:
                return []

            # TF-IDF 계산
            overviews = [movie['overview'] for movie in movies]
            tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = tfidf_vectorizer.fit_transform(overviews)

            # 선택한 영화의 TF-IDF 계산
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
        
        
def insert_movie_genres(movie_id, genres):
    """영화와 관련된 장르를 movie_genre 테이블에 삽입"""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return
    try:
        with conn.cursor() as cur:
            # 여러 개의 장르를 일괄 삽입
            sql = """
            INSERT INTO movie_genre (movie_id, genre_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE movie_id = movie_id
            """
            values = [(movie_id, genre['id']) for genre in genres]
            cur.executemany(sql, values)  # 일괄 처리
            conn.commit()  # 명시적으로 커밋
            print(f"Inserted genres for movie_id {movie_id}: {[genre['id'] for genre in genres]}")
    except pymysql.MySQLError as e:
        print(f"Error inserting genres for movie_id {movie_id}: {e}")
        conn.rollback()  # 오류 발생 시 롤백
    finally:
        conn.close()