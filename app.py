import streamlit as st
from checkdb import (
    save_review,
    create_user,
    verify_user,
    insert_movie_if_not_exists,
    recommend_movies_based_on_genre_and_overview,
    check_review_exists,
    recommend_random_movies,
    get_db_connection,
    insert_movie_genres
)
import sys
import os
import pymysql
from dotenv import load_dotenv
from lstm_model import predict_sentiment

# 환경 변수 로드
load_dotenv(dotenv_path="C:\\Users\\you0m\\Desktop\\movie\\env_example.env")

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
    get_tmdb_movie_credits,
    get_tmdb_movie_details_with_genres
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

if not st.session_state.get('logged_in', False):
    if st.session_state.get('show_signup', False):
        st.header('회원가입')

        new_user_id = st.text_input('사용자 아이디', key='new_user_id')
        new_password = st.text_input('비밀번호', type='password', key='new_password')
        confirm_password = st.text_input('비밀번호 확인', type='password', key='confirm_password')
        username = st.text_input('이름', key='new_username')

        if st.button('회원가입 하기'):
            if new_user_id and new_password and confirm_password and username:
                if new_password != confirm_password:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    # 회원가입 처리
                    create_user(new_user_id, new_password, username)
                    st.success("회원가입이 완료되었습니다.")
                    st.session_state.show_signup = False  # 회원가입 화면 종료
                    st.session_state.show_login_button = True  # 로그인하기 버튼 활성화
            else:
                st.error("모든 필드를 입력해주세요.")

        # 회원가입 완료 후에만 "로그인하기" 버튼 표시
        if st.session_state.get('show_login_button', False):
            if st.button('로그인하기'):
                st.session_state.show_signup = False  # 회원가입 화면 종료
                st.session_state.show_login_button = False  # 로그인 버튼 숨김
                st.experimental_rerun()  # 로그인 화면으로 새로고침

        # 회원가입 중에는 "이미 계정이 있나요? 로그인" 버튼 표시
        elif st.button('이미 계정이 있나요? 로그인'):
            st.session_state.show_signup = False  # 회원가입 화면 종료

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
            st.session_state.show_signup = True  # 회원가입 화면 활성화


else:
    st.header('영화 검색')

    search_query = st.text_input('영화 이름을 입력하세요')

    if st.button('검색'):
        if search_query:
            search_results = search_tmdb_movie(search_query)
            if search_results and 'results' in search_results and len(search_results['results']) > 0:
                movie_data = search_results['results'][0]
                tmdb_id = movie_data['id']
                
                # TMDB 영화 세부 정보와 장르 가져오기
                tmdb_movie_details, genres = get_tmdb_movie_details_with_genres(tmdb_id)
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
                            st.markdown(f"""
                                        <div style="text-align: center; margin-left: 100px;">
                                            <img src="{poster_url}" width="230">
                                        </div>
                                        """, unsafe_allow_html=True)

                    # 영화가 이미 DB에 있는지 확인 및 삽입
                    movie_id = insert_movie_if_not_exists(tmdb_movie_details, tmdb_movie_credits)
                    if genres:
                        insert_movie_genres(movie_id, genres)  # 장르 삽입

                    st.session_state.selected_movie_id = movie_id
                    st.success("영화 정보가 저장되었습니다. 이제 리뷰를 작성해주세요.")
                else:
                    st.error("영화 상세 정보를 가져오는 데 실패했습니다.")
            else:
                st.warning("검색 결과가 없습니다.")
        else:
            st.error("영화 이름을 입력해주세요.")

    # 영화가 선택된 경우에만 리뷰 작성 섹션 표시
    if st.session_state.selected_movie_id:
        # 해당 영화에 대한 리뷰가 이미 존재하는지 확인
        review_exists = check_review_exists(st.session_state.user_id, st.session_state.selected_movie_id)
        if review_exists:
            st.warning("해당 영화에 대한 리뷰가 이미 존재합니다.")
        else:
            st.subheader("리뷰 작성")
            review_text = st.text_area('영화에 대한 리뷰를 작성하세요', key="review_text")

            if st.button('리뷰 제출'):
                if review_text:
                    sentiment = predict_sentiment(review_text)
                    st.session_state.review_saved = True
                    
                    # 리뷰를 데이터베이스에 저장
                    save_review(st.session_state.user_id, st.session_state.selected_movie_id, review_text, sentiment)
                    
                    st.success("리뷰가 저장되었습니다.")
                    
                    if sentiment == "positive":
                        # 선택된 영화의 제목을 가져오기
                        conn = get_db_connection()
                        try:
                            with conn.cursor() as cur:
                                # 선택된 영화의 제목을 가져옴
                                cur.execute("SELECT movie_name FROM MOVIE WHERE movie_id = %s", (st.session_state.selected_movie_id,))
                                selected_movie = cur.fetchone()
                                if selected_movie:
                                    movie_name = selected_movie['movie_name']
                                    st.subheader(f'"{movie_name}"와 비슷한 영화 추천')

                                    # 장르와 overview 기반으로 유사한 영화 추천
                                    recommended_movies = recommend_movies_based_on_genre_and_overview(
                                        st.session_state.selected_movie_id, limit=5)
                                    if recommended_movies:
                                        for movie in recommended_movies:
                                            tmdb_url = f"https://www.themoviedb.org/movie/{movie['tmdb_id']}"
                                            st.markdown(f"[{movie['movie_name']}]({tmdb_url})", unsafe_allow_html=True)
                                    else:
                                        st.write("추천할 영화가 없습니다.")
                                else:
                                    st.error("선택된 영화의 이름을 가져오는 데 실패했습니다.")
                        finally:
                            conn.close()

                    else:
                        st.subheader("이런 영화는 어떠신가요?")
                        # 랜덤으로 평점 좋은 영화 5개 추천
                        recommended_movies = recommend_random_movies(limit=5)
                        if recommended_movies:
                            for movie in recommended_movies:
                                tmdb_url = f"https://www.themoviedb.org/movie/{movie['tmdb_id']}"
                                st.markdown(f"[{movie['movie_name']}]({tmdb_url})", unsafe_allow_html=True)
                        else:
                            st.write("추천할 영화가 없습니다.")
                else:
                    st.error("리뷰를 작성해주세요.")
