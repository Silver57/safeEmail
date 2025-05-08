import streamlit as st
import re
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SMTP Configuration
smtplib.SMTP('smtp.sapo.pt', 587)
SMTP_USERNAME = "senhor.frogs.racing@sapo.pt"
SMTP_PASSWORD = "Nazare2024!"

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
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'inbox'  # Default view
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
        emails_df = pd.read_csv('emails.csv')
        # Add is_trash column if it doesn't exist
        if 'is_trash' not in emails_df.columns:
            emails_df['is_trash'] = False
            emails_df.to_csv('emails.csv', index=False)
        # Add is_draft column if it doesn't exist
        if 'is_draft' not in emails_df.columns:
            emails_df['is_draft'] = False
            emails_df.to_csv('emails.csv', index=False)
        return emails_df
    except:
        return pd.DataFrame(columns=['from', 'to', 'subject', 'date', 'content', 'status', 'is_trash', 'is_draft'])

def move_to_trash(email_id):
    emails_df = load_emails()
    if email_id in emails_df.index:
        emails_df.at[email_id, 'is_trash'] = True
        emails_df.to_csv('emails.csv', index=False)
        st.session_state.selected_email = None
        st.rerun()

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

def display_email_detail(email, email_id, show_trash_button=False):
    st.markdown(f'''
    <div class="email-detail-box">
        <h2 style="margin-bottom: 0.2em;">{email['subject']}</h2>
        <div style="color:#b0b8c1; margin-bottom: 0.5em;">From: <b>{email['from']}</b> | To: <b>{email['to']}</b> | <span style="float:right">{email['date']}</span></div>
        <div style="margin-top: 1em; font-size: 1.1em;">{email['content']}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if show_trash_button:
            if st.button("🗑️ Move to Trash", key=f"trash_{email_id}"):
                move_to_trash(email_id)
    with col2:
        if st.button("✉️ Respond", key=f"respond_{email_id}"):
            st.session_state.compose_data = {
                'to': email['from'],
                'subject': f"Re: {email['subject']}",
                'content': f"\n\nOn {email['date']}, {email['from']} wrote:\n{email['content']}"
            }
            st.session_state.current_view = 'compose'
            st.rerun()

def save_draft(to_email, subject, content):
    emails_df = load_emails()
    new_draft = {
        'from': st.session_state.current_user,
        'to': to_email,
        'subject': subject,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'content': content,
        'status': 'draft',
        'is_trash': False,
        'is_draft': True
    }
    emails_df = pd.concat([emails_df, pd.DataFrame([new_draft])], ignore_index=True)
    emails_df.to_csv('emails.csv', index=False)
    st.success("Draft saved successfully!")
    st.session_state.current_view = 'drafts'
    st.rerun()

def send_email(to_email, subject, content):
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add body
        msg.attach(MIMEText(content, 'plain'))

        # Create SMTP session
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Enable TLS
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def compose_email():
    st.markdown("### ✍️ Write New Email")
    
    # Get pre-filled data if available
    compose_data = st.session_state.get('compose_data', {})
    to_email = st.text_input("To:", value=compose_data.get('to', ''))
    subject = st.text_input("Subject:", value=compose_data.get('subject', ''))
    content = st.text_area("Message:", value=compose_data.get('content', ''), height=200)
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("Send", key="send_email"):
            if to_email and subject and content:
                # Send actual email
                success, message = send_email(to_email, subject, content)
                if success:
                    st.success(message)
                    # Save to sent items
                    emails_df = load_emails()
                    new_email = {
                        'from': SMTP_USERNAME,
                        'to': to_email,
                        'subject': subject,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'content': content,
                        'status': 'sent',
                        'is_trash': False,
                        'is_draft': False
                    }
                    emails_df = pd.concat([emails_df, pd.DataFrame([new_email])], ignore_index=True)
                    emails_df.to_csv('emails.csv', index=False)
                    
                    # Clear compose data
                    if 'compose_data' in st.session_state:
                        del st.session_state.compose_data
                    st.session_state.current_view = 'inbox'
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please fill in all fields!")
    with col2:
        if st.button("Save Draft", key="save_draft"):
            save_draft(to_email, subject, content)
            # Clear compose data
            if 'compose_data' in st.session_state:
                del st.session_state.compose_data
    with col3:
        if st.button("Cancel", key="cancel_email"):
            # Clear compose data
            if 'compose_data' in st.session_state:
                del st.session_state.compose_data
            st.session_state.current_view = 'inbox'
            st.rerun()

def inbox_page():
    # Sidebar
    with st.sidebar:
        st.title("📧 Menu")
        st.markdown("---")
        
        if st.button("✉️ Compose New Email", key="compose_button", use_container_width=True):
            st.session_state.current_view = 'compose'
            st.rerun()
        
        st.markdown("### 📁 Folders")
        if st.button("📥 Inbox", use_container_width=True):
            st.session_state.current_view = 'inbox'
            st.session_state.selected_email = None
            st.rerun()
        if st.button("📤 Sent", use_container_width=True):
            st.session_state.current_view = 'sent'
            st.session_state.selected_email = None
            st.rerun()
        if st.button("📝 Drafts", use_container_width=True):
            st.session_state.current_view = 'drafts'
            st.session_state.selected_email = None
            st.rerun()
        if st.button("🗑️ Trash", use_container_width=True):
            st.session_state.current_view = 'trash'
            st.session_state.selected_email = None
            st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    # Main content
    if st.session_state.current_view == 'compose':
        compose_email()
    else:
        emails_df = load_emails()
        user_email = st.session_state.current_user
        
        # Filter emails based on view
        non_trash_emails = emails_df[~emails_df['is_trash'].fillna(False)]
        received_emails = non_trash_emails[non_trash_emails['to'] == user_email].sort_values('date', ascending=False)
        sent_emails = non_trash_emails[non_trash_emails['from'] == user_email].sort_values('date', ascending=False)
        trashed_emails = emails_df[emails_df['is_trash'].fillna(False)].sort_values('date', ascending=False)
        draft_emails = non_trash_emails[non_trash_emails['is_draft'].fillna(False)].sort_values('date', ascending=False)
        
        # Display content based on current view
        if st.session_state.current_view == 'inbox':
            st.title("📥 Inbox")
            # For demo, all received emails are unread except the first one
            unread_ids = set(received_emails.index[1:]) if len(received_emails) > 1 else set()
            selected_id = st.session_state.selected_email
            col1, col2 = st.columns([2, 3])
            with col1:
                display_email_list(received_emails, selected_id, unread_ids, list_type='received')
            with col2:
                if selected_id is not None and selected_id in emails_df.index:
                    display_email_detail(emails_df.loc[selected_id], selected_id, show_trash_button=True)
                else:
                    st.markdown('<div style="color:#b0b8c1; font-size:1.2em; margin-top:2em;">Select an email to read it here.</div>', unsafe_allow_html=True)
        
        elif st.session_state.current_view == 'sent':
            st.title("📤 Sent Emails")
            selected_id = st.session_state.selected_email
            col1, col2 = st.columns([2, 3])
            with col1:
                display_email_list(sent_emails, selected_id, list_type='sent')
            with col2:
                if selected_id is not None and selected_id in emails_df.index:
                    display_email_detail(emails_df.loc[selected_id], selected_id, show_trash_button=False)
                else:
                    st.markdown('<div style="color:#b0b8c1; font-size:1.2em; margin-top:2em;">Select an email to read it here.</div>', unsafe_allow_html=True)
        
        elif st.session_state.current_view == 'drafts':
            st.title("📝 Drafts")
            selected_id = st.session_state.selected_email
            col1, col2 = st.columns([2, 3])
            with col1:
                display_email_list(draft_emails, selected_id, list_type='drafts')
            with col2:
                if selected_id is not None and selected_id in emails_df.index:
                    display_email_detail(emails_df.loc[selected_id], selected_id, show_trash_button=False)
                else:
                    st.markdown('<div style="color:#b0b8c1; font-size:1.2em; margin-top:2em;">Select a draft to view it here.</div>', unsafe_allow_html=True)
        
        elif st.session_state.current_view == 'trash':
            st.title("🗑️ Trash")
            selected_id = st.session_state.selected_email
            col1, col2 = st.columns([2, 3])
            with col1:
                display_email_list(trashed_emails, selected_id, list_type='trash')
            with col2:
                if selected_id is not None and selected_id in emails_df.index:
                    display_email_detail(emails_df.loc[selected_id], selected_id, show_trash_button=False)
                else:
                    st.markdown('<div style="color:#b0b8c1; font-size:1.2em; margin-top:2em;">Select an email to view it here.</div>', unsafe_allow_html=True)

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