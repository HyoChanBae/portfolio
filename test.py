from typing import Literal, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END



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

    # 여기 안에 기존 SQL 생성 체인 + 실행 체인을 넣으면 됩니다.
    # generated_sql = write_query.invoke({"question": question})
    # result = execute_query.invoke({"query": generated_sql})
    # answer = answer_chain.invoke({...})

    return {
        "answer": f"DB 조회 질문으로 분기되었습니다. 여기서 SQL 생성/실행 로직을 연결하면 됩니다. 질문: {question}"
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
    "question": "beleza_saude가 뭐야?"
})

print(result["answer"])