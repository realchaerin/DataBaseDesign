import streamlit as st
from checkdb import (
    get_genre_by_movie,
    get_movies_by_genre,
    save_review,
    create_user,
    verify_user,
    insert_movie
)
import sys
import os
import pymysql
from dotenv import load_dotenv
from lstm_model import predict_sentiment

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

# api_fetch에서 함수 가져오기
sys.path.append(os.path.abspath("C:/Users/you0m/Desktop/movie/utils"))  # utils 경로 추가
from api_fetch import (
    search_tmdb_movie,
    get_tmdb_movie_details,
    get_tmdb_movie_credits
)
# CSS 적용
st.markdown("""
<style>
.title {
    color: #B22222;  /* 어두운 빨간색으로 설정 */
    text-align: center;
}

.stButton > button {
    background-color: #B22222;
    color: white;
    border-radius: 5px;
    padding: 10px 20px;
}

.stTextInput, .stTextArea {
    background-color: #f4f4f4;
    color: #333;
    border-radius: 5px;
    border: 1px solid #ccc;
}

/* 내 리뷰 보기 버튼 오른쪽 상단 배치 */
.reviews-button {
    position: fixed;
    top: 10px;
    right: 10px;
    background-color: #B22222;
    color: white;
    padding: 10px 15px;
    border-radius: 5px;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# 페이지 제목과 부제목
st.markdown('<h1 class="title">무비뭐봐🎬</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center;">리뷰 기반 영화 추천 시스템</p>', unsafe_allow_html=True)

# 세션 상태 관리
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

# 로그인 화면
if not st.session_state.logged_in:
    if st.session_state.show_signup:
        # 회원가입 화면
        st.header('회원가입')

        new_username = st.text_input('새 사용자 이름', key='new_username')
        new_password = st.text_input('새 비밀번호', type='password', key='new_password')
        name = st.text_input('이름', key='new_name')

        if st.button('회원가입 하기'):
            if new_username and new_password and name:
                try:
                    create_user(new_username, new_password, name)
                    st.success("회원가입이 완료되었습니다.")
                    # 회원가입 완료 후 로그인 화면으로 전환
                    st.session_state.show_signup = False
                except pymysql.MySQLError as e:
                    st.error(f"회원가입 오류")
            else:
                st.error("모든 필드를 입력해주세요.")

        if st.button('이미 계정이 있나요? 로그인'):
            # 로그인 화면으로 돌아가기
            st.session_state.show_signup = False
    else:
        # 로그인 화면
        st.header('로그인')

        username = st.text_input('사용자 이름')
        password = st.text_input('비밀번호', type='password')

        if st.button('로그인'):
            if username and password:
                user_id = verify_user(username, password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.success(f"{username}님 환영합니다!")
                else:
                    st.error("사용자 이름 또는 비밀번호가 올바르지 않습니다.")
            else:
                st.error("모든 필드를 입력해주세요.")
        
        if st.button('회원가입'):
            # 회원가입 화면으로 전환
            st.session_state.show_signup = True

else:
    # 로그인 후에만 표시되는 영화 검색 기능
    st.header('영화 검색 및 선택')

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
            cur.execute("SELECT movie_id, movie_name, tmdb_id FROM MOVIE")
            movies = cur.fetchall()
            if not movies:
                st.warning("저장된 영화가 없습니다. 영화를 검색하여 추가해주세요.")
            
            movie_dict = {f"{movie['movie_name']} (TMDB ID: {movie['tmdb_id']})": movie['movie_id'] for movie in movies}
            selected_movie_display = st.selectbox('영화를 선택하세요', list(movie_dict.keys()))
            selected_movie_id = movie_dict[selected_movie_display]
            
            cur.execute("SELECT tmdb_id FROM MOVIE WHERE movie_id = %s", (selected_movie_id,))
            tmdb_id_result = cur.fetchone()
            if tmdb_id_result and tmdb_id_result['tmdb_id']:
                tmdb_id = tmdb_id_result['tmdb_id']
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
            else:
                st.warning("선택한 영화의 TMDB ID가 없습니다.")
                
            review_text = st.text_area('리뷰를 작성하세요')
            if st.button('리뷰 제출 및 추천 받기'):
                if review_text:
                    sentiment = predict_sentiment(review_text)
                    save_review(st.session_state.user_id, selected_movie_id, review_text, sentiment)
                    st.success(f"리뷰가 저장되었습니다. 감정: {sentiment}")
                else:
                    st.error("리뷰를 작성해주세요.")
    except pymysql.MySQLError as e:
        st.error(f"데이터베이스 오류: {e}")
    finally:
        conn.close()