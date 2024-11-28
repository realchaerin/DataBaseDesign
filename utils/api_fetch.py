import sys
import os
import requests
from dotenv import load_dotenv

# 상위 디렉토리를 PYTHONPATH에 추가
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

try:
    from checkdb import insert_movie_list  # movie_list 테이블에 삽입하는 함수만 import
    print("checkdb 모듈을 성공적으로 임포트했습니다.")
except ModuleNotFoundError as e:
    print("모듈 임포트 오류:", e)
    sys.exit(1)  # 스크립트 종료

# 환경 변수 로드
## 지현
# load_dotenv(dotenv_path="C:\\Users\\you0m\\Desktop\\movie\\env_example.env")
## 채린
load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def search_tmdb_movie(query, response_format='json'):
    if response_format != 'json':
        raise ValueError("TMDB API는 'json' 형식만 지원합니다.")
    
    endpoint = f"{TMDB_BASE_URL}/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'ko-KR'  # 기본적으로 한국어 데이터 요청
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB API 요청 중 오류 발생: {e}")
        return None

def get_tmdb_movie_details(tmdb_id):
    # 기본 영화 세부 정보 (한국어)
    endpoint = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ko-KR'  # 한국어 데이터 요청
    }
    
    try:
        # 기본 영화 정보 요청
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        movie_details = response.json()

        return movie_details
    except requests.exceptions.RequestException as e:
        print(f"TMDB API 요청 중 오류 발생: {e}")
        return None

def get_tmdb_movie_credits(tmdb_id):
    """TMDB API를 통해 영화의 출연진 및 제작진 정보를 가져옵니다."""
    endpoint = f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ko-KR'  # 한국어로 데이터를 요청
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB API 요청 중 오류 발생: {e}")
        return None
    
def get_tmdb_movie_details_with_genres(tmdb_id):
    """
    TMDB API에서 영화 세부 정보와 장르 정보를 가져옵니다.
    """
    movie_details = get_tmdb_movie_details(tmdb_id)
    if movie_details:
        genres = movie_details.get('genres', [])
        return movie_details, genres
    return None, None