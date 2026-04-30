
import streamlit as st

st.title("Hello World")


user_input = st.chat_input("Enter your prompt")

if user_input:
    st.chat_message("user").write(user_input)
    # with st.chat_message("user"):
    #     st.write(user_input)







