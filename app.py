import streamlit as st
from checkdb import (
    save_review,
    create_user,
    verify_user,
    insert_movie,
    recommend_movies_based_on_reviews
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

st.set_page_config(
    page_title="무비뭐바",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.append(os.path.abspath("C:/Users/you0m/Desktop/movie/utils"))
from api_fetch import (
    search_tmdb_movie,
    get_tmdb_movie_details,
    get_tmdb_movie_credits
)

# CSS 적용
st.markdown("""
<style>
body {
    margin: 0px !important;
    padding: 0px !important;
}
.title {
    color: #B22222;
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
img {
    margin-top: -70px;
}
.movie-overview {
    width: 100%;
    text-align: justify;
    font-size: 1rem;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">무비뭐봐🎬</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center;">리뷰 기반 영화 추천 시스템</p>', unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

if 'selected_movie_id' not in st.session_state:
    st.session_state.selected_movie_id = None

if 'review_saved' not in st.session_state:
    st.session_state.review_saved = False

if 'username' not in st.session_state:
    st.session_state.username = None

if not st.session_state.logged_in:
    if st.session_state.show_signup:
        st.header('회원가입')

        new_user_id = st.text_input('사용자 아이디', key='new_user_id')
        new_password = st.text_input('비밀번호', type='password', key='new_password')
        username = st.text_input('이름', key='new_username')

        if st.button('회원가입 하기'):
            if new_user_id and new_password and username:
                try:
                    create_user(new_user_id, new_password, username)
                    st.success("회원가입이 완료되었습니다.")
                    st.session_state.show_signup = False
                except pymysql.MySQLError:
                    st.error("회원가입 오류")
            else:
                st.error("모든 필드를 입력해주세요.")

        if st.button('이미 계정이 있나요? 로그인'):
            st.session_state.show_signup = False
    else:
        st.header('로그인')

        user_id = st.text_input('사용자 아이디')
        password = st.text_input('비밀번호', type='password')

        if st.button('로그인'):
            if user_id and password:
                username = verify_user(user_id, password)
                if username:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.success(f"{username}님 환영합니다!")
                else:
                    st.error("사용자 이름 또는 비밀번호가 올바르지 않습니다.")
            else:
                st.error("모든 필드를 입력해주세요.")

        if st.button('회원가입'):
            st.session_state.show_signup = True

else:
    if st.session_state.review_saved:
        st.success("리뷰가 저장되었습니다.")
        sentiment = st.session_state.sentiment
        satisfaction = "Good" if sentiment == "positive" else "Bad"
        st.write(f"만족도: {satisfaction}")

        if satisfaction == "Bad":
            st.warning("만족도가 낮아 랜덤 영화를 추천합니다:")
            with pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT movie_name FROM MOVIE ORDER BY RAND() LIMIT 5;")
                    random_movies = cur.fetchall()
                    for movie in random_movies:
                        st.write(f"- {movie['movie_name']}")
        else:
            st.subheader("추천 영화")
            recommended_movies = recommend_movies_based_on_reviews(st.session_state.user_id, limit=5)
            if recommended_movies:
                with pymysql.connect(
                    host=DB_HOST,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    db=DB_NAME,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                ) as conn:
                    for movie_id in recommended_movies:
                        with conn.cursor() as cur:
                            cur.execute("SELECT movie_name FROM MOVIE WHERE movie_id = %s", (movie_id,))
                            result = cur.fetchone()
                            if result:
                                st.write(f"- {result['movie_name']}")
            else:
                st.write("추천할 영화가 없습니다.")

        if st.button("다시 영화 검색하기"):
            st.session_state.review_saved = False
            st.session_state.selected_movie_id = None
    else:
        st.header('영화 검색')

        search_query = st.text_input('영화 이름을 입력하세요')

        if st.button('검색'):
            if search_query:
                search_results = search_tmdb_movie(search_query)
                if search_results and 'results' in search_results and len(search_results['results']) > 0:
                    movie_data = search_results['results'][0]
                    tmdb_id = movie_data['id']
                    
                    tmdb_movie_details = get_tmdb_movie_details(tmdb_id)
                    tmdb_movie_credits = get_tmdb_movie_credits(tmdb_id)

                    if tmdb_movie_details:
                        st.subheader("TMDB 영화 상세 정보")

                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**영화명:** {tmdb_movie_details.get('title', 'N/A')}")
                            st.write(f"**영화명(영문):** {tmdb_movie_details.get('original_title', 'N/A')}")
                            st.write(f"**개봉일:** {tmdb_movie_details.get('release_date', 'N/A')}")
                            st.write(f"**상영시간:** {tmdb_movie_details.get('runtime', 'N/A')} 분")
                        st.markdown(f"<div class='movie-overview'>{tmdb_movie_details.get('overview', 'N/A')}</div>", unsafe_allow_html=True)

                        with col2:
                            poster_path = tmdb_movie_details.get('poster_path')
                            if poster_path:
                                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                                st.image(poster_url, width=150)

                        movie_id = insert_movie(tmdb_movie_details, tmdb_movie_credits)
                        st.session_state.selected_movie_id = movie_id
                    else:
                        st.error("영화 상세 정보를 가져오는 데 실패했습니다.")
                else:
                    st.warning("검색 결과가 없습니다.")
            else:
                st.error("영화 이름을 입력해주세요.")

        if st.session_state.selected_movie_id:
            review_text = st.text_area('리뷰를 작성하세요')
            if st.button('리뷰 제출'):
                if review_text:
                    sentiment = predict_sentiment(review_text)
                   
