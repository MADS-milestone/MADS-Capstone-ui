import os

import streamlit as st
import random
import time
import requests as req
from dotenv import load_dotenv

load_dotenv()
if "API_HOST" not in st.session_state:
    st.session_state["api_host"] = os.getenv("API_HOST")


# Streamed response emulator
def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

st.title("UMSI Clinical Trials chatbot")
st.caption("Brought to you by the RAGtime Band")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What are you searching for?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        #response = st.write_stream(response_generator())
        api_res = req.post(f"{st.session_state.api_host}/get_response", json=prompt)
        res = api_res.json()["detail"]["response"]
        response = st.write_stream(response_generator(res))
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

