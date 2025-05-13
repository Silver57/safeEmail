import streamlit as st
import re
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from transformers import pipeline
import openai
from typing import List, Dict

# Initialize sentiment analysis pipeline
@st.cache_resource
def load_sentiment_analyzer():
    return pipeline("sentiment-analysis", model="siebert/sentiment-roberta-large-english")

# Initialize OpenAI client
openai.api_key = st.secrets["OPENAI_API_KEY"]

def analyze_email_sentiment(content):
    try:
        sentiment_analyzer = load_sentiment_analyzer()
        result = sentiment_analyzer(content)
        # Convert sentiment to a score between 0 and 10
        score = float(result[0]['score']) * 10
        print("Sentiment", score)
        if result[0]['label'] == 'NEGATIVE':
            score = 10 - score
        return score
    except Exception as e:
        st.error(f"Error analyzing sentiment: {str(e)}")
        return None

# SMTP Configuration
SMTP_USERNAME = st.secrets["SMTP_USERNAME"]
SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]
SMTP_SERVER = "smtp.sapo.pt"
SMTP_PORT = 587

# Set page config
st.set_page_config(
    page_title="SafeEmail - Login",
    page_icon="🔒",
    layout="wide"
)

# Custom CSS for kid-friendly, modern inbox style
st.markdown("""
    <style>
    body, .main, .block-container {
        background-color: #E8F4FF !important;
        color: #1A365D !important;
    }
    .stApp {
        background-color: #E8F4FF !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #4A90E2;
        color: #FFFFFF;
        padding: 12px;
        border: none;
        border-radius: 12px;
        cursor: pointer;
        font-size: 1.1em;
        margin-bottom: 8px;
        text-align: left;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background-color: #357ABD;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .stButton>button.selected {
        background: #2E86C1 !important;
        color: #fff !important;
    }
    .sidebar .sidebar-content, .css-1d391kg, .css-1lcbmhc {
        background-color: #FFFFFF !important;
        color: #1A365D !important;
        border-right: 2px solid #E8F4FF;
    }
    .email-list {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .email-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #4A90E2;
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
        color: #1A365D;
    }
    .email-subject {
        font-size: 1.05em;
        color: #1A365D;
        font-weight: 500;
    }
    .email-preview {
        color: #4A5568;
        font-size: 0.98em;
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 80vw;
    }
    .email-time {
        color: #4A5568;
        font-size: 0.95em;
        margin-left: 16px;
        min-width: 60px;
        text-align: right;
    }
    .compose-button {
        background-color: #4A90E2 !important;
        color: white !important;
        font-size: 1.2em !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    .compose-button:hover {
        background-color: #357ABD !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15) !important;
    }
    .email-detail-box {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        margin-top: 10px;
        color: #1A365D;
        border: 2px solid #E8F4FF;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    /* Text input styling */
    .stTextInput>div>div>input {
        border-radius: 12px !important;
        border: 2px solid #E8F4FF !important;
        padding: 12px !important;
        background-color: #FFFFFF !important;
        color: #1A365D !important;
    }
    .stTextInput>div>div>input::placeholder {
        color: #718096 !important;
    }
    .stTextArea>div>div>textarea {
        border-radius: 12px !important;
        border: 2px solid #E8F4FF !important;
        padding: 12px !important;
        background-color: #FFFFFF !important;
        color: #1A365D !important;
    }
    .stTextArea>div>div>textarea::placeholder {
        color: #718096 !important;
    }
    /* Form styling */
    .stForm {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    /* Chat message styling */
    .chat-message {
        margin: 10px 0;
        padding: 15px;
        border-radius: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chat-message.user {
        background: #4A90E2;
        color: #FFFFFF;
        margin-left: 20%;
    }
    .chat-message.assistant {
        background: #FFFFFF;
        color: #1A365D;
        margin-right: 20%;
        border: 2px solid #E8F4FF;
    }
    /* Label styling */
    .stMarkdown p {
        color: #1A365D !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #1A365D !important;
    }
    /* Selectbox styling */
    .stSelectbox>div>div>select {
        background-color: #FFFFFF !important;
        color: #1A365D !important;
        border: 2px solid #E8F4FF !important;
        border-radius: 12px !important;
        padding: 8px !important;
    }
    /* Error message styling */
    .stAlert {
        background-color: #FED7D7 !important;
        color: #C53030 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }
    /* Success message styling */
    .stSuccess {
        background-color: #C6F6D5 !important;
        color: #2F855A !important;
        border-radius: 12px !important;
        padding: 12px !important;
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
        # Add sentiment_score column if it doesn't exist
        if 'sentiment_score' not in emails_df.columns:
            emails_df['sentiment_score'] = None
            # Analyze sentiment for existing emails
            for idx, row in emails_df.iterrows():
                if pd.isna(row['sentiment_score']):
                    score = analyze_email_sentiment(row['content'])
                    emails_df.at[idx, 'sentiment_score'] = score
            emails_df.to_csv('emails.csv', index=False)
        return emails_df
    except:
        return pd.DataFrame(columns=['from', 'to', 'subject', 'date', 'content', 'status', 'is_trash', 'is_draft', 'sentiment_score'])

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
    # Create message
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add body
    msg.attach(MIMEText(content, 'plain'))

    try:
        # Create SMTP session
        server = smtplib.SMTP('smtp.sapo.pt', 587)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_email, text)
        server.quit()
        
        # Analyze sentiment
        sentiment_score = analyze_email_sentiment(content)
        
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
            'is_draft': False,
            'sentiment_score': sentiment_score
        }
        emails_df = pd.concat([emails_df, pd.DataFrame([new_email])], ignore_index=True)
        emails_df.to_csv('emails.csv', index=False)
        
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
        try:
            emails_df = load_emails()
            user_email = st.session_state.current_user
            
            # Ensure all required columns exist
            required_columns = ['from', 'to', 'subject', 'date', 'content', 'status', 'is_trash', 'is_draft', 'sentiment_score']
            for col in required_columns:
                if col not in emails_df.columns:
                    emails_df[col] = None
            
            # Filter emails based on view
            non_trash_emails = emails_df[~emails_df['is_trash'].fillna(False)]
            received_emails = non_trash_emails[non_trash_emails['to'].str.lower() == user_email.lower()].sort_values('date', ascending=False)
            sent_emails = non_trash_emails[non_trash_emails['from'].str.lower() == SMTP_USERNAME.lower()].sort_values('date', ascending=False)
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
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check if the emails.csv file exists and has the correct format.")

def get_risk_level(score):
    if score >= 70:
        return "High", "#ff6b6b"
    elif score >= 40:
        return "Medium", "#ffd93d"
    else:
        return "Low", "#4cd137"

def get_chatgpt_response(messages: List[Dict[str, str]]) -> str:
    """
    Get a response from ChatGPT for the Smart Parenting chat.
    """
    try:
        # Add system message with context and guardrails
        system_message = {
            "role": "system",
            "content": """You are a helpful and empathetic parenting assistant focused on digital safety and child development. 
            Your role is to provide guidance while maintaining appropriate boundaries:
            
            1. Always prioritize child safety and wellbeing
            2. Provide evidence-based advice when possible
            3. Be supportive and non-judgmental
            4. Avoid giving medical or legal advice
            5. Encourage professional help when appropriate
            6. Focus on practical, actionable suggestions
            7. Consider age-appropriate recommendations
            8. Emphasize open communication and trust
            9. Promote healthy digital habits
            10. Respect cultural and family differences
            
            Keep responses concise, clear, and focused on the specific question asked."""
        }
        
        # Add system message to the beginning of the conversation
        messages_with_context = [system_message] + messages
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_with_context,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I apologize, but I'm having trouble connecting to my knowledge base right now. Please try again later. Error: {str(e)}"

def parent_dashboard():
    # Sidebar navigation
    with st.sidebar:
        st.title("👨‍👩‍👧‍👦 Parent Dashboard")
        st.markdown("---")
        
        # Navigation buttons with cute icons
        if st.button("📊 Activity Overview", use_container_width=True):
            st.session_state.parent_view = 'overview'
            st.rerun()
        if st.button("❤️ Wellbeing Check", use_container_width=True):
            st.session_state.parent_view = 'wellbeing'
            st.rerun()
        if st.button("🧠 Smart Parenting Helper", use_container_width=True):
            st.session_state.parent_view = 'smart_parenting'
            st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    # Initialize parent view if not set
    if 'parent_view' not in st.session_state:
        st.session_state.parent_view = 'overview'

    # Load email data
    try:
        emails_df = load_emails()
        total_emails = len(emails_df)
        today_emails = len(emails_df[emails_df['date'].str.startswith(datetime.now().strftime('%Y-%m-%d'))])
        
        # Calculate sentiment statistics
        sentiment_scores = emails_df['sentiment_score'].dropna()
        avg_sentiment = sentiment_scores.mean() if not sentiment_scores.empty else 0
        
        # Calculate sentiment distribution
        positive_count = len(sentiment_scores[sentiment_scores >= 7])
        neutral_count = len(sentiment_scores[(sentiment_scores >= 4) & (sentiment_scores < 7)])
        negative_count = len(sentiment_scores[sentiment_scores < 4])
        total_sentiment = len(sentiment_scores)
        
        # Calculate percentages
        positive_pct = (positive_count / total_sentiment * 100) if total_sentiment > 0 else 0
        neutral_pct = (neutral_count / total_sentiment * 100) if total_sentiment > 0 else 0
        negative_pct = (negative_count / total_sentiment * 100) if total_sentiment > 0 else 0
        
        # Calculate trend
        sentiment_trend = "↗️ Improving" if len(sentiment_scores) > 1 and sentiment_scores.iloc[-1] > sentiment_scores.iloc[-2] else "↘️ Declining"
        
        # Calculate risk scores based on sentiment and content
        violence_score = 75 if any('violence' in str(content).lower() for content in emails_df['content']) else 15
        self_harm_score = 45 if any('harm' in str(content).lower() or 'hurt' in str(content).lower() for content in emails_df['content']) else 10
        sexual_score = 15 if any('sexual' in str(content).lower() or 'inappropriate' in str(content).lower() for content in emails_df['content']) else 5
        
    except Exception as e:
        st.error(f"Error loading email data: {str(e)}")
        total_emails = 0
        today_emails = 0
        avg_sentiment = 0
        sentiment_trend = "↘️ Declining"
        positive_pct = 0
        neutral_pct = 0
        negative_pct = 0
        violence_score = 0
        self_harm_score = 0
        sexual_score = 0

    # Main content based on selected view
    if st.session_state.parent_view == 'overview':
        st.title("📊 Activity Overview")
        st.markdown(f"""
        <div style='background:#FFFFFF; padding:2em; border-radius:16px; color:#2C3E50; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
            <h2>📱 Daily Activity</h2>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1em; margin-top: 1em;'>
                <div style='background:#E8F4FF; padding:1.5em; border-radius:12px;'>
                    <h3>📧 Emails</h3>
                    <p>Total: {total_emails}</p>
                    <p>Today: {today_emails}</p>
                </div>
                <div style='background:#E8F4FF; padding:1.5em; border-radius:12px;'>
                    <h3>⏰ Screen Time</h3>
                    <p>Today: 2h 15m</p>
                    <p>Weekly Avg: 1h 45m</p>
                </div>
                <div style='background:#E8F4FF; padding:1.5em; border-radius:12px;'>
                    <h3>🔍 Safety Score</h3>
                    <p>Current: {avg_sentiment:.1f}/10</p>
                    <p>Trend: {sentiment_trend}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif st.session_state.parent_view == 'wellbeing':
        st.title("❤️ Wellbeing Check")
        
        # Create three columns for the modules
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### ⚠️ Safety Check")
            
            # Violence risk
            violence_level, violence_color = get_risk_level(violence_score)
            st.write("**Violence**")
            st.markdown(f"""
            <div style='background:#E8F4FF; height:12px; border-radius:6px; margin:0.5em 0;'>
                <div style='background:{violence_color}; width:{violence_score}%; height:100%; border-radius:6px;'></div>
            </div>
            <span style='color:{violence_color};'>{violence_level} ({violence_score}%)</span>
            """, unsafe_allow_html=True)

            # Self-harm risk
            self_harm_level, self_harm_color = get_risk_level(self_harm_score)
            st.write("**Self-harm**")
            st.markdown(f"""
            <div style='background:#E8F4FF; height:12px; border-radius:6px; margin:0.5em 0;'>
                <div style='background:{self_harm_color}; width:{self_harm_score}%; height:100%; border-radius:6px;'></div>
            </div>
            <span style='color:{self_harm_color};'>{self_harm_level} ({self_harm_score}%)</span>
            """, unsafe_allow_html=True)

            # Sexual content risk
            sexual_level, sexual_color = get_risk_level(sexual_score)
            st.write("**Sexual Content**")
            st.markdown(f"""
            <div style='background:#E8F4FF; height:12px; border-radius:6px; margin:0.5em 0;'>
                <div style='background:{sexual_color}; width:{sexual_score}%; height:100%; border-radius:6px;'></div>
            </div>
            <span style='color:{sexual_color};'>{sexual_level} ({sexual_score}%)</span>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style='background:#FFFFFF; padding:1.5em; border-radius:16px; color:#2C3E50; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height:100%;'>
                <h3>🎭 Communication Style</h3>
                <div style='margin-top:1em;'>
                    <div style='margin-bottom:1em;'>
                        <h4 style='color:#4A90E2; margin-bottom:0.5em;'>Overall Tone</h4>
                        <p style='color:#27AE60;'>• Generally positive and respectful</p>
                        <p style='color:#F39C12;'>• Some instances of frustration</p>
                    </div>
                    <div style='margin-bottom:1em;'>
                        <h4 style='color:#4A90E2; margin-bottom:0.5em;'>Language Patterns</h4>
                        <p>• Formal in academic contexts</p>
                        <p>• Casual with peers</p>
                    </div>
                    <div>
                        <h4 style='color:#4A90E2; margin-bottom:0.5em;'>Key Insights</h4>
                        <p>• Increased formality in recent weeks</p>
                        <p>• Improved conflict resolution</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:        
            st.markdown(f"""
            <div style='background:#FFFFFF; padding:1.5em; border-radius:16px; color:#2C3E50; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height:100%;'>
                <h3>📊 Mood Analysis</h3>
                <div style='margin-top:1em; text-align:center;'>
                    <div style='font-size:2.5em; margin:0.2em 0; color:#4A90E2;'>{avg_sentiment:.1f}</div>
                    <div style='color:#7F8C8D; margin-bottom:1em;'>Overall Mood Score</div>
                    <div style='background:#E8F4FF; height:12px; border-radius:6px; margin:1em 0;'>
                        <div style='background:#4A90E2; width:{avg_sentiment*10}%; height:100%; border-radius:6px;'></div>
                    </div>
                    <div style='text-align:left; margin-top:1em;'>
                        <p>• Positive: {positive_pct:.0f}%</p>
                        <p>• Neutral: {neutral_pct:.0f}%</p>
                        <p>• Negative: {negative_pct:.0f}%</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    elif st.session_state.parent_view == 'smart_parenting':
        st.title("🧠 Smart Parenting Helper")
        st.markdown("""
        <div style='background:#FFFFFF; padding:2em; border-radius:16px; color:#2C3E50; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
            <h2>👨‍👩‍👧‍👦 Parenting Assistant</h2>
            <p style='color:#7F8C8D;'>Ask questions and get tips on how to help your child thrive online and offline.</p>
        </div>
        """, unsafe_allow_html=True)

        # Initialize chat history in session state
        if 'parent_chat_history' not in st.session_state:
            st.session_state.parent_chat_history = [
                {"role": "assistant", "content": "Hello! I'm here to help you with parenting tips and advice. How can I assist you today?"}
            ]

        # Display chat history
        for msg in st.session_state.parent_chat_history:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-message user'><b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-message assistant'><b>Assistant:</b> {msg['content']}</div>", unsafe_allow_html=True)

        # Input for new question
        with st.form(key="parent_chat_form", clear_on_submit=True):
            user_input = st.text_input("Type your question here...", key="parent_chat_input")
            submitted = st.form_submit_button("Send")
            if submitted and user_input.strip():
                # Add parent message
                st.session_state.parent_chat_history.append({"role": "user", "content": user_input.strip()})
                # Get response from ChatGPT
                response = get_chatgpt_response(st.session_state.parent_chat_history)
                st.session_state.parent_chat_history.append({"role": "assistant", "content": response})
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

def display_email(email):
    st.write(f"**From:** {email['from']}")
    st.write(f"**To:** {email['to']}")
    st.write(f"**Subject:** {email['subject']}")
    st.write(f"**Date:** {email['date']}")
    
    # Display sentiment analysis
    if pd.notna(email['sentiment_score']):
        sentiment_score = email['sentiment_score']
        sentiment_color = 'green' if sentiment_score > 0 else 'red' if sentiment_score < 0 else 'gray'
        sentiment_text = 'Positive' if sentiment_score > 0 else 'Negative' if sentiment_score < 0 else 'Neutral'
        st.markdown(f"**Sentiment:** <span style='color:{sentiment_color}'>{sentiment_text} ({sentiment_score:.2f})</span>", unsafe_allow_html=True)
    
    st.write("**Content:**")
    st.write(email['content'])
    
    # Add action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Reply", key=f"reply_{email.name}"):
            st.session_state['reply_to'] = email
            st.session_state['current_page'] = 'compose'
    with col2:
        if st.button("Forward", key=f"forward_{email.name}"):
            st.session_state['forward_email'] = email
            st.session_state['current_page'] = 'compose'
    with col3:
        if st.button("Delete", key=f"delete_{email.name}"):
            move_to_trash(email.name)
            st.success("Email moved to trash!")
            st.experimental_rerun()