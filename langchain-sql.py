# API KEY를 환경변수로 관리하기 위한 설정 파일
from dotenv import load_dotenv
import logging
import os
import re
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

# API KEY 정보로드
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")

#sql 로그 보기 좋게 하기 위한 함수
def sql_for_copy_paste(raw: object) -> str:
    """LLM 출력 전체가 오거나 이스케이프된 \\n이 섞여도 DB에 붙여넣기 쉬운 한 줄/여러 줄 SQL로 정리."""
    s = raw.strip() if isinstance(raw, str) else str(raw).strip()
    if "SQLQuery:" in s:
        s = s.split("SQLQuery:", 1)[1].strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    start_kw = re.search(
        r"\b(WITH|SELECT|INSERT|UPDATE|DELETE|SHOW|DESCRIBE|EXPLAIN)\b",
        s,
        re.IGNORECASE | re.DOTALL,
    )
    if start_kw:
        s = s[start_kw.start() :].strip()
    s = s.replace("\\n", "\n").replace("\\t", "\t")
    return s.strip()

# MySQL 데이터베이스에 연결합니다.
db_uri = os.getenv("DATABASE_URL")
if not db_uri:
    raise ValueError("DATABASE_URL 환경변수가 설정되어 있지 않습니다.")

db = SQLDatabase.from_uri(db_uri)

# 데이터베이스 dialect 출력
print(db.dialect)

# 사용 가능한 테이블 이름 출력
print(db.get_usable_table_names())

prompt = PromptTemplate.from_template(
    """Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer. Unless the user specifies in his question a specific number of examples he wishes to obtain, always limit your query to at most {top_k} results. You can order the results by a relevant column to return the most interesting examples in the database.
Use the following format:

Question: "Question here"
SQLQuery: "SQL Query to run"
SQLResult: "Result of the SQLQuery"
Answer: "Final answer here"

Only use the following tables:
{table_info}

Here is the description of the columns in the tables:
`seller_city`: city name of the seller's registered address  
`seller_id`: unique seller identifier (primary key)  
`seller_state`: state/region code of the seller's location  
`seller_zip_code_prefix`: leading digits of the seller's postal code (used for regional grouping)

Question: {input}"""
).partial(dialect=db.dialect)

# model 은 gpt-3.5-turbo 를 지정
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# LLM 과 DB 를 매개변수로 입력하여 chain 을 생성합니다.
chain = create_sql_query_chain(llm, db, prompt)

# chain 을 실행하고 결과를 출력합니다.
generated_sql_query = chain.invoke({"question": "beleza_saude가 뭐야?"})

sql_clean = sql_for_copy_paste(generated_sql_query)
logging.info("생성 SQL (아래 블록 그대로 복사해 DB 클라이언트에 붙여넣기)\n---\n%s\n---", sql_clean)

# 생성한 쿼리를 실행하기 위한 도구를 생성합니다.
execute_query = QuerySQLDataBaseTool(db=db)
result = execute_query.invoke({"query": sql_clean})
# 실행 값 출력
print(result)

