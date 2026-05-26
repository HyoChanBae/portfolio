import logging
from typing import Literal, NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_classic.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from db_config import get_db
from schema_context import SCHEMA_RELATIONSHIPS
from sql_utils import sql_for_copy_paste

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

SQL_PROMPT = PromptTemplate.from_template(
    """You are a {dialect} expert. Write ONE executable SQL query only.

Rules:
- Use ONLY tables/columns listed below. If a column is not in a table, JOIN the correct table.
- For customer city/state, JOIN customers on orders.customer_id = customers.customer_id.
- For revenue/sales amounts, use order_items.price (usually with orders + order_items).
- Do not invent column names (e.g. orders.customer_city does not exist).
- Unless the user asks for a specific count, limit SELECT results to at most {top_k} rows.

Schema relationships and join examples:
{schema_relationships}

Table definitions (columns + sample rows):
{table_info}

Question: {input}"""
)

MAX_SQL_RETRIES = 2


def _is_sql_error(result: object) -> bool:
    text = str(result).lower()
    markers = (
        "error",
        "unknown column",
        "doesn't exist",
        "does not exist",
        "no such column",
        "1054",
        "1146",
        "existieren nicht",
        "열이 존재하지 않",
    )
    return any(m in text for m in markers)


class GraphState(TypedDict):
    question: str
    route: NotRequired[str]
    answer: NotRequired[str]
    sql: NotRequired[str]
    db_result: NotRequired[str]


def build_graph(
    db: SQLDatabase | None = None,
    router_llm: ChatOpenAI | None = None,
    sql_llm: ChatOpenAI | None = None,
):
    db = db or get_db()
    router_llm = router_llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)
    sql_llm = sql_llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    sql_prompt = SQL_PROMPT.partial(
        dialect=db.dialect,
        schema_relationships=SCHEMA_RELATIONSHIPS,
    )
    sql_chain = create_sql_query_chain(sql_llm, db, sql_prompt)
    execute_query = QuerySQLDataBaseTool(db=db)

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
        route = router_llm.invoke(prompt).content.strip().lower()
        if route not in ("db", "general"):
            route = "general"
        return {"route": route}

    def answer_general(state: GraphState):
        question = state["question"]
        response = router_llm.invoke(
            f"""다음 질문에 한국어로 자연스럽게 답변하세요.

질문: {question}
"""
        )
        return {"answer": response.content}

    def answer_db(state: GraphState):
        question = state["question"]
        chain_input: dict[str, str] = {"question": question}
        sql_clean = ""
        db_result = ""

        for attempt in range(MAX_SQL_RETRIES + 1):
            generated_sql = sql_chain.invoke(chain_input)
            sql_clean = sql_for_copy_paste(generated_sql)
            db_result = execute_query.invoke({"query": sql_clean})

            if not _is_sql_error(db_result):
                break

            if attempt >= MAX_SQL_RETRIES:
                break

            chain_input = {
                "question": (
                    f"{question}\n\n"
                    f"The previous SQL failed.\n"
                    f"SQL:\n{sql_clean}\n"
                    f"Error:\n{db_result}\n"
                    "Fix the query. Remember: customer_city is in customers, "
                    "not orders. Join customers when filtering or grouping by customer city."
                )
            }
            logging.info("SQL 오류로 재생성 시도 (%s/%s)", attempt + 1, MAX_SQL_RETRIES)

        summary = router_llm.invoke(
            f"""사용자 질문에 대해 DB 조회 결과를 바탕으로 한국어로 간결하게 답변하세요.

질문: {question}
실행 SQL:
{sql_clean}

조회 결과:
{db_result}
"""
        )
        return {
            "answer": summary.content,
            "sql": sql_clean,
            "db_result": str(db_result),
        }

    def route_question(state: GraphState) -> Literal["db", "general"]:
        return state["route"]  # type: ignore[return-value]

    graph = StateGraph(GraphState)
    graph.add_node("classify_question", classify_question)
    graph.add_node("answer_general", answer_general)
    graph.add_node("answer_db", answer_db)
    graph.set_entry_point("classify_question")
    graph.add_conditional_edges(
        "classify_question",
        route_question,
        {"db": "answer_db", "general": "answer_general"},
    )
    graph.add_edge("answer_db", END)
    graph.add_edge("answer_general", END)

    return graph.compile()
