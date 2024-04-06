import os

import streamlit as st
import random
import time
import requests as req
from dotenv import load_dotenv
from streamlit_modal import Modal
import streamlit.components.v1 as components

load_dotenv()
if "API_HOST" not in st.session_state:
    st.session_state["api_host"] = os.getenv("API_HOST")


# Streamed response emulator
def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


def set_condition(condition):
    if condition is None or len(condition.strip()) == 0:
        return
    api_res = req.get(f"{st.session_state.api_host}/get_most_recent_trial/{condition}").json()
    if api_res["detail"]["results_found"]:
        init_prompt = f"Are you familiar with trial {api_res['detail']['nct_id']} with brief title: \"{api_res['detail']['brief_title']}?\""
        st.session_state.init_prompt = init_prompt
    else:
        st.warning(f"No clinical trials found for {condition}")
        return
    st.session_state["condition"] = condition


if "condition" not in st.session_state or st.session_state["condition"] is None:
    st.title("Welcome to the UMSI Clinical Trials!")
    st.markdown("""Get insights into the newest healthcare research.  
    I'm your trusty guide, here to help you explore Pfizer's latest Phase 3 Clinical Trials.  
    Simply name a condition that interests you (for example: Migraine? Leukemia? Pneumonia?)  
    I'll return the most recent trial and get ready for your questions.  
    Ready? Let's get started.""")
    condition = st.text_input(label="Condition", placeholder="Please enter condition", label_visibility="collapsed")
    st.button("Submit", on_click=set_condition, args=(condition,))
else:
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
    if prompt := st.chat_input() or st.session_state.init_prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            api_res = req.post(f"{st.session_state.api_host}/get_response", json=prompt)
            res = api_res.json()["response"]
            response = st.write_stream(response_generator(res))
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
