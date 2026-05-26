"""LangGraph 통합 로컬 테스트 (CLI). UI는 app.py 사용."""

from dotenv import load_dotenv

from graph import build_graph

load_dotenv()

if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"question": "sao paulo의 매출을 알려줘"})
    print(result.get("answer", ""))
    if sql := result.get("sql"):
        print("\n--- SQL ---\n", sql)
