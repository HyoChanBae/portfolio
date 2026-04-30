# API KEY를 환경변수로 관리하기 위한 설정 파일
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_classic.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

# API KEY 정보로드
load_dotenv()

# MySQL 데이터베이스에 연결합니다.
db = SQLDatabase.from_uri(
    "mysql+pymysql://root:Root1234%21@3.94.10.95:3306/testdb"
)

# 데이터베이스 dialect 출력
print(db.dialect)

# 사용 가능한 테이블 이름 출력
print(db.get_usable_table_names())

# model 은 gpt-3.5-turbo 를 지정
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# LLM 과 DB 를 매개변수로 입력하여 chain 을 생성합니다.
chain = create_sql_query_chain(llm, db)



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
generated_sql_query = chain.invoke({"question": "판매자가 등록한 주소의 도시들이 총 몇 종류 있나 알려줘"})

# 생성된 쿼리를 출력합니다.
print(generated_sql_query.__repr__())

# 생성한 쿼리를 실행하기 위한 도구를 생성합니다.
execute_query = QuerySQLDataBaseTool(db=db)
result = execute_query.invoke({"query": generated_sql_query})
print(result)

