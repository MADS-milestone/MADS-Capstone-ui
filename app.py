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
        res_for_condition = [res["nct_id"] + " - \"" + res["brief_title"] + "\"" for res in api_res["detail"]["trials"]]
        st.session_state["res_for_condition"] = res_for_condition
    else:
        st.warning(f"No clinical trials found for {condition}")
        return
    st.session_state["condition"] = condition


def set_trial(trial, profile):
    trial_parts = trial.split(" - ")
    trial_prompt = f"Are you familiar with trial {trial_parts[0]} with brief title: {trial_parts[1]}"
    with st.spinner('Setting ChatBot context...'):
        req.post(f"{st.session_state.api_host}/get_response", json={"query": trial_prompt, "profile": None})
    st.session_state["current_trial"] = trial
    st.session_state["current_profile"] = profile


def reset_trial():
    st.session_state.condition = None
    st.session_state.current_trial = None
    st.session_state.current_profile = None
    st.session_state.res_for_condition = None
    st.session_state.messages = None
    req.get(f"{st.session_state.api_host}/reset_chat")


if "current_trial" not in st.session_state or st.session_state.current_trial is None:
    st.title("UMSI Clinical Trials ChatBot")
    st.markdown("""Get insights into the newest healthcare research.  
    I'm your trusty guide, here to help you explore Pfizer's latest Phase 3 Clinical Trials.  
    Simply name a condition that interests you (for example: Pneumonia)  
    I'll return the most recent trial and get ready for your questions.  
    Ready? Let's get started.""")

    with st.form("condition_form"):
        col1, col2 = st.columns([7, 1])
        with col1:
            condition = st.text_input(label="Condition", placeholder="Please enter condition", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Submit")
        if submitted:
            set_condition(condition)

    if "res_for_condition" in st.session_state and st.session_state.res_for_condition is not None:
        st.markdown(f"I have found **{len(st.session_state.res_for_condition)}** trials for **{condition}**.")
        with st.form("trial_form"):
            trial = st.selectbox(label="Please select one from the dropdown list below you would like to find out more about",
                             options=st.session_state.res_for_condition)
            profile = st.selectbox(label="Select the profile that best describes you",
                               options=["General/layperson", "PhD scientist", "5-year old child"])
            confirmed = st.form_submit_button("Confirm")
            if confirmed:
                set_trial(trial, profile)
                st.rerun()

else:
    st.title("UMSI Clinical Trials ChatBot")
    st.caption("Brought to you by the MADS RAGtime Band")

    response_container = st.container(height=500)
    input_container = st.container()

    # Initialize chat history
    if "messages" not in st.session_state or st.session_state.messages is None:
        st.session_state.messages = []
        init_msg = f"My context is set to:  \n**{st.session_state.current_trial}.**  \nWhat would you like to learn about it?"
        st.session_state.messages.append({"role": "assistant", "content": init_msg})

    with response_container:
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    with input_container:
        # Accept user input
        if prompt := st.chat_input("Your query"):
            with response_container:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                # Display user message in chat message container
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    api_res = req.post(f"{st.session_state.api_host}/get_response",
                                       json={"query": prompt, "profile": st.session_state.current_profile})
                    res = api_res.json()["response"]
                    response = st.write_stream(response_generator(res.replace("\n", "  \n").replace("<br>", "  \n")))
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.button("Reset", use_container_width=True, on_click=reset_trial)

st.caption("For informational purposes only. Not medical advice.")