from typing import Literal, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
# API KEY를 환경변수로 관리하기 위한 설정 파일
from dotenv import load_dotenv
import logging

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from db_config import get_db
from sql_utils import sql_for_copy_paste


# API KEY 정보로드
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
# OpenAI / httpx 요청 로그 숨기기
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


db = get_db()

print(db.dialect)
print(db.get_usable_table_names())
####################################################################################
class GraphState(TypedDict):
    question: str
    route: str
    answer: str


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def classify_question(state: GraphState):
    question = state["question"]

    prompt = f"""
        다음 질문을 분류하세요.

        분류 기준:
        - db: 데이터베이스 조회, 테이블, 컬럼, 매출, 주문, 고객, 상품, seller, SQL이 필요한 질문
        - general: 일반 지식, 개념 설명, 번역, 코딩 개념, DB 조회가 필요 없는 질문

        질문: {question}

        반드시 db 또는 general 중 하나만 답하세요.
        """

    route = llm.invoke(prompt).content.strip().lower()

    if route not in ["db", "general"]:
        route = "general"

    return {"route": route}


def answer_general(state: GraphState):
    question = state["question"]

    response = llm.invoke(f"""
다음 질문에 한국어로 자연스럽게 답변하세요.

질문: {question}
""")

    return {"answer": response.content}


def answer_db(state: GraphState):
    question = state["question"]
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
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    chain = create_sql_query_chain(llm, db, prompt)
    # 여기 안에 기존 SQL 생성 체인 + 실행 체인을 넣으면 됩니다.
    # gpt 가이드 # generated_sql = write_query.invoke({"question": question})
    generated_sql = chain.invoke({"question": question})
    
    # gpt 가이드 #  result = execute_query.invoke({"query": generated_sql})
    # 생성한 쿼리를 실행하기 위한 도구를 생성합니다.
    execute_query = QuerySQLDataBaseTool(db=db)
    result = execute_query.invoke({"query": generated_sql})
    print(result)
    return {
        "answer": f"""
    DB 조회 질문으로 분기되었습니다.

    생성 SQL:
    {generated_sql}

    조회 결과:
    {result}
    """
    }
  

def route_question(state: GraphState) -> Literal["db", "general"]:
    return state["route"]


graph = StateGraph(GraphState)

graph.add_node("classify_question", classify_question)
graph.add_node("answer_general", answer_general)
graph.add_node("answer_db", answer_db)

graph.set_entry_point("classify_question")

graph.add_conditional_edges(
    "classify_question",
    route_question,
    {
        "db": "answer_db",
        "general": "answer_general",
    },
)

graph.add_edge("answer_db", END)
graph.add_edge("answer_general", END)

app = graph.compile()

result = app.invoke({
    "question": "주문 기록 기간이 어디서부터 어디까지 적재되어있는가가"
})

print(result["answer"])