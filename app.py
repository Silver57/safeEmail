import streamlit as st
import re
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="SafeEmail - Login",
    page_icon="🔒",
    layout="wide"
)

# Custom CSS for dark, high-contrast, modern inbox style
st.markdown("""
    <style>
    body, .main, .block-container {
        background-color: #181c1f !important;
        color: #f5f6fa !important;
    }
    .stApp {
        background-color: #181c1f !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #2d333b;
        color: #f5f6fa;
        padding: 10px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 1.1em;
        margin-bottom: 8px;
        text-align: left;
    }
    .stButton>button.selected {
        background: #2962ff !important;
        color: #fff !important;
    }
    .stButton>button:hover {
        background-color: #444c56;
    }
    .sidebar .sidebar-content, .css-1d391kg, .css-1lcbmhc {
        background-color: #23272b !important;
        color: #f5f6fa !important;
    }
    .email-list {
        background: #23272b;
        border-radius: 10px;
        padding: 0;
        margin-bottom: 20px;
    }
    .email-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #2196f3;
        border-radius: 50%;
        margin-right: 10px;
        margin-bottom: 2px;
    }
    .email-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .email-sender {
        font-weight: bold;
        font-size: 1.1em;
        color: #fff;
    }
    .email-subject {
        font-size: 1.05em;
        color: #f5f6fa;
        font-weight: 500;
    }
    .email-preview {
        color: #b0b8c1;
        font-size: 0.98em;
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 80vw;
    }
    .email-time {
        color: #b0b8c1;
        font-size: 0.95em;
        margin-left: 16px;
        min-width: 60px;
        text-align: right;
    }
    .compose-button {
        background-color: #ff9800 !important;
        color: white !important;
        font-size: 1.2em !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        border-radius: 8px !important;
    }
    .compose-button:hover {
        background-color: #f57c00 !important;
    }
    .email-detail-box {
        background: #23272b;
        border-radius: 10px;
        padding: 24px;
        margin-top: 10px;
        color: #fff;
        border: 1px solid #2d333b;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'show_compose' not in st.session_state:
    st.session_state.show_compose = False
if 'selected_email' not in st.session_state:
    st.session_state.selected_email = None

# Mock database
USERS = {
    "test@example.com": "password123",
    "test@parent.com": "password123"
}

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 8

def login(email, password):
    st.write("email:", email)
    st.write("users:", USERS)
    if email in USERS and USERS[email] == password:
        st.session_state.authenticated = True
        st.session_state.current_user = email
        return True
    return False

def register(email, password):
    if email in USERS:
        return False, "Email already registered"
    if not validate_email(email):
        return False, "Invalid email format"
    if not validate_password(password):
        return False, "Password must be at least 8 characters long"
    
    USERS[email] = password
    return True, "Registration successful"

def load_emails():
    try:
        return pd.read_csv('emails.csv')
    except:
        return pd.DataFrame(columns=['from', 'to', 'subject', 'date', 'content', 'status'])

def display_email_list(emails, selected_id=None, unread_ids=None, list_type='received'):
    for idx, email in emails.iterrows():
        is_unread = unread_ids and idx in unread_ids
        is_selected = selected_id == idx
        # Use emoji for unread dot
        dot = "🔵 " if is_unread and list_type == 'received' else ""
        # Format the button label as a single string
        btn_label = (
            f"{dot}"
            f"{email['from']}  |  {email['date']}\n"
            f"{email['subject']}\n"
            f"{email['content'][:60]}{'...' if len(email['content']) > 60 else ''}"
        )
        btn_key = f"email-btn-{idx}-{list_type}"
        # Highlight selected button with a different color using Streamlit's style
        if st.button(btn_label, key=btn_key, use_container_width=True):
            st.session_state.selected_email = idx

def display_email_detail(email):
    st.markdown(f'''
    <div class="email-detail-box">
        <h2 style="margin-bottom: 0.2em;">{email['subject']}</h2>
        <div style="color:#b0b8c1; margin-bottom: 0.5em;">From: <b>{email['from']}</b> | To: <b>{email['to']}</b> | <span style="float:right">{email['date']}</span></div>
        <div style="margin-top: 1em; font-size: 1.1em;">{email['content']}</div>
    </div>
    ''', unsafe_allow_html=True)

def compose_email():
    st.markdown("### ✍️ Write New Email")
    to_email = st.text_input("To:")
    subject = st.text_input("Subject:")
    content = st.text_area("Message:", height=200)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Send", key="send_email"):
            if to_email and subject and content:
                st.success("Email sent successfully!")
                st.session_state.show_compose = False
                st.rerun()
            else:
                st.error("Please fill in all fields!")
    with col2:
        if st.button("Cancel", key="cancel_email"):
            st.session_state.show_compose = False
            st.rerun()

def inbox_page():
    # Sidebar
    with st.sidebar:
        st.title("📧 Menu")
        st.markdown("---")
        
        if st.button("✉️ Compose New Email", key="compose_button", use_container_width=True):
            st.session_state.show_compose = True
            st.rerun()
        
        st.markdown("### 📁 Folders")
        st.button("📥 Inbox", use_container_width=True)
        st.button("📤 Sent", use_container_width=True)
        st.button("📝 Drafts", use_container_width=True)
        st.button("🗑️ Trash", use_container_width=True)
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    # Main content
    if st.session_state.show_compose:
        compose_email()
    else:
        st.title("📥 Your Inbox")
        emails_df = load_emails()
        user_email = st.session_state.current_user
        received_emails = emails_df[emails_df['to'] == user_email].sort_values('date', ascending=False)
        sent_emails = emails_df[emails_df['from'] == user_email].sort_values('date', ascending=False)
        # For demo, all received emails are unread except the first one
        unread_ids = set(received_emails.index[1:]) if len(received_emails) > 1 else set()
        selected_id = st.session_state.selected_email
        col1, col2 = st.columns([2, 3])
        with col1:
            st.subheader("📨 Received Emails")
            display_email_list(received_emails, selected_id, unread_ids, list_type='received')
            st.subheader("📤 Sent Emails")
            display_email_list(sent_emails, selected_id, list_type='sent')
        with col2:
            if selected_id is not None and selected_id in emails_df.index:
                display_email_detail(emails_df.loc[selected_id])
            else:
                st.markdown('<div style="color:#b0b8c1; font-size:1.2em; margin-top:2em;">Select an email to read it here.</div>', unsafe_allow_html=True)

def parent_dashboard():
    st.title("👨‍👩‍👧‍👦 Parent Dashboard")
    st.markdown("""
    <div style='background:#23272b; padding:2em; border-radius:10px; color:#fff;'>
        <h2>Welcome, Parent!</h2>
        <p>This is your special dashboard. Here you can monitor your child's inbox, set rules, and more features coming soon!</p>
        <ul>
            <li>🔍 View your child's recent emails</li>
            <li>🛡️ Set safety rules</li>
            <li>📊 See activity reports</li>
        </ul>
        <p style='color:#b0b8c1;'>This is a demo parent interface. More features can be added as needed.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

# Main app logic
if not st.session_state.authenticated:
    st.title("🔒 SafeEmail")
    # Create tabs for Login and Register
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        st.header("Login")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if login(login_email, login_password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password")
    with tab2:
        st.header("Register")
        register_email = st.text_input("Email", key="register_email")
        register_password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        if st.button("Register"):
            if register_password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = register(register_email, register_password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
else:
    # Show parent dashboard if email ends with @parent.com
    if st.session_state.current_user and st.session_state.current_user.endswith("@parent.com"):
        parent_dashboard()
    else:
        inbox_page()