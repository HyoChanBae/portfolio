import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import ChatMessage

from db_config import get_db
from graph import build_graph

load_dotenv()

st.set_page_config(page_title="LangChain SQL Chat", page_icon="💬")
st.title("LangChain SQL Chat")


def print_history():
    for msg in st.session_state["messages"]:
        st.chat_message(msg.role).write(msg.content)


def add_history(role: str, content: str):
    st.session_state["messages"].append(ChatMessage(role=role, content=content))


@st.cache_resource
def get_graph_app():
    return build_graph(get_db())


if "messages" not in st.session_state:
    st.session_state["messages"] = []

print_history()

if user_input := st.chat_input("질문을 입력하세요"):
    add_history("user", user_input)
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            result = get_graph_app().invoke({"question": user_input})

        answer = result.get("answer", "답변을 생성하지 못했습니다.")
        st.markdown(answer)

        if sql := result.get("sql"):
            with st.expander("생성된 SQL"):
                st.code(sql, language="sql")

        route = result.get("route")
        if route:
            st.caption(f"분기: {route}")

    add_history("assistant", answer)
