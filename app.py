import os

import streamlit as st
import time
import requests as req
from dotenv import load_dotenv
import asyncio

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
    with st.spinner(f'Looking up trials for {condition}...'):
        api_res = req.get(f"{st.session_state.api_host}/get_trials_for_condition/{condition}").json()

    if api_res["detail"]["results_found"]:
        res_for_condition = [res["nct_id"] + " - " + res["brief_title"] for res in api_res["detail"]["trials"]]
        st.session_state["res_for_condition"] = res_for_condition
    else:
        st.warning(f"No clinical trials found for {condition}")
        return
    st.session_state["condition"] = condition


def set_trial(trial):
    trial_parts = trial.split(" - ")
    trial_prompt = f"Are you familiar with trial {trial_parts[0]} with brief title: {trial_parts[1]}"
    with st.spinner('Please wait...'):
        req.post(f"{st.session_state.api_host}/get_response", json=trial_prompt)
    st.session_state.current_trial = trial


if "current_trial" not in st.session_state or st.session_state["current_trial"] is None:
    st.title("Welcome to the UMSI Clinical Trials!")
    st.markdown("""Get insights into the newest healthcare research.  
    I'm your trusty guide, here to help you explore Pfizer's latest Phase 3 Clinical Trials.  
    Simply name a condition that interests you (for example: Migraine? Leukemia? Pneumonia?)  
    I'll return the most recent trial and get ready for your questions.  
    Ready? Let's get started.""")

    col1, col2 = st.columns([7, 1])

    with col1:
        condition = st.text_input(label="Condition", placeholder="Please enter condition", label_visibility="collapsed")
    with col2:
        st.button("Submit", on_click=set_condition, args=(condition,))

    if "res_for_condition" in st.session_state:
        st.markdown(f"""I have found **{len(st.session_state.res_for_condition)}** trials for **{condition}**.  
                    Please select one from the dropdown list below you would like to find out more about.""")
        trial = st.selectbox(label="Trial", options=st.session_state.res_for_condition, label_visibility="collapsed")
        st.button("Confirm", on_click=set_trial, args=(trial,))

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
    if prompt := st.chat_input(f"What would you like to ask about "
                               f"{st.session_state.current_trial.split(' - ')[0]} ({st.session_state.condition})?"):
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
