# db_design/utils/api_fetch.py

import sys
import os
import requests
from dotenv import load_dotenv

# 상위 디렉토리를 PYTHONPATH에 추가
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

# 디버깅을 위해 현재 작업 디렉토리와 parent_dir의 파일 목록 출력
print("현재 작업 디렉토리:", os.getcwd())
print("parent_dir:", parent_dir)
print("parent_dir의 파일 목록:", os.listdir(parent_dir))

try:
    from checkdb import insert_movie_list  # movie_list 테이블에 삽입하는 함수만 import
    print("checkdb 모듈을 성공적으로 임포트했습니다.")
except ModuleNotFoundError as e:
    print("모듈 임포트 오류:", e)
    sys.exit(1)  # 스크립트 종료

# 환경 변수 로드 (상대 경로 사용)
load_dotenv(dotenv_path="../.env")

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def search_tmdb_movie(query, response_format='json'):
    if response_format != 'json':
        raise ValueError("TMDB API는 'json' 형식만 지원합니다.")
    
    endpoint = f"{TMDB_BASE_URL}/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'ko-KR'  # 한국어 데이터 요청
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB API 요청 중 오류 발생: {e}")
        return None

def get_tmdb_movie_details(tmdb_id):
    endpoint = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ko-KR'
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB API 요청 중 오류 발생: {e}")
        return None

def get_tmdb_movie_credits(tmdb_id):
    endpoint = f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ko-KR'
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB API 요청 중 오류 발생: {e}")
        return None

def get_top_rated_movies(page=1):
    endpoint = f"{TMDB_BASE_URL}/movie/top_rated"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ko-KR',
        'page': page
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB API 요청 중 오류 발생: {e}")
        return None

def fetch_and_save_top_rated_movies():
    top_rated_movies = get_top_rated_movies(page=1)  # 기본적으로 1페이지만 가져옴
    
    if top_rated_movies and 'results' in top_rated_movies:
        for movie in top_rated_movies['results']:
            tmdb_id = movie.get('id')
            if not tmdb_id:
                print("TMDB ID가 없는 영화는 건너뜁니다.")
                continue

            tmdb_movie_details = get_tmdb_movie_details(tmdb_id)
            tmdb_movie_credits = get_tmdb_movie_credits(tmdb_id)

            if tmdb_movie_details:
                genres = tmdb_movie_details.get('genres', [])
                if not genres:
                    print(f"영화 '{tmdb_movie_details.get('title', 'N/A')}'에 장르 정보가 없습니다.")
                    primary_genre_id = 'UNKNOWN'
                else:
                    primary_genre_id = str(genres[0]['id'])  # 첫 번째 장르 사용

                movie_data = {
                    'title': tmdb_movie_details.get('title', 'N/A'),
                    'tmdb_id': tmdb_id,
                    'genre_id': primary_genre_id,
                    'original_title': tmdb_movie_details.get('original_title', 'N/A'),
                    'release_date': tmdb_movie_details.get('release_date', '0000-00-00'),
                    'runtime': tmdb_movie_details.get('runtime', 0),
                    'overview': tmdb_movie_details.get('overview', 'N/A'),
                    'director': ', '.join([crew['name'] for crew in tmdb_movie_credits.get('crew', []) if crew['job'] == 'Director']) if tmdb_movie_credits else 'N/A',
                    'cast': ', '.join([cast['name'] for cast in tmdb_movie_credits.get('cast', [])[:5]]) if tmdb_movie_credits else 'N/A',
                    'production_company': ', '.join([company['name'] for company in tmdb_movie_details.get('production_companies', [])]) if tmdb_movie_details else 'N/A'
                }

                # 삽입 전에 movie_data 출력
                print(f"Inserting movie: {movie_data['title']} with genre_id: {movie_data['genre_id']}")

                # 영화 데이터를 movie_list 테이블에 삽입
                insert_movie_list(movie_data)
            else:
                print(f"영화 상세 정보를 가져오는 데 실패했습니다: TMDB ID {tmdb_id}")
    else:
        print("TMDB API에서 영화를 가져오지 못했습니다.")

if __name__ == "__main__":
    fetch_and_save_top_rated_movies()
