import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

load_dotenv()

def get_db() -> SQLDatabase:
    db_uri = os.getenv("DATABASE_URL")

    if not db_uri:
        raise ValueError("DATABASE_URL 환경변수가 설정되어 있지 않습니다.")

    return SQLDatabase.from_uri(db_uri)