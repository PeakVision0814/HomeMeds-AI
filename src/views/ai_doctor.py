# src/views/ai_doctor.py
import streamlit as st
from openai import OpenAI
from src.services.ai_service import get_inventory_str_for_ai

def show_ai_doctor():
    st.header("🤖 AI 药剂师")
    if 'api_key' not in st.session_state: st.warning("请在侧边栏设置 API Key"); return
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages: st.chat_message(m["role"]).write(m["content"])
    
    if prompt := st.chat_input("输入症状..."):
        st.session_state.messages.append({"role":"user", "content":prompt})
        st.chat_message("user").write(prompt)
        
        ctx = get_inventory_str_for_ai()
        sys = f"基于库存回答。库存：\n{ctx}"
        
        client = OpenAI(api_key=st.session_state['api_key'], base_url=st.session_state['api_base'])
        try:
            stream = client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role":"system","content":sys},{"role":"user","content":prompt}], 
                stream=True
            )
            resp = st.write_stream(stream)
            st.session_state.messages.append({"role":"assistant", "content":resp})
        except Exception as e:
            st.error(str(e))