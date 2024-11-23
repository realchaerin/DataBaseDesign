import requests
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def search_tmdb_movie(query, response_format='json'):
    """
    TMDB API를 사용하여 영화 검색을 수행합니다.
    
    Parameters:
        query (str): 검색할 영화명
        response_format (str): 'json' 형식 (TMDB는 XML을 지원하지 않음)
        
    Returns:
        dict: 검색 결과 (JSON 형식)
    """
    if response_format != 'json':
        raise ValueError("TMDB API는 'json' 형식만 지원합니다.")
    
    endpoint = f"{TMDB_BASE_URL}/search/movie"
    params = {
        'api_key':'TMDB_API_KEY',
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
    """
    TMDB API를 사용하여 특정 영화의 상세 정보를 가져옴
    
    Parameters:
        tmdb_id (int): TMDB 영화 ID
        
    Returns:
        dict: 영화의 상세 정보
    """
    endpoint = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
    params = {
        'api_key': 'TMDB_API_KEY',
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
    """
    TMDB API를 사용하여 특정 영화의 크레딧 정보를 가져옴
    
    Parameters:
        tmdb_id (int): TMDB 영화 ID
        
    Returns:
        dict: 영화의 크레딧 정보
    """
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
