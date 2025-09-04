# buzzer_app.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pytz
import hashlib
import sqlite3
import threading

# Set page configuration
st.set_page_config(
    page_title="Quiz Buzzer System",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
def init_db():
    conn = sqlite3.connect('buzzer.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS buzzer_presses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  timestamp TEXT NOT NULL,
                  press_time REAL NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS participants
                 (user_id TEXT PRIMARY KEY,
                  name TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS system_state
                 (key TEXT PRIMARY KEY,
                  value TEXT NOT NULL)''')
    
    # Initialize system state if not exists
    c.execute("INSERT OR IGNORE INTO system_state VALUES ('buzzer_active', 'True')")
    
    conn.commit()
    return conn

# Initialize database
db_conn = init_db()

# Initialize session state variables
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'show_admin_login' not in st.session_state:
    st.session_state.show_admin_login = False

# Admin credentials (in a real app, use environment variables or a secure database)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("quiz123".encode()).hexdigest()  # password: quiz123

# Function to verify admin credentials
def verify_admin(username, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH

# Function to get buzzer state from database
def get_buzzer_state():
    c = db_conn.cursor()
    c.execute("SELECT value FROM system_state WHERE key = 'buzzer_active'")
    result = c.fetchone()
    return result[0] == 'True' if result else True

# Function to set buzzer state in database
def set_buzzer_state(active):
    c = db_conn.cursor()
    c.execute("UPDATE system_state SET value = ? WHERE key = 'buzzer_active'", 
              ('True' if active else 'False',))
    db_conn.commit()

# Function to get all buzzer presses from database
def get_buzzer_presses():
    c = db_conn.cursor()
    c.execute("SELECT name, user_id, timestamp, press_time FROM buzzer_presses ORDER BY press_time")
    return pd.DataFrame(c.fetchall(), columns=['Name', 'ID', 'Timestamp', 'Time'])

# Function to add a buzzer press to the database
def add_buzzer_press(user_id, name, timestamp, press_time):
    c = db_conn.cursor()
    # Check if user has already pressed the buzzer
    c.execute("SELECT COUNT(*) FROM buzzer_presses WHERE user_id = ?", (user_id,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO buzzer_presses (name, user_id, timestamp, press_time) VALUES (?, ?, ?, ?)",
                  (name, user_id, timestamp, press_time))
        db_conn.commit()
        return True
    return False

# Function to reset the buzzer in the database
def reset_buzzer_db():
    c = db_conn.cursor()
    c.execute("DELETE FROM buzzer_presses")
    db_conn.commit()

# Function to add a participant to the database
def add_participant(user_id, name):
    c = db_conn.cursor()
    try:
        c.execute("INSERT INTO participants (user_id, name) VALUES (?, ?)", (user_id, name))
        db_conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Function to get all participants from the database
def get_participants():
    c = db_conn.cursor()
    c.execute("SELECT user_id, name FROM participants")
    return {row[0]: row[1] for row in c.fetchall()}

# Function to press the buzzer
def press_buzzer():
    if st.session_state.current_user and get_buzzer_state():
        user_id = st.session_state.current_user
        c = db_conn.cursor()
        c.execute("SELECT name FROM participants WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result:
            user_name = result[0]
            current_time = time.time()
            timestamp = datetime.now(pytz.timezone('UTC')).astimezone(pytz.timezone('US/Eastern')).strftime("%H:%M:%S.%f")[:-3]
            
            if add_buzzer_press(user_id, user_name, timestamp, current_time):
                st.success(f"Buzzer pressed by {user_name} at {timestamp}!")
            else:
                st.warning("You have already pressed the buzzer!")
    elif not get_buzzer_state():
        st.error("Buzzer is currently disabled!")
    else:
        st.error("Please login first!")

# Function to reset the buzzer
def reset_buzzer():
    reset_buzzer_db()
    st.session_state.buzzer_active = True
    set_buzzer_state(True)

# Function to login participant
def login_participant():
    name = st.session_state.name_input
    id_num = st.session_state.id_input
    
    if name and id_num:
        if add_participant(id_num, name):
            st.session_state.current_user = id_num
            st.success(f"Welcome, {name}!")
        else:
            st.error("This ID is already registered. Please use a different ID.")

# Function to logout participant
def logout_participant():
    st.session_state.current_user = None

# Function to login admin
def login_admin():
    username = st.session_state.admin_username
    password = st.session_state.admin_password
    
    if verify_admin(username, password):
        st.session_state.admin_logged_in = True
        st.session_state.show_admin_login = False
        st.success("Admin login successful!")
    else:
        st.error("Invalid admin credentials")

# Function to logout admin
def logout_admin():
    st.session_state.admin_logged_in = False

# Function to toggle admin login form
def toggle_admin_login():
    st.session_state.show_admin_login = not st.session_state.show_admin_login

# Function to toggle buzzer state
def toggle_buzzer_state():
    set_buzzer_state(st.session_state.buzzer_active)

# Application title and description
st.title("🔔 Multi-Device Quiz Buzzer System")
st.markdown("A real-time buzzer system for quiz events with database support for multiple devices")

# Sidebar for login and admin functions
with st.sidebar:
    st.header("Participant Login")
    
    if st.session_state.current_user is None:
        with st.form("participant_login_form"):
            st.text_input("Name", key="name_input")
            st.text_input("ID Number", key="id_input")
            st.form_submit_button("Login as Participant", on_click=login_participant)
    else:
        c = db_conn.cursor()
        c.execute("SELECT name FROM participants WHERE user_id = ?", (st.session_state.current_user,))
        result = c.fetchone()
        if result:
            user_name = result[0]
            st.success(f"Logged in as: {user_name} (ID: {st.session_state.current_user})")
        st.button("Logout", on_click=logout_participant)
    
    st.divider()
    
    st.header("Admin Access")
    
    if st.session_state.admin_logged_in:
        st.success("Admin logged in")
        st.button("Admin Logout", on_click=logout_admin)
        
        st.subheader("Admin Controls")
        st.checkbox("Buzzer Active", value=get_buzzer_state(), key="buzzer_active", on_change=toggle_buzzer_state)
        st.button("Reset Buzzer", on_click=reset_buzzer)
    else:
        if st.session_state.show_admin_login:
            with st.form("admin_login_form"):
                st.text_input("Admin Username", key="admin_username")
                st.text_input("Admin Password", type="password", key="admin_password")
                st.form_submit_button("Login as Admin", on_click=login_admin)
            st.button("Cancel", on_click=toggle_admin_login)
        else:
            st.button("Admin Login", on_click=toggle_admin_login)
    
    st.divider()
    
    st.header("Instructions")
    st.info("""
    1. Enter your name and ID number to login as participant
    2. Press the buzzer when you know the answer
    3. Admin can login to control the buzzer system
    4. Multiple devices are supported through database
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Buzzer")
    
    if st.session_state.current_user:
        st.button(
            "🔔 PRESS BUZZER", 
            on_click=press_buzzer, 
            use_container_width=True, 
            disabled=not get_buzzer_state(),
            help="Press when you know the answer!"
        )
        
        if not get_buzzer_state():
            st.error("Buzzer is currently disabled by admin")
    else:
        st.info("Please login from the sidebar to access the buzzer")
    
    st.divider()
    
    st.header("Buzzer Status")
    if st.session_state.current_user:
        user_id = st.session_state.current_user
        buzzer_presses = get_buzzer_presses()
        if user_id in buzzer_presses['ID'].values:
            press_time = buzzer_presses[
                buzzer_presses['ID'] == user_id
            ]['Timestamp'].values[0]
            st.success(f"You pressed the buzzer at {press_time}")
        else:
            st.info("You haven't pressed the buzzer yet")
    else:
        st.info("Login to see your buzzer status")

with col2:
    st.header("Leaderboard")
    
    buzzer_presses = get_buzzer_presses()
    if not buzzer_presses.empty:
        # Sort by time and add position
        leaderboard = buzzer_presses.sort_values('Time').copy()
        leaderboard['Position'] = range(1, len(leaderboard) + 1)
        
        # Display leaderboard
        st.dataframe(
            leaderboard[['Position', 'Name', 'Timestamp']],
            hide_index=True,
            use_container_width=True
        )
        
        # Show first place
        first_place = leaderboard.iloc[0]
        st.success(f"🏆 First: {first_place['Name']} at {first_place['Timestamp']}")
    else:
        st.info("No buzzer presses yet")

# Auto-refresh the page every 2 seconds to get latest buzzer presses
st.markdown("""
<meta http-equiv="refresh" content="2">
""", unsafe_allow_html=True)

# Admin view (only show if admin is logged in)
if st.session_state.admin_logged_in:
    st.divider()
    st.header("Admin View")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("All Buzzer Presses")
        buzzer_presses = get_buzzer_presses()
        if not buzzer_presses.empty:
            st.dataframe(buzzer_presses, use_container_width=True)
        else:
            st.info("No buzzer presses recorded")
    
    with col4:
        st.subheader("Participants")
        participants = get_participants()
        if participants:
            participants_df = pd.DataFrame([
                {"ID": id, "Name": name} for id, name in participants.items()
            ])
            st.dataframe(participants_df, use_container_width=True)
        else:
            st.info("No participants yet")

# Add some custom CSS
st.markdown("""
<style>
    .stButton button {
        height: 200px;
        font-size: 32px;
        font-weight: bold;
        border-radius: 10px;
        background-color: #ff4b4b;
        color: white;
    }
    .stButton button:disabled {
        background-color: #cccccc;
        color: #666666;
    }
    .stSuccess {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)
