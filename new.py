import streamlit as st
import pyrebase
import pandas as pd
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    if "firebase_credentials" in st.secrets:
        # Parse the JSON string from secrets
        cred_dict = json.loads(st.secrets["firebase_credentials"])
        cred = credentials.Certificate(cred_dict)
    else:
        # Fallback to local file
        CREDENTIALS_PATH = "firebase_credentials.json"
        cred = credentials.Certificate(CREDENTIALS_PATH)
    
    firebase_admin.initialize_app(cred)
db = firestore.client()  # Use Firestore

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyBCayMJMnvbmu5QTmduQAWbFvQ4AtkyOM0",
    "authDomain": "tut1-3e7f8.firebaseapp.com",
    "projectId": "tut1-3e7f8",
    "storageBucket": "tut1-3e7f8.firebasestorage.app",
    "messagingSenderId": "725847647177",
    "appId": "1:725847647177:web:bdd902edcff0133dc73e18",
    "measurementId": "G-KFWE1TRETH",
    "databaseURL": "",  # Not needed for Firestore
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Streamlit App
st.title("Stock Data Dashboard")

# Authentication
choice = st.sidebar.selectbox("Login/Signup", ["Login", "Sign Up"])

if choice == "Login":
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.success("Logged in successfully!")
            st.session_state.user = user  # Store user in session state
        except Exception as e:
            st.error(f"Login failed: {e}")

elif choice == "Sign Up":
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Sign Up"):
        try:
            user = auth.create_user_with_email_and_password(email, password)
            st.success("Account created successfully! Please log in.")
        except Exception as e:
            st.error(f"Sign up failed: {e}")

# Logout Button
if "user" in st.session_state:
    if st.sidebar.button("Logout"):
        del st.session_state.user  # Clear the user session
        st.success("Logged out successfully!")
        st.experimental_rerun()  # Refresh the app to reflect logout

# Display Data (if logged in)
if "user" in st.session_state:
    st.write("Welcome to the app!")

    # Fetch all dates from the flagged_stocks collection
    try:
        flagged_stocks_ref = db.collection("flagged_stocks_new").stream()
        dates = [doc.id for doc in flagged_stocks_ref]  # Get all dates

        if dates:
            # Ask the user to select a date
            selected_date = st.selectbox("Select a Date", dates)

            # Fetch flagged stocks for the selected date
            flagged_stocks_doc = db.collection("flagged_stocks_new").document(selected_date).get()
            if flagged_stocks_doc.exists:
                flagged_stocks = flagged_stocks_doc.to_dict().get("SYMBOL", "").split(", ")

                if flagged_stocks:
                    st.write(f"### Flagged Stocks on {selected_date}")

                    # Display flagged stocks as clickable buttons
                    selected_stock = st.radio("Select a Stock", flagged_stocks)

                    # Fetch and display daily data for the selected stock
                    if selected_stock:
                        st.write(f"#### Data for {selected_stock}")
                        
                        # Add time period selection
                        time_period = st.radio("Select Time Period", ["Daily", "Monthly"], horizontal=True)
                        
                        # Fetch data for the selected stock
                        stock_doc_ref = db.collection("testblock_phase2").document(selected_stock)
                        stock_doc = stock_doc_ref.get()
                        
                        if time_period == "Daily":
                            data = stock_doc.to_dict().get("daily_data", {})
                            freq_label = "Daily"
                        else:
                            data = stock_doc.to_dict().get("monthly_data", {})
                            freq_label = "Monthly"
                        if data:
                            st.write("##### Raw Data")
                            st.write(selected_stock)  # Display raw data
                            df = pd.DataFrame.from_dict(data, orient='index')
                            df.index = pd.to_datetime(df.index)
                            df = df.sort_index()
                            # Format the display based on time period
                            if time_period == "Monthly":
                                df.index = df.index.strftime('%Y-%m')
                            st.write("##### Data Table")
                            st.dataframe(df)  # Display data in a table
                        else:
                            st.write("No data found for the selected stock.")
                else:
                    st.write("No flagged stocks found for the selected date.")
            else:
                st.write("No data found for the selected date.")
        else:
            st.write("No flagged stocks found in the database.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
