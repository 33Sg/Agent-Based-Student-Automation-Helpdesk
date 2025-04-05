import streamlit as st
import  requests
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder

url = "http://127.0.0.1:8000/genova"

st.set_page_config(page_title="Student Admission Helpdesk", page_icon="🎓")
st.markdown("### 🎓 Automated Helpdesk Support")
st.write("This system helps in admission queries, document verification, loan-related queries, and more.")
st.markdown("#### AI Chatbot for your queries")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "bot", "content": "Hi! How can I assist you?"}]

for msg in st.session_state.messages:
    if msg["role"] == "bot":
        with st.chat_message("assistant"):
            st.write(msg["content"])
            #formatted_response = str(msg["content"]).replace('\n', '') 
            #print(formatted_response)
            #st.markdown(formatted_response, unsafe_allow_html=True)
    else:
        with st.chat_message("user"):
            st.write(msg["content"])

uploaded_file = st.file_uploader("📤", type=["pdf", "docx", "doc"], label_visibility="collapsed", key="uploader_small")
user_input = st.chat_input("Type your query...") 

if uploaded_file!=None and user_input!=None:
    st.session_state.messages.append({"role": "bot", "content": f"Your file '{uploaded_file.name}' has been uploaded and is being processed."})
    st.session_state.messages.append({"role": "user", "content": user_input})
    multipart_data = MultipartEncoder(
    fields={
        "promptt": json.dumps({"prompt": user_input}),
        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
    })
    headers = {"Content-Type": multipart_data.content_type}
    bot_response =  requests.post(url, data=multipart_data, headers=headers).json()
    st.session_state.messages.append({"role": "bot", "content": bot_response})
    st.rerun()
elif user_input!=None:
    st.session_state.messages.append({"role": "user", "content": user_input})
    multipart_data = MultipartEncoder(
    fields={
        "promptt": json.dumps({"prompt": user_input})
    })
    headers = {"Content-Type": multipart_data.content_type}
    bot_response =  requests.post(url, data=multipart_data, headers=headers).json()[1:-1].replace('\\n','\n')
    print(bot_response,type(bot_response))
    st.session_state.messages.append({"role": "bot", "content": bot_response})
    st.rerun()