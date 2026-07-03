import re

APP_PATH = "Streamlit/App.py"

with open(APP_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject CSS for radio blobs
css_blob = """
/* Sidebar Radio Button styling to look like blobs */
[data-testid="stSidebar"] div[role="radiogroup"] > label {
    background-color: transparent;
    padding: 12px 20px;
    border-radius: 12px;
    margin-bottom: 8px;
    transition: all 0.2s ease;
    cursor: pointer;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background-color: #f0f4f8;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
    background-color: #e8f0fe !important;
    border-left: 5px solid #1456AD;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] p {
    font-weight: 800 !important;
    color: #1456AD !important;
}
/* Hide the actual radio circle */
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
"""
content = content.replace("</style>", css_blob + "\n</style>")

# 2. Add chat_history to _init_state
init_state_marker = '"soft_conflicts": [],\n    }'
if init_state_marker in content:
    content = content.replace(init_state_marker, '"soft_conflicts": [],\n        "chat_history": [{"role": "assistant", "content": "Hi! I am the ASCS AI Assistant. How can I help you today?"}],\n    }')

# 3. Replace right_col content
# We will find everything inside `with right_col:` until `with main_col:`

start_right_col = 'with right_col:\n'
end_right_col = 'with main_col:\n'

new_right_col = """with right_col:
    st.markdown("### ✨ AI Assistant")
    
    st.markdown("<p style='font-size:0.9rem; color:#666;'><strong>Quick Actions:</strong></p>", unsafe_allow_html=True)
    qa1, qa2 = st.columns(2)
    if qa1.button("🔍 Scan Conflicts", use_container_width=True):
        st.session_state.chat_history.append({"role": "user", "content": "Please scan the schedule for any conflicts."})
        st.session_state.chat_history.append({"role": "assistant", "content": "Scanning complete. ✅ I found 0 critical conflicts. However, there are 2 soft conflicts regarding teacher back-to-back classes."})
        st.rerun()
    if qa2.button("💡 AI Suggestions", use_container_width=True):
        st.session_state.chat_history.append({"role": "user", "content": "Generate AI suggestions for the unassigned subjects."})
        st.session_state.chat_history.append({"role": "assistant", "content": "Here are my top suggestions:\\n\\n- Assign **Innovation Management** to **Osabel** (Sat 07:00-10:00, Rm 101).\\n\\n⚠️ *Note: This will cause an overload for Osabel.*"})
        st.rerun()
        
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    chat_container = st.container(height=600)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    if prompt := st.chat_input("Ask the AI Assistant..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": f"I understand you want to: '{prompt}'. I am a demonstration bot, but I will execute this command in the final version!"})
        st.rerun()

"""

if start_right_col in content and end_right_col in content:
    idx_start = content.find(start_right_col)
    idx_end = content.find(end_right_col)
    
    content = content[:idx_start] + new_right_col + content[idx_end:]

with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("Successfully applied Phase 2 UI updates to App.py")
