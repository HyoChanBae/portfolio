import os

from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

from schema_context import CUSTOM_TABLE_INFO

load_dotenv()


def get_db() -> SQLDatabase:
    db_uri = os.getenv("DATABASE_URL")

    if not db_uri:
        raise ValueError("DATABASE_URL 환경변수가 설정되어 있지 않습니다.")

    return SQLDatabase.from_uri(
        db_uri,
        custom_table_info=CUSTOM_TABLE_INFO,
        sample_rows_in_table_info=2,
    )