import streamlit as st
from lstm_model import predict_sentiment
from checkdb import (
    get_genre_by_movie,
    get_movies_by_genre,
    save_review,
    create_user,
    verify_user,
    insert_movie
)
from utils.api_fetch import (
    search_tmdb_movie,
    get_tmdb_movie_details,
    get_tmdb_movie_credits
)
import pymysql
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Streamlit 페이지 설정
st.set_page_config(
    page_title="무비뭐바",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 적용 (선택 사항)
st.markdown("""
<style>
.title {
    color: #1f77b4;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">리뷰 기반 영화 추천 시스템</h1>', unsafe_allow_html=True)

# 사용자 로그인
st.header('로그인')

username = st.text_input('사용자 이름')
password = st.text_input('비밀번호', type='password')

if st.button('로그인'):
    if username and password:
        user_id = verify_user(username, password)
        if user_id:
            st.success(f"{username}님 환영합니다!")
            
            # 영화 선택 및 리뷰 작성
            st.header('영화 선택 및 리뷰 작성')
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            try:
                with conn.cursor() as cur:
                    # 모든 영화 목록 가져오기
                    cur.execute("SELECT movie_id, movie_name, tmdb_id FROM MOVIE")
                    movies = cur.fetchall()
                    if not movies:
                        st.warning("저장된 영화가 없습니다. 영화를 검색하여 추가해주세요.")
                    
                    movie_dict = {f"{movie['movie_name']} (TMDB ID: {movie['tmdb_id']})": movie['movie_id'] for movie in movies}
                    selected_movie_display = st.selectbox('영화를 선택하세요', list(movie_dict.keys()))
                    selected_movie_id = movie_dict[selected_movie_display]
                    
                    # 선택한 영화의 TMDB ID 가져오기
                    cur.execute("SELECT tmdb_id FROM MOVIE WHERE movie_id = %s", (selected_movie_id,))
                    tmdb_id_result = cur.fetchone()
                    if tmdb_id_result and tmdb_id_result['tmdb_id']:
                        tmdb_id = tmdb_id_result['tmdb_id']
                        # TMDB API를 통해 영화 상세 정보 가져오기
                        tmdb_movie_details = get_tmdb_movie_details(tmdb_id)
                        tmdb_movie_credits = get_tmdb_movie_credits(tmdb_id)
                        if tmdb_movie_details:
                            st.subheader("TMDB 영화 상세 정보")
                            st.write(f"**영화명:** {tmdb_movie_details.get('title', 'N/A')}")
                            st.write(f"**영화명(영문):** {tmdb_movie_details.get('original_title', 'N/A')}")
                            st.write(f"**개봉일:** {tmdb_movie_details.get('release_date', 'N/A')}")
                            st.write(f"**상영시간:** {tmdb_movie_details.get('runtime', 'N/A')} 분")
                            st.write(f"**개요:** {tmdb_movie_details.get('overview', 'N/A')}")
                            st.write(f"**제작사:** {', '.join([company['name'] for company in tmdb_movie_details.get('production_companies', [])])}")
                            st.write(f"**감독:** {', '.join([crew['name'] for crew in tmdb_movie_credits.get('crew', []) if crew['job'] == 'Director'])}")
                            st.write(f"**배우:** {', '.join([cast['name'] for cast in tmdb_movie_credits.get('cast', [])[:5]])}")  # 상위 5명

                            # MOVIE 테이블에 TMDB 데이터 삽입 (이미 저장된 데이터이므로 업데이트)
                            insert_movie(None, tmdb_movie_details, tmdb_movie_credits)
                    else:
                        st.warning("선택한 영화의 TMDB ID가 없습니다.")
            
                review_text = st.text_area('리뷰를 작성하세요')

                if st.button('리뷰 제출 및 추천 받기'):
                    if review_text:
                        # 리뷰 감정 분석
                        sentiment = predict_sentiment(review_text)

                        # 리뷰 저장
                        save_review(user_id, selected_movie_id, review_text, sentiment)

                        st.success(f"리뷰가 저장되었습니다. 감정: {sentiment}")

                        # 추천 로직
                        if sentiment == 'positive':
                            # 선택한 영화의 장르 ID 가져오기
                            genre_id = get_genre_by_movie(selected_movie_id)
                            if genre_id:
                                # 같은 장르의 영화 5개 추천
                                recommendations = get_movies_by_genre(genre_id, selected_movie_id, limit=5)
                                st.subheader('추천 영화')
                                if recommendations:
                                    for rec in recommendations:
                                        st.write(f"- {rec}")
                                else:
                                    st.info("추천할 영화가 더 이상 없습니다.")
                            else:
                                st.warning("장르 정보를 찾을 수 없습니다.")
                        else:
                            st.info("부정적인 리뷰이므로 추천하지 않습니다.")
                    else:
                        st.error("리뷰를 작성해주세요.")
            except pymysql.MySQLError as e:
                st.error(f"데이터베이스 오류: {e}")
            finally:
                conn.close()
        else:
            st.error("사용자 이름 또는 비밀번호가 올바르지 않습니다.")
    else:
        st.error("모든 필드를 입력해주세요.")

# 사용자 회원가입
st.header('회원가입')

new_username = st.text_input('새 사용자 이름', key='new_username')
new_password = st.text_input('새 비밀번호', type='password', key='new_password')
name = st.text_input('이름', key='new_name')

if st.button('회원가입'):
    if new_username and new_password and name:
        try:
            create_user(new_username, new_password, name)
            st.success("회원가입이 완료되었습니다.")
        except pymysql.MySQLError as e:
            st.error(f"회원가입 오류: {e}")
    else:
        st.error("모든 필드를 입력해주세요.")

# 영화 추가 섹션 (선택 사항)
st.header('영화 추가하기')

movie_search_query = st.text_input('영화명을 입력하세요')

if st.button('영화 검색 및 추가'):
    if movie_search_query:
        search_results = search_tmdb_movie(movie_search_query)
        if search_results and search_results.get('results'):
            first_result = search_results['results'][0]
            tmdb_id = first_result['id']
            tmdb_movie_details = get_tmdb_movie_details(tmdb_id)
            tmdb_movie_credits = get_tmdb_movie_credits(tmdb_id)
            if tmdb_movie_details:
                st.subheader("TMDB 영화 상세 정보")
                st.write(f"**영화명:** {tmdb_movie_details.get('title', 'N/A')}")
                st.write(f"**영화명(영문):** {tmdb_movie_details.get('original_title', 'N/A')}")
                st.write(f"**개봉일:** {tmdb_movie_details.get('release_date', 'N/A')}")
                st.write(f"**상영시간:** {tmdb_movie_details.get('runtime', 'N/A')} 분")
                st.write(f"**개요:** {tmdb_movie_details.get('overview', 'N/A')}")
                st.write(f"**제작사:** {', '.join([company['name'] for company in tmdb_movie_details.get('production_companies', [])])}")
                st.write(f"**감독:** {', '.join([crew['name'] for crew in tmdb_movie_credits.get('crew', []) if crew['job'] == 'Director'])}")
                st.write(f"**배우:** {', '.join([cast['name'] for cast in tmdb_movie_credits.get('cast', [])[:5]])}")  # 상위 5명

                # MOVIE 테이블에 TMDB 데이터 삽입
                insert_movie(None, tmdb_movie_details, tmdb_movie_credits)
                st.success("영화가 성공적으로 추가되었습니다.")
        else:
            st.warning("검색 결과가 없습니다. 다른 영화명을 시도해보세요.")
    else:
        st.error("영화명을 입력해주세요.")
