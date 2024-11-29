import streamlit as st
from checkdb import (
    save_review,
    create_user,
    verify_user,
    insert_movie_if_not_exists,
    recommend_movies_based_on_genre_and_overview,
    check_review_exists,
    get_db_connection,
    insert_movie_genres
)
import os
import sys
from dotenv import load_dotenv
from lstm_model import predict_sentiment

# 환경 변수 로드
## 지현
# load_dotenv(dotenv_path="C:\\Users\\you0m\\Desktop\\movie\\env_example.env")
## 채린
load_dotenv()

st.set_page_config(
    page_title="무비뭐봐",
    page_icon="🎬",
    layout="wide",
)

## 지현
# sys.path.append(os.path.abspath("C:/Users/you0m/Desktop/movie/utils"))
## 채린
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from utils.api_fetch import (
    search_tmdb_movie,
    get_tmdb_movie_details,
    get_tmdb_movie_credits,
    get_tmdb_movie_details_with_genres
)

# CSS 스타일링
st.markdown("""
<style>
body {
}
[data-testid="stAppViewContainer"] {
    background-color: #000000;
    color: #FFFFFF;
}
/* 헤더 바 배경색 및 텍스트 색상 변경 */
header[data-testid="stHeader"] {
    background-color: #000000;
}

header[data-testid="stHeader"] * {
    color: #FFFFFF;
}

.main-title {
    text-align: center;
    color: #B22222; /* 버튼과 동일한 빨간색 */
    font-weight: bold;
    font-size: 3rem; /* 원하는 크기로 조정 */
}

.navbar {
    display: flex; justify-content: flex-end; align-items: center;
    padding: 10px 20px; background-color: #f8f9fa;
}
.navbar .mypage-btn {
    font-size: 0.9rem; color: #555; background: none; border: none;
    text-decoration: underline; cursor: pointer;
}
.title-section {
    text-align: center; margin-top: 10px; margin-bottom: 20px;
}
.title-section .main-title { font-size: 2rem; color: #B22222; font-weight: bold; }
.title-section .subtitle { font-size: 1rem; color: #555; }
.movie-search {
    text-align: center; margin-bottom: 20px;
}
.movie-poster img { height: 150px; object-fit: cover; border-radius: 5px; }
.movie-title {
    font-size: 0.8rem; /* 제목 크기 */
    text-align: left; /* 제목 왼쪽 정렬 */
    margin-left: 10px; /* 제목을 살짝 왼쪽으로 이동 */
}
.movie-container {
    text-align: center; /* 전체 가운데 정렬 */
}
div.stButton > button {
    background-color: #B22222; /* 버튼 배경색을 빨간색으로 설정 */
    color: #FFFFFF; /* 버튼 글씨색을 하얀색으로 설정 */
    border: none; /* 테두리 제거 */
    padding: 0.5em 1em; /* 패딩 조절 */
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 1em;
    margin: 0.2em;
    cursor: pointer;
    border-radius: 5px;
}

div.stButton > button:hover {
    background-color: #B22222; /* 호버 시에도 색상 변화 없도록 */
    color: #FFFFFF;
}

div.stButton > button:active {
    background-color: #B22222; /* 클릭 시에도 색상 변화 없도록 */
}
div[class^='stTextInput'] > label > div[data-testid='stMarkdownContainer'] > p {
    text-align: center; /* 레이블 중앙 정렬 */
}

div[class^='stTextInput'] {
    width: 100% !important;
}

div[class^='stTextInput'] > div {
    width: 100% !important;
}

div[class^='stTextInput'] input {
    width: 100% !important;
    text-align: left; /* 입력 텍스트 중앙 정렬 */
}

/* 제목 텍스트 중앙 정렬 */
h1 {
    text-align: center;
}

/* 입력 필드 레이블의 텍스트 색상을 하얀색으로 변경 */
div[class^='stTextInput'] label p {
    color: #FFFFFF;
}

/* 링크 스타일 변경 */
a {
    color: #FFFFFF !important;
    text-decoration: none; /* 밑줄 제거 */
}

/* 링크에 마우스를 올렸을 때 스타일 유지 */
a:hover {
    color: #FFFFFF;
    text-decoration: none;
}
            
/* 사이드바 배경색 변경 */
[data-testid="stSidebar"] {
    background-color: #1E1E1E; /* 더 어두운 색상으로 변경 */
}

/* 사이드바 텍스트 색상 변경 */
[data-testid="stSidebar"] * {
    color: #FFFFFF; /* 텍스트를 하얀색으로 변경 */
}

.button-container {
    display: flex;
    justify-content: center; /* 중앙 정렬 */
    gap: 10px; /* 버튼 사이 간격 */
    margin-top: 20px; /* 위쪽 여백 */
}    
            
/* 검색창 스타일 */
.search-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 20px;
}

.search-container .search-input {
    width: 300px;
    padding: 0.5em;
    font-size: 1em;
}

.search-container .search-button {
    background-color: #B22222;
    color: #FFFFFF;
    border: none;
    padding: 0.5em 1em;
    font-size: 1em;
    cursor: pointer;
    border-radius: 5px;
    margin-left: 10px;
}

div.stButton {
    text-align: center;
}

div[class^='stTextInput'] input {
    width: 100% !important;
    max-width: 300px; /* 최대 너비 설정 */
    text-align: left;
}        

.input-container {
    max-width: 300px;
    margin: 0 auto; /* 중앙 정렬 */
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">
    무비뭐봐🎬
</div>
""", unsafe_allow_html=True)
st.markdown('<p style="text-align: center;">리뷰 기반 영화 추천 시스템</p>', unsafe_allow_html=True)

