import pymysql
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(dotenv_path="../.env")

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