import os
import re

APP_PATH = "Streamlit/App.py"

with open(APP_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update CSS
css_addition = """
/* Hide sidebar when collapsed */
[data-testid="collapsedControl"] { display: none !important; }

/* Login Screen Styles */
.login-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 70vh;
}
.login-card {
    background: #fcfcfc;
    padding: 3rem;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    text-align: center;
    width: 350px;
    margin: 0 auto;
}
.login-title {
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    color: #111;
    margin-bottom: 0.5rem;
}
.login-subtitle {
    color: #666;
    font-size: 0.9rem;
    margin-bottom: 2rem;
}
.stTextInput input {
    background-color: #f1f1f1 !important;
    border: none !important;
    border-radius: 8px !important;
}
"""
content = content.replace("</style>", css_addition + "\n</style>")

# 2. Replace Auth and Sidebar logic
# We will find the section starting with `# SIDEBAR — BRANDING & AUTH`
# and ending before `# ROLE-BASED ROUTING`

start_marker = "# ─────────────────────────────────────────────────────────────────────────────\n# SIDEBAR — BRANDING & AUTH"
end_marker = "# ─────────────────────────────────────────────────────────────────────────────\n# ROLE-BASED ROUTING"

new_auth_logic = """# ─────────────────────────────────────────────────────────────────────────────
# AUTH & LOGIN SCREEN
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.access_token:
    st.markdown('''
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header { visibility: hidden; }
        </style>
    ''', unsafe_allow_html=True)
    
    st.markdown('''
    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-title">timetable</div>
            <div class="login-subtitle">Enter Email & Password</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form", clear_on_submit=True):
            uname = st.text_input("Email", placeholder="admin@example.com", label_visibility="collapsed")
            pwd   = st.text_input("Password", type="password", placeholder="••••••••", label_visibility="collapsed")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                # Dummy login for demonstration as per UI request
                st.session_state.access_token = "dummy_token"
                st.session_state.username = uname
                st.session_state.user_role = "admin"
                st.session_state.tenant_id = "local-tenant"
                st.rerun()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN NAVIGATION (SIDEBAR)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="text-align: center; font-family: Montserrat; font-size: 2rem; font-weight: 800; color: #111; margin-bottom: 2rem;">timetable</div>', unsafe_allow_html=True)
    
    page = st.radio("Nav", ["Dashboard", "Manage", "View Schedule"], label_visibility="collapsed")
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.button("Error Log", use_container_width=True)
    if st.button("Generate", use_container_width=True, type="primary"):
        st.session_state.trigger_generate = True
    
    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(st.session_state.username)
    with col2:
        if st.button("🚪", key="logout_btn", help="Logout"):
            st.session_state.access_token = None
            st.rerun()

if st.session_state.access_token and not st.session_state.backend_catalogs_loaded:
    _load_backend_catalogs()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
main_col, right_col = st.columns([3, 1])

with right_col:
    if page == "Dashboard":
        st.markdown('''
        <div style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #eee;">
            <h4 style="margin-top:0;">Schedule Details</h4>
            <hr>
            <p><strong>Unassigned Subjects Overview</strong></p>
            <p style="font-size: 0.9rem; margin-bottom: 0;">Total Subjects: <span style="background:#1456AD; color:white; padding: 2px 6px; border-radius: 4px;">72</span></p>
            <p style="font-size: 0.9rem; margin-bottom: 0;">Assigned by AI: <span style="background:#1456AD; color:white; padding: 2px 6px; border-radius: 4px;">68</span></p>
            <p style="font-size: 0.9rem; margin-bottom: 1rem;">Unassigned: <span style="background:#1456AD; color:white; padding: 2px 6px; border-radius: 4px;">4</span></p>
            
            <div style="background: #FFFBEB; padding: 10px; border-radius: 8px; border-left: 4px solid #F59E0B; margin-bottom: 10px;">
                <strong>Innovation Management</strong><br>
                <span style="font-size:0.8rem; color:#666;">Course: BSEN 1-21 - Units: 3</span>
            </div>
            
            <p style="font-size: 0.9rem; font-weight: bold;">Possible Assignments (AI Suggestions):</p>
            <div style="background: white; border: 1px solid #eee; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                <span style="font-size: 1.2rem;">👨‍🏫</span> <strong>Osabel</strong> <span style="font-size:0.8rem;">(Load: 26/20)</span><br>
                <span style="background:#FEE2E2; color:#991B1B; padding:2px 6px; border-radius:4px; font-size:0.7rem;">Overload</span>
                <span style="background:#FEF3C7; color:#92400E; padding:2px 6px; border-radius:4px; font-size:0.7rem;">Time conflict</span><br>
                <span style="font-size:0.8rem;">🕒 Sat 07:00-10:00 | 📍 101</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

with main_col:
"""

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_auth_logic + content[end_idx:]
else:
    print("Could not find auth markers")
    exit(1)

# Now we need to indent everything after `with main_col:\n` which is from `end_marker` onwards.
# Actually, the string we inserted ends with `with main_col:\n`. The rest of `content` starts with `# ────────────────────────`
# We need to split the remaining content by lines and prepend 4 spaces.

parts = content.split("with main_col:\n")
if len(parts) == 2:
    header = parts[0] + "with main_col:\n"
    body = parts[1]
    
    indented_body = ""
    for line in body.split("\n"):
        if line.strip() == "":
            indented_body += "\n"
        else:
            indented_body += "    " + line + "\n"
            
    content = header + indented_body

# Let's map old page names to new page names in the if statements.
# Old: if page == "📅 Schedule Generator": -> New: if page == "Dashboard":
# Old: elif page == "👥 Faculty Manager": -> New: elif page == "Manage":
# Old: elif page == "📅 My Timetable": -> New: elif page == "View Schedule":

content = content.replace('page == "📅 Schedule Generator"', 'page == "Dashboard"')
content = content.replace('page == "👥 Faculty Manager"', 'page == "Manage"')
content = content.replace('page == "📅 My Timetable"', 'page == "View Schedule"')

# Since the old default was an `else:` for the schedule generator, we should change the condition order.
# The original file had:
# if page == "📅 My Timetable" and is_student...
# elif page == "📅 My Schedule" and is_faculty...
# elif page == "⚙️ Availability Settings" and is_faculty...
# elif page == "👥 Faculty Manager":
# elif page == "🏫 Room Manager":
# elif page == "📚 Subject Manager":
# else: (this was the generator)
# We will just change the `else:` to `elif page == "Dashboard":`
# Wait, changing `else:` might be tricky via replace.
# Let's do regex replace for `else:\n        st.markdown("""\n        <div class="hero-title">ASCS`
# Actually, the original file has:
# else:
#     st.markdown("""
#     <div class="hero-title">ASCS — <span>AI School</span> Scheduler</div>
content = re.sub(r'else:\n\s*st\.markdown\("""\n\s*<div class="hero-title">ASCS', 
                 'elif page == "Dashboard":\n        st.markdown("""\n        <div class="hero-title">ASCS', 
                 content)

with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("Successfully rewrote App.py")