# 세션 초기화
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

# 마이페이지 구현 (포스터 포함)
def display_user_reviews():
    st.header("마이페이지")
    st.subheader(f"{st.session_state.username}님의 리뷰 목록")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT m.movie_name, r.review_text, r.sentiment, m.tmdb_id
                FROM REVIEW r
                JOIN MOVIE m ON r.movie_id = m.movie_id
                WHERE r.user_id = %s
            """, (st.session_state.user_id,))
            reviews = cur.fetchall()
            if reviews:
                for review in reviews:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        sentiment_kor = '좋아요' if review['sentiment'] == 'positive' else '싫어요'
                        st.markdown(f"**영화명:** {review['movie_name']}")
                        st.markdown(f"**리뷰:** {review['review_text']}")
                        st.markdown(f"해당 영화가 {sentiment_kor}")
                        st.markdown("---")
                    with col2:
                        # 영화 포스터 가져오기
                        movie_details = get_tmdb_movie_details(review['tmdb_id'])
                        if movie_details and movie_details.get('poster_path'):
                            poster_url = f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}"
                            st.image(poster_url, width=100)  # 포스터 표시
                        else:
                            st.write("포스터 없음")  # 포스터가 없을 경우 대체 텍스트
            else:
                st.info("작성한 리뷰가 없습니다.")
    finally:
        conn.close()

        
    # "영화 검색으로 돌아가기" 버튼 추가
    if st.button("영화 검색하기"):
        st.session_state.current_page = "search"  # 페이지 상태를 검색으로 변경


# 로그인/회원가입 처리
if not st.session_state.get('logged_in', False):
    if st.session_state.get('show_signup', False):
        st.markdown("<h2 style='text-align: center;'>회원가입</h2>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            new_user_id = st.text_input('사용자 아이디', key='new_user_id')
            new_password = st.text_input('비밀번호', type='password', key='new_password')
            confirm_password = st.text_input('비밀번호 확인', type='password', key='confirm_password')
            username = st.text_input('이름', key='new_username')

        signup_submit_button = st.button('회원가입 하기', key='signup_submit')
        login_redirect_button = st.button('이미 계정이 있나요? 로그인', key='login_redirect')


        if signup_submit_button:
            if new_user_id and new_password and confirm_password and username:
                if new_password != confirm_password:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    create_user(new_user_id, new_password, username)
                    st.success("회원가입이 완료되었습니다.")
                    st.session_state.show_signup = False
            else:
                st.error("모든 필드를 입력해주세요.")
        if login_redirect_button:
            st.session_state.show_signup = False
    else:
        st.markdown("<h2 style='text-align: center;'>로그인</h2>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            user_id = st.text_input('사용자 아이디')
            password = st.text_input('비밀번호', type='password')
    

        login_button = st.button('로그인', key='login_button')
        signup_button = st.button('회원가입', key='signup_button')


        if login_button:
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
        if signup_button:
            st.session_state.show_signup = True
else:
    # 세션 상태를 이용한 페이지 전환 처리
    if "current_page" not in st.session_state:
        st.session_state.current_page = "search"  # 기본 페이지: 영화 검색
    if "show_recommendation" not in st.session_state:
        st.session_state.show_recommendation = False  # 추천 영화 표시 여부
        
    # 사이드바로 마이페이지 버튼 추가
    with st.sidebar:
        if st.button("마이페이지"):
            st.session_state.current_page = "mypage"  # 세션 상태로 페이지 전환

    # 페이지 상태에 따라 화면 구성
    if st.session_state.current_page == "mypage":
        display_user_reviews()  # 마이페이지 표시
    else:
        # 영화 검색창
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            search_col, button_col = st.columns([4, 1])
            with search_col:
                search_query = st.text_input("", key="search_query", placeholder="영화 이름을 입력하세요", label_visibility='collapsed')
            with button_col:
                search_button = st.button("검색", key="search_button")

        if search_button:
            if search_query:
                search_results = search_tmdb_movie(search_query)
                if search_results and 'results' in search_results and len(search_results['results']) > 0:
                    movie_data = search_results['results'][0]
                    tmdb_id = movie_data['id']
                    tmdb_movie_details, genres = get_tmdb_movie_details_with_genres(tmdb_id)
                    tmdb_movie_credits = get_tmdb_movie_credits(tmdb_id)
                    if tmdb_movie_details:
                        st.session_state.show_recommendation = False  # 검색 결과를 표시할 경우 추천 영화 숨김
                        st.session_state.selected_movie_id = insert_movie_if_not_exists(tmdb_movie_details, tmdb_movie_credits)
                        if genres:
                            insert_movie_genres(st.session_state.selected_movie_id, genres)
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
                        # 영화 및 장르 저장
                        movie_id = insert_movie_if_not_exists(tmdb_movie_details, tmdb_movie_credits)
                        if genres:
                            insert_movie_genres(movie_id, genres)
                        st.session_state.selected_movie_id = movie_id
                        st.success("영화 정보가 저장되었습니다. 이제 리뷰를 작성해주세요.")

                        # **다른 사용자들의 리뷰를 표시하는 코드 추가**
                        st.subheader("다른 사용자들의 리뷰")
                        conn = get_db_connection()
                        try:
                            with conn.cursor() as cur:
                                # 리뷰와 사용자 이름을 가져오기 위해 USER 테이블과 JOIN
                                cur.execute("""
                                    SELECT r.review_text, r.sentiment, u.username
                                    FROM REVIEW r
                                    JOIN USER u ON r.user_id = u.user_id
                                    WHERE r.movie_id = %s
                                """, (movie_id,))
                                reviews = cur.fetchall()
                                if reviews:
                                    for review in reviews:
                                        st.markdown(f"**{review['username']}님의 리뷰:**")
                                        st.write(review['review_text'])
                                        st.markdown("---")
                                else:
                                    st.info("아직 이 영화에 대한 다른 사용자의 리뷰가 없습니다.")
                        finally:
                            conn.close()

                    else:
                        st.error("영화 상세 정보를 가져오는 데 실패했습니다.")
                else:
                    st.warning("검색 결과가 없습니다.")
            else:
                st.error("검색어를 입력하세요.")

        # 영화가 선택된 경우에만 리뷰 작성 섹션 표시
        if st.session_state.selected_movie_id:
            review_exists = check_review_exists(st.session_state.user_id, st.session_state.selected_movie_id)
            if review_exists:
                st.warning("해당 영화에 대한 리뷰가 이미 존재합니다.")
            else:
                st.subheader("리뷰 작성")
                review_text = st.text_area("리뷰를 입력하세요", key="review_text")
                if st.button("리뷰 제출"):
                    if review_text:
                        sentiment = predict_sentiment(review_text)
                        save_review(st.session_state.user_id, st.session_state.selected_movie_id, review_text, sentiment)
                        st.success("리뷰가 저장되었습니다.")
                        conn = get_db_connection()
                        try:    
                            with conn.cursor() as cur:
                                cur.execute("SELECT movie_name FROM MOVIE WHERE movie_id = %s", (st.session_state.selected_movie_id,))
                                selected_movie = cur.fetchone()
                                if selected_movie:
                                    movie_name = selected_movie['movie_name']
                                    if sentiment == "positive":
                                        st.subheader(f'"{movie_name}"와 비슷한 영화 추천')
            
                                        # 유사한 영화 추천
                                        recommended_movies = recommend_movies_based_on_genre_and_overview(st.session_state.selected_movie_id, limit=5)
                                        if recommended_movies:
                                            cols = st.columns(5)  # 5개의 열 생성
                                            for i, movie in enumerate(recommended_movies):
                                                with cols[i % 5]:  # 5개씩 가로로 정렬
                                                    movie_details = get_tmdb_movie_details(movie['tmdb_id'])
                                                    if movie_details and movie_details.get('poster_path'):
                                                        poster_url = f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}"
                                                        st.image(poster_url, use_container_width=True)
                                                    else:
                                                        st.write("포스터 없음")
                                                    st.markdown(
                                                        f"[**{movie['movie_name']}**](https://www.themoviedb.org/movie/{movie['tmdb_id']})",
                                                        unsafe_allow_html=True,
                                                    )
                                        else:
                                            st.write("추천할 영화가 없습니다.")
                                    else:
                                        # 부정 리뷰: 랜덤 영화 추천
                                        st.subheader("이런 영화는 어떠신가요?")
                                        conn = get_db_connection()
                                        with conn.cursor() as cur:
                                            cur.execute("""
                                                SELECT movie_name, tmdb_id
                                                FROM movie_list
                                                ORDER BY RAND()
                                                LIMIT 5
                                            """)
                                            random_movies = cur.fetchall()  # 커서에서 fetchall() 호출
                                            if random_movies:
                                                cols = st.columns(5)
                                                for i, movie in enumerate(random_movies):
                                                    with cols[i % 5]:
                                                        movie_details = get_tmdb_movie_details(movie['tmdb_id'])
                                                        if movie_details and movie_details.get('poster_path'):
                                                            poster_url = f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}"
                                                            st.image(poster_url, use_container_width=True)
                                                        else:
                                                            st.write("포스터 없음")
                                                        st.markdown(
                                                            f"[**{movie['movie_name']}**](https://www.themoviedb.org/movie/{movie['tmdb_id']})",
                                                            unsafe_allow_html=True,
                                                        )
                                            else:   
                                                st.write("추천할 영화가 없습니다.")
                                else:
                                    st.error("선택된 영화의 이름을 가져오는 데 실패했습니다.")
                        finally:
                            conn.close()
                    else:
                        st.error('리뷰를 작성해주세요.')
        else:
            # 로그인 후 첫 화면에서만 "오늘의 추천 영화" 표시
            st.subheader("오늘의 추천 영화")
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT movie_name, tmdb_id
                        FROM movie_list
                        ORDER BY RAND()
                        LIMIT 5
                    """)
                    movies = cur.fetchall()
            finally:
                conn.close()

            cols = st.columns(5)
            for i, movie in enumerate(movies):
                with cols[i]:
                    movie_details = get_tmdb_movie_details(movie['tmdb_id'])
                    if movie_details and movie_details.get('poster_path'):
                        st.image(f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}", width=150)
                    st.markdown(
                        f"[**{movie['movie_name']}**](https://www.themoviedb.org/movie/{movie['tmdb_id']})",
                        unsafe_allow_html=True,
                    )