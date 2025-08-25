# buzzer_app.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pytz

# Set page configuration
st.set_page_config(
    page_title="Quiz Buzzer System",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'buzzer_presses' not in st.session_state:
    st.session_state.buzzer_presses = pd.DataFrame(columns=['Name', 'ID', 'Timestamp', 'Time'])
if 'buzzer_active' not in st.session_state:
    st.session_state.buzzer_active = True
if 'participants' not in st.session_state:
    st.session_state.participants = {}
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Application title and description
st.title("🔔 Quiz Buzzer System")
st.markdown("A real-time buzzer system for quiz events")

# Function to press the buzzer
def press_buzzer():
    if st.session_state.current_user and st.session_state.buzzer_active:
        user_id = st.session_state.current_user
        user_name = st.session_state.participants[user_id]
        current_time = time.time()
        timestamp = datetime.now(pytz.timezone('UTC')).astimezone(pytz.timezone('US/Eastern')).strftime("%H:%M:%S.%f")[:-3]
        
        # Check if user has already pressed the buzzer
        if user_id not in st.session_state.buzzer_presses['ID'].values:
            new_press = pd.DataFrame({
                'Name': [user_name],
                'ID': [user_id],
                'Timestamp': [timestamp],
                'Time': [current_time]
            })
            st.session_state.buzzer_presses = pd.concat([st.session_state.buzzer_presses, new_press], ignore_index=True)
            st.success(f"Buzzer pressed by {user_name} at {timestamp}!")
        else:
            st.warning("You have already pressed the buzzer!")
    elif not st.session_state.buzzer_active:
        st.error("Buzzer is currently disabled!")
    else:
        st.error("Please login first!")

# Function to reset the buzzer
def reset_buzzer():
    st.session_state.buzzer_presses = pd.DataFrame(columns=['Name', 'ID', 'Timestamp', 'Time'])
    st.session_state.buzzer_active = True

# Function to login
def login():
    name = st.session_state.name_input
    id_num = st.session_state.id_input
    
    if name and id_num:
        st.session_state.participants[id_num] = name
        st.session_state.current_user = id_num
        st.success(f"Welcome, {name}!")

# Function to logout
def logout():
    st.session_state.current_user = None

# Sidebar for login and admin functions
with st.sidebar:
    st.header("Participant Login")
    
    if st.session_state.current_user is None:
        with st.form("login_form"):
            st.text_input("Name", key="name_input")
            st.text_input("ID Number", key="id_input")
            st.form_submit_button("Login", on_click=login)
    else:
        user_id = st.session_state.current_user
        user_name = st.session_state.participants[user_id]
        st.success(f"Logged in as: {user_name} (ID: {user_id})")
        st.button("Logout", on_click=logout)
    
    st.divider()
    
    st.header("Admin Controls")
    st.checkbox("Buzzer Active", value=st.session_state.buzzer_active, key="buzzer_active")
    st.button("Reset Buzzer", on_click=reset_buzzer)
    
    st.divider()
    
    st.header("Instructions")
    st.info("""
    1. Enter your name and ID number to login
    2. Press the buzzer when you know the answer
    3. Admin can reset the buzzer for the next question
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
            disabled=not st.session_state.buzzer_active,
            help="Press when you know the answer!"
        )
        
        if not st.session_state.buzzer_active:
            st.error("Buzzer is currently disabled by admin")
    else:
        st.info("Please login from the sidebar to access the buzzer")
    
    st.divider()
    
    st.header("Buzzer Status")
    if st.session_state.current_user:
        user_id = st.session_state.current_user
        if user_id in st.session_state.buzzer_presses['ID'].values:
            press_time = st.session_state.buzzer_presses[
                st.session_state.buzzer_presses['ID'] == user_id
            ]['Timestamp'].values[0]
            st.success(f"You pressed the buzzer at {press_time}")
        else:
            st.info("You haven't pressed the buzzer yet")
    else:
        st.info("Login to see your buzzer status")

with col2:
    st.header("Leaderboard")
    
    if not st.session_state.buzzer_presses.empty:
        # Sort by time and add position
        leaderboard = st.session_state.buzzer_presses.sort_values('Time').copy()
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

# Admin view (only show if no user is logged in or in expanded view)
if st.session_state.current_user is None:
    st.divider()
    st.header("Admin View")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("All Buzzer Presses")
        if not st.session_state.buzzer_presses.empty:
            st.dataframe(st.session_state.buzzer_presses, use_container_width=True)
        else:
            st.info("No buzzer presses recorded")
    
    with col4:
        st.subheader("Participants")
        if st.session_state.participants:
            participants_df = pd.DataFrame([
                {"ID": id, "Name": name} for id, name in st.session_state.participants.items()
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
</style>
""", unsafe_allow_html=True)