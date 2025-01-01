
# Import Libraries
# ---------------------------

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import re
from pathlib import Path
import sqlite3
import io
import numpy as np
import warnings
import hashlib
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from st_aggrid import AgGrid, GridOptionsBuilder


warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(layout="wide")

# Set global text color to black
st.markdown("""
    <style>
    /* Set the default text color to black */
    html, body, [class*="css"]  {
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------
# Session State Initialization
# ---------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = 'Login'  # Start with Login page
if 'reset_password' not in st.session_state:
    st.session_state.reset_password = False  # Flag to check if reset password is active

# ---------------------------
# Password Hashing Function
# ---------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------
# Database Paths
# ---------------------------
home_dir = Path.home()
users_db_path = home_dir / "new" / "users.db"          # Users database
bookmarks_db_path = home_dir / "new" / "bookmarks.db"  # Bookmarks database
login_history_db_path = home_dir / "new" / "login_history.db"  # Login history database



# ---------------------------
# Initialize Users Database
# ---------------------------
def init_users_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# ---------------------------
# Initialize Login History Database
# ---------------------------
def init_login_history_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        login_time DATETIME,
        logout_time DATETIME
    )
    """)
    conn.commit()
    conn.close()

# Call the functions to initialize the databases
init_users_db(users_db_path)
init_login_history_db(login_history_db_path)

# ---------------------------
# User Authentication Functions
# ---------------------------
def authenticate_user(username, password):
    hashed_password = hash_password(password)
    conn = sqlite3.connect(users_db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM users WHERE username = ? AND password = ?
    """, (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(username, email, password):
    hashed_password = hash_password(password)
    conn = sqlite3.connect(users_db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (username, email, password) VALUES (?, ?, ?)
        """, (username, email, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Username already exists

def get_user_email(username):
    conn = sqlite3.connect(users_db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT email FROM users WHERE username = ?
    """, (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_user_password(username, new_password):
    hashed_password = hash_password(new_password)
    conn = sqlite3.connect(users_db_path)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users SET password = ? WHERE username = ?
    """, (hashed_password, username))
    conn.commit()
    conn.close()

# ---------------------------
# Login, Logout, Signup, and Reset Password Functions
# ---------------------------
def record_login(username):
    from datetime import datetime, timedelta, timezone
    import sqlite3

    conn = sqlite3.connect(login_history_db_path)
    cursor = conn.cursor()
    
    # Define IST timezone
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    # Get current time in IST
    now_ist = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')

    # Insert login time as IST
    cursor.execute("""
    INSERT INTO login_history (username, login_time) VALUES (?, ?)
    """, (username, now_ist))
    conn.commit()
    conn.close()


def record_logout(username):
    from datetime import datetime, timedelta, timezone
    import sqlite3

    conn = sqlite3.connect(login_history_db_path)
    cursor = conn.cursor()
    
    # Define IST timezone
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    # Get current time in IST
    now_ist = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')

    # Update logout time as IST
    cursor.execute("""
    UPDATE login_history
    SET logout_time = ?
    WHERE id = (
        SELECT id FROM login_history
        WHERE username = ? AND logout_time IS NULL
        ORDER BY login_time DESC
        LIMIT 1
    )
    """, (now_ist, username))
    conn.commit()
    conn.close()


def login(username, password):
    user = authenticate_user(username, password)
    if user:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.page = 'Home'  # Go to Home after login
        st.success(f"Welcome {username}!")
        record_login(username)  # Record the login event
    else:
        st.error("Invalid Username or Password")

def logout():
    record_logout(st.session_state.username)  # Record the logout event
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.page = 'Login'
    st.success("You have been logged out.")

# Define the allowed users (email-to-username mapping)
allowed_users = {
    "senthil@subasolutions.com": "Senthil",
    "balaji@subasolutions.com": "Balaji",
    "vaidy@subasolutions.com": "Vaidy",
    "headcorporateservice@subasolutions.com": "Arun",
    "sudharshan@subasolutions.com": "Sudharshan",
    "ravi@wiseowlconsulting.in": "Ravi",
    "marketingtl@subasolutions.com": "Shalini",
    "saleswest@subasolutions.com": "Manish Kumar Gupta",
    "mohan@subasolutions.com": "Mohan",
    "saleswest1@subasolutions.com": "Sachin Pawar",
    "businessdevelopment@subasolutions.com": "Krishnakumari",
    "corr1@subasolutions.com": "Vishal",
    "sales1@subasolutions.com": "Thamarai",
    "pm@subasolutions.com": "Prabakar",
    "pscwest@subasolutions.com": "Manoj Lele",
    "salessupport@subasolutions.com": "Sales Support",
    "sales@subasolutions.com": "Rajalakshmi",
    "salesap@subasolutions.com": "Swarnakumar",
    "salescentral@subasolutions.com": "Vivek Todkari",
    "saleseast1@subasolutions.com": "Avi Bhattahcharjee",
    "saleseast@subasolutions.com": "Bapi Das",
    "salesgujarat@subasolutions.com": "Nilesh Jethva",
    "salesnorth1@subasolutions.com": "Pankaj Kumar",
    "salesnorth@subasolutions.com": "Naresh",
    "salessouth2@subasolutions.com": "Kumar",
    "salessouth@subasolutions.com": "Babu",
    "salesup@subasolutions.com": "Rahul Sharma"
}
    

def signup(new_user, new_email, new_password):
    # The modified signup logic
    if new_email not in allowed_users:
        st.error("Registration failed. Your email is not allowed.")
        return

    expected_username = allowed_users[new_email]
    if new_user != expected_username:
        st.error(f"Registration failed. The username must be '{expected_username}' for this email.")
        return

    success = register_user(new_user, new_email, new_password)
    if success:
        st.success("You have successfully created an account.")
        st.info("Go to Login Menu to login")
        st.session_state.page = 'Login'
    else:
        st.error("Registration failed. Username may already exist.")

def reset_password(username, email, new_password):
    stored_email = get_user_email(username)
    if stored_email and stored_email == email:
        update_user_password(username, new_password)
        st.success("Your password has been reset successfully.")
        st.session_state.reset_password = False
        st.session_state.page = 'Login'
    else:
        st.error("Username and email do not match our records.")

# ---------------------------
# Data Loading and Caching Functions
# ---------------------------
@st.cache_data
def load_data(db_path):
    """
    Load and preprocess data from the specified SQLite database.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM sales_reporting_logic", conn)
    conn.close()

    date_columns = [
        'Enquiry Date', 'Created Date', 'Modified Date', 'Closing Date',
        'Last Contact Date', 'Next Followup Date', 'PS Contacted On Date',
        'PS Follow-up On Date', 'PS Closure Date', 'CS Contacted On Date',
        'CS Follow-up On Date', 'CS Closure Date'
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    if 'Flag' not in df.columns:
        df['Flag'] = 'Existing'  # Assuming default as 'Existing'

    return df, date_columns

@st.cache_data
def load_modified_rdb_data(db_path, potential_nos):
    """
    Load and preprocess data from 'modified_rdb.db' based on provided Potential Numbers.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_names = [table[0] for table in tables]

    if not table_names:
        st.error("No tables found in the modified_rdb.db database.")
        conn.close()
        return pd.DataFrame()

    selected_table = table_names[0]

    required_columns = [
        "Potential No.", "Potential Code", "Potential Owner","Executive", "Company Name","Billing City", "Stage", "Created Date",
        "Last Contact Date", "Next Followup Date", "Enquiry Date",
        "Closing Date", "Category", "Full Name","Mobile","Email","Report ID",
        "Description (Potential Details)", "Modified Date", "Region", "Campaign Source", "Lead Source"
    ]

    cursor.execute(f"PRAGMA table_info('{selected_table}')")
    columns_info = cursor.fetchall()
    available_columns = [col[1] for col in columns_info]

    columns_to_select = [col for col in required_columns if col in available_columns]

    if "Potential No." not in columns_to_select:
        st.error(f"Column 'Potential No.' not found in table '{selected_table}'.")
        conn.close()
        return pd.DataFrame()

    columns_str = ', '.join(f'"{col}"' for col in columns_to_select)
    placeholders = ', '.join(['?'] * len(potential_nos))

    query = f"""
    SELECT
        {columns_str}
    FROM
        "{selected_table}"
    WHERE
        "Potential No." IN ({placeholders})
        AND ("Report ID" IS NULL OR TRIM("Report ID") = '')
    """

    try:
        cursor.execute(query, potential_nos)
        rows = cursor.fetchall()

        col_names = [desc[0] for desc in cursor.description]
        df_modified = pd.DataFrame(rows, columns=col_names)

        date_cols = [
            "Last Contact Date", "Next Followup Date", "Enquiry Date",
            "Closing Date", "Modified Date", "Created Date"
        ]
        for col in date_cols:
            if col in df_modified.columns:
                df_modified[col] = pd.to_datetime(df_modified[col], errors='coerce')

        if 'Report ID' in df_modified.columns:
            df_modified.drop(columns=['Report ID'], inplace=True)

        if 'Modified Date' in df_modified.columns:
            df_modified.sort_values(['Potential No.', 'Modified Date'], ascending=[True, False], inplace=True)
            df_modified = df_modified.drop_duplicates(subset='Potential No.', keep='first')

        df_modified.reset_index(drop=True, inplace=True)
        df_modified.index = df_modified.index + 1

        return df_modified
    except Exception as e:
        st.error(f"An error occurred while querying modified_rdb.db: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def load_potential_details(db_path, potential_no):
    """
    Load potential details from 'modified_rdb.db' where DSR Type is NULL.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_names = [table[0] for table in tables]

    if not table_names:
        st.error("No tables found in the modified_rdb.db database.")
        conn.close()
        return pd.DataFrame()

    selected_table = table_names[0]  # Assuming we're using the first table

    required_columns = [
        "Potential No.", "Potential Code","Potential Owner","Billing City", "Executive", "Region", "Campaign Source", "Lead Source",
        "Stage","Probability (%)","Full Name","Mobile","Email", "Category", "Enquiry Date", "Created Date", "Modified Date",
        "Next Followup Date", "Closing Date", "Last Contact Date", "DSR Type"
    ]

    cursor.execute(f"PRAGMA table_info('{selected_table}')")
    columns_info = cursor.fetchall()
    available_columns = [col[1] for col in columns_info]

    columns_to_select = [col for col in required_columns if col in available_columns]

    if "Potential No." not in columns_to_select or "DSR Type" not in columns_to_select:
        st.error(f"Required columns not found in table '{selected_table}'.")
        conn.close()
        return pd.DataFrame()

    columns_str = ', '.join(f'"{col}"' for col in columns_to_select)

    query = f"""
    SELECT
        {columns_str}
    FROM
        "{selected_table}"
    WHERE
        "Potential No." = ?
        AND "DSR Type" IS NULL
    """

    try:
        cursor.execute(query, (potential_no,))
        rows = cursor.fetchall()

        col_names = [desc[0] for desc in cursor.description]
        df_potential = pd.DataFrame(rows, columns=col_names)

        date_cols = [
            "Enquiry Date", "Created Date", "Modified Date",
            "Next Followup Date", "Closing Date", "Last Contact Date"
        ]
        for col in date_cols:
            if col in df_potential.columns:
                df_potential[col] = pd.to_datetime(df_potential[col], errors='coerce')

        if 'Modified Date' in df_potential.columns:
            df_potential.sort_values('Modified Date', ascending=False, inplace=True)
            df_potential = df_potential.iloc[0:1]  # Take the latest modified entry

        df_potential.reset_index(drop=True, inplace=True)

        return df_potential
    except Exception as e:
        st.error(f"An error occurred while querying modified_rdb.db: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def load_dsr_stage_history(db_path, potential_no):
    """
    Load DSR stage history data for a given Potential No.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_names = [table[0] for table in tables]

    if not table_names:
        st.error("No tables found in the database.")
        conn.close()
        return pd.DataFrame()

    selected_table = table_names[0]  # Assuming we're using the first table

    required_columns = ["Created Date", "Original Stage", "New Stage", "Closing Date",
                        "Description (Potential Details)", "Potential No.", "DSR Type"]

    cursor.execute(f"PRAGMA table_info('{selected_table}')")
    columns_info = cursor.fetchall()
    available_columns = [col[1] for col in columns_info]

    columns_to_select = [col for col in required_columns if col in available_columns]

    if "Potential No." not in columns_to_select or "DSR Type" not in columns_to_select:
        st.error(f"Required columns 'Potential No.' and 'DSR Type' not found in table '{selected_table}'.")
        conn.close()
        return pd.DataFrame()

    columns_str = ', '.join(f'"{col}"' for col in columns_to_select)
    query = f"""
    SELECT
        {columns_str}
    FROM
        "{selected_table}"
    WHERE
        "Potential No." = ?
        AND "DSR Type" IS NOT NULL
    """
    try:
        cursor.execute(query, (potential_no,))
        rows = cursor.fetchall()

        col_names = [desc[0] for desc in cursor.description]
        df_dsr = pd.DataFrame(rows, columns=col_names)

        if 'Created Date' in df_dsr.columns:
            df_dsr['Created Date'] = pd.to_datetime(df_dsr['Created Date'], errors='coerce')

        if 'Created Date' in df_dsr.columns:
            df_dsr.sort_values('Created Date', inplace=True)

        if 'Description (Potential Details)' in df_dsr.columns:
            df_dsr.rename(columns={'Description (Potential Details)': 'Description'}, inplace=True)
        else:
            st.warning("'Description (Potential Details)' column not found. Using original 'Description' column if available.")

        columns_to_drop = ['DSR Type', 'Potential No.']
        df_dsr.drop(columns=[col for col in columns_to_drop if col in df_dsr.columns], inplace=True)

        display_columns = ["Created Date", "Original Stage", "New Stage", "Closing Date", "Description"]
        display_columns = [col for col in display_columns if col in df_dsr.columns]
        df_dsr = df_dsr[display_columns]

        df_dsr.reset_index(drop=True, inplace=True)
        df_dsr.index = df_dsr.index + 1

        return df_dsr
    except Exception as e:
        st.error(f"An error occurred while querying the database: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ---------------------------
# Utility Functions
# ---------------------------
def dataframe_to_excel(df, sheet_name='Sheet1', additional_info=None, wrap_text_columns=None):
    """
    Convert a DataFrame to an Excel file with optional additional information.
    """
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    start_row = 0
    if additional_info:
        df_info = pd.DataFrame(additional_info)
        df_info.to_excel(writer, index=False, sheet_name=sheet_name, startrow=start_row)
        start_row += len(df_info) + 1
    df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=start_row)
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    header_format = workbook.add_format({'bold': True, 'bg_color': 'yellow'})
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(start_row, col_num, value, header_format)
    # Adjust column widths
    for idx, col in enumerate(df.columns):
        series = df[col].astype(str)
        max_width = series.map(len).max()
        adjusted_width = min(max_width + 2, 50)
        if wrap_text_columns and col in wrap_text_columns:
            cell_format = workbook.add_format({'text_wrap': True})
            worksheet.set_column(idx, idx, adjusted_width, cell_format)
        else:
            worksheet.set_column(idx, idx, adjusted_width)
    # Freeze the first column in Excel
    worksheet.freeze_panes(start_row + 1, 1)
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def get_stage_number(stage_name):
    match = re.match(r'(\d+)', str(stage_name))
    return int(match.group(1)) if match else float('inf')

def init_bookmarks_db(db_path):
    """
    Initialize the bookmarks database if it doesn't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        potential_no TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def add_bookmark(db_path, potential_no):
    """
    Add a bookmark to the database for the logged-in user with timestamp in IST.
    """
    user = st.session_state.username

    # Get current time in IST
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO bookmarks (user, potential_no, timestamp) VALUES (?, ?, ?)
    """, (user, potential_no, now_ist))
    conn.commit()
    conn.close()


def get_user_bookmarks(db_path):
    """
    Retrieve bookmarks for the logged-in user.
    """
    user = st.session_state.username
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT potential_no, timestamp FROM bookmarks WHERE user = ?
    """, (user,))
    rows = cursor.fetchall()
    conn.close()
    bookmarks = [{'potential_no': row[0], 'timestamp': row[1]} for row in rows]
    return bookmarks

def is_potential_bookmarked(db_path, potential_no):
    """
    Check if a potential is already bookmarked by the logged-in user.
    """
    user = st.session_state.username
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 1 FROM bookmarks WHERE user = ? AND potential_no = ?
    """, (user, potential_no))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def remove_bookmark(db_path, potential_no):
    """
    Remove a bookmark from the database for the logged-in user.
    """
    user = st.session_state.username
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    DELETE FROM bookmarks WHERE user = ? AND potential_no = ?
    """, (user, potential_no))
    conn.commit()
    conn.close()


# ---------------------------
# Display Filters Function
# ---------------------------
def display_filters():
    """
    Display filter options in the Streamlit sidebar.
    """
    st.sidebar.header('FILTER OPTIONS')

    # CSS to adjust the size and font of elements in the sidebar
    st.sidebar.markdown(
        """
        <style>
        /* Set font size to 10px for sidebar elements */
        div[data-testid="stSidebar"] * {
            font-size: 10px !important;
        }
        /* Adjust margins and paddings for selectboxes */
        div[data-testid="stSidebar"] .stSelectbox, div[data-testid="stSidebar"] .stMultiselect {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        div[data-testid="stSidebar"] .stSelectbox > label, div[data-testid="stSidebar"] .stMultiselect > label {
            margin-bottom: 0 !important;
        }
        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"], div[data-testid="stSidebar"] .stMultiselect div[data-baseweb="select"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            min-height: 1.5em !important;
        }
        /* Adjust font size for info text */
        div[data-testid="stSidebar"] .stAlert p {
            font-size: 10px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Retrieve previous filter values
    previous_filters = st.session_state.get('previous_filters', {})

    # 1. Region Filter
    if 'Region' in full_df.columns:
        regions = full_df['Region'].dropna().unique().tolist()
        regions.sort()
        regions.insert(0, 'All')

        username = st.session_state.username

        if username == 'Mohan':
            # Only show 'South' region
            selected_region = 'South'
            st.session_state['selected_region'] = selected_region
            st.sidebar.write(f"Region: {selected_region}")
        elif username == 'Manish Kumar Gupta':
            # Only show 'West' region
            selected_region = 'West'
            st.session_state['selected_region'] = selected_region
            st.sidebar.write(f"Region: {selected_region}")
        else:
            # Allow selecting from all regions
            selected_region = st.sidebar.selectbox('Region', regions, key='selected_region')
    else:
        st.sidebar.error("Column 'Region' not found in the data.")
        selected_region = 'All'

    # 2. Executive Filter
    if 'Executive' in full_df.columns:
        all_executives = full_df['Executive'].dropna().unique().tolist()
        all_executives.sort()
        all_executives.insert(0, 'All')

        # Define special executive lists for Mohan and Manish Kumar Gupta
        special_executives = {
            'Mohan': ['All', 'Mohan', 'Babu', 'Prabakar', 'Swarnakumar', 'Kumar', 'Raji', 'Rajalakshmi', 'Vishal Manohar Mohod'],
            'Manish Kumar Gupta': ['All', 'Manish Kumar Gupta', 'Manoj Lele', 'Nilesh Jathva', 'Sachin Pawar', 'Vivek Ashok Todkari']
        }

        restricted_users = ['Rajalakshmi', 'Ankit Gupta','Avi Bhattahcharjee','Babu','Bapi Das','Krishnakumari','Kumar','Vivek Ashok Todkari','Manoj Kumar','Manoj Lele','Naresh Bharadwaj','Nilesh Jethva','Pankaj Kumar','Prabakar','Rahul Sharma','Sachin Pawar','Swarnakumar','Vishal Manohar Mohod']  # Existing restricted users

        username = st.session_state.username

        if username in special_executives:
            # Set the Executive filter to the special list for the user
            allowed_executives = special_executives[username]
            selected_executive = st.sidebar.selectbox('Executive', allowed_executives, key='selected_executive')
        elif username in restricted_users:
            # Set the Executive filter to the username and prevent changing
            selected_executive = username
            st.sidebar.write(f"Executive: {selected_executive}")
        else:
            selected_executive = st.sidebar.selectbox('Executive', all_executives, key='selected_executive')
    else:
        st.sidebar.error("Column 'Executive' not found in the data.")
        selected_executive = 'All'

    # 3. Potential Code Filter
    if 'Potential Code' in full_df.columns:
        potential_codes = full_df['Potential Code'].dropna().unique().tolist()
        potential_codes.sort()
        potential_codes.insert(0, 'All')
        selected_potential_code = st.sidebar.selectbox('Potential Code', potential_codes, key='selected_potential_code')
    else:
        st.sidebar.error("Column 'Potential Code' not found in the data.")
        selected_potential_code = 'All'

    # 4. Higher Stages Filter
    higher_stages_list = [
        'All',
        '60 - Value Proposition',
        '70 - Demo/Trials',
        '75 - Negotiation/Review',
        '80 - Cancelled',
        '80 - Final Quote',
        '85 - Order confirmed-Awaiting for PO',
        '90 - Purchase order recd.',
        '90 - On Hold',
        '95 - Closed Won-Advance received',
        '100 - Billed'
    ]

    # Change filter title to 'Stage'
    selected_higher_stage = st.sidebar.selectbox('Stage', higher_stages_list, key='selected_higher_stage')

    # 5. Criterion Date Filter
    criterion_options = ['Last Week', 'Current Week', 'Current Month', 'Last Month', 'Current Quarter', 'Current FY', 'Till date', 'Custom']
    selected_criterion = st.sidebar.selectbox(
        'Criterion Date', criterion_options, index=criterion_options.index('Last Week'), key='selected_criterion'
    )

    # 6. Report Filter
    report_options = ['Follow-up', 'Pending', 'Planned','Closure', 'All']
    selected_report = st.sidebar.selectbox(
        'Report', report_options, index=report_options.index('All'), key='selected_report'
    )

    # Store current filter values
    current_filters = {
        'selected_region': selected_region,
        'selected_executive': selected_executive,
        'selected_potential_code': selected_potential_code,
        'selected_higher_stage': selected_higher_stage,
        'selected_criterion': selected_criterion,
        'selected_report': selected_report
    }

    # Update previous filters in session_state
    st.session_state['previous_filters'] = current_filters

    # Compare current filters with previous filters
    if current_filters != previous_filters:
        # Filters or available options have changed, reset selections
        st.session_state['selected_stage'] = None
        st.session_state['selected_columns'] = None
        st.session_state['selected_potential_no'] = None
        #st.info("Selections have been reset due to change in filters.")


# ---------------------------
# Main Application Function
# ---------------------------
def main_app():
    #st.title('SALES REPORTING LOGIC')



    # Sidebar Radio Buttons
    selected_option = st.sidebar.radio('', ['Forms', 'Find Potential', 'Closing Report', 'Bookmarks'], index=0, key='main_option')

    # Database Paths
    db_file_path = home_dir / "new" / "sales_reporting_logic.db"
    modified_rdb_file_path = home_dir / "new" / "modified_rdb.db"
    dsr2rdb_db_path = home_dir / "new" / "dsr2rdb.db"

    if not db_file_path.exists():
        st.error(f"Database file not found at the path: {db_file_path}")
        st.stop()

    # Initialize bookmarks database
    init_bookmarks_db(bookmarks_db_path)

    # Data Loading with Spinner
    with st.spinner('Loading data from database...'):
        global full_df, date_columns
        full_df, date_columns = load_data(db_file_path)

    if selected_option != 'Bookmarks':
        # Apply filters and get the filtered DataFrame
        display_filters()
        filtered_df, start_date, end_date = apply_filters()
        st.session_state['filtered_df'] = filtered_df
        st.session_state['start_date'] = start_date
        st.session_state['end_date'] = end_date
        st.session_state['home_dir'] = home_dir  # Store home_dir in session_state

    if selected_option == 'Forms':
        # Form 1 Execution
        grid_df = form1()
        st.session_state['grid_df_export'] = grid_df.copy()  # Save for export

        # Add horizontal line after Form 1
        st.write('---')

        # Form 2 Execution
        form2()
        # Form 3 Execution
        form3()
    elif selected_option == 'Bookmarks':
        bookmarks()
    elif selected_option == 'Find Potential':
        find_potential()

# ---------------------------
# Apply Filters Function
# ---------------------------
def apply_filters():
    selected_region = st.session_state.get('selected_region', 'All')
    selected_executive = st.session_state.get('selected_executive', 'All')
    selected_potential_code = st.session_state.get('selected_potential_code', 'All')
    selected_higher_stage = st.session_state.get('selected_higher_stage', 'All')
    selected_criterion = st.session_state.get('selected_criterion', 'Till date')
    selected_report = st.session_state.get('selected_report', 'All')

    filtered_df = full_df.copy()

    username = st.session_state.username

    # Define special executive lists for Mohan and Manish Kumar Gupta
    special_executives = {
        'Mohan': ['Mohan', 'Babu', 'Prabakar', 'Swarnakumar', 'Kumar', 'Raji', 'Rajalakshmi', 'Vishal Manohar Mohod'],
        'Manish Kumar Gupta': ['Manish Kumar Gupta', 'Manoj Lele', 'Nilesh Jathva', 'Sachin Pawar', 'Vivek Ashok Todkari']
    }

    restricted_users = ['Rajalakshmi', 'User2', 'User3']  # Existing restricted users

    # Filter based on user roles
    if username in special_executives:
        allowed_executives = special_executives[username]
        if selected_executive != 'All':
            if selected_executive in allowed_executives:
                filtered_df = filtered_df[filtered_df['Executive'] == selected_executive]
            else:
                st.warning(f"Selected executive '{selected_executive}' is not in your allowed list.")
                filtered_df = filtered_df[filtered_df['Executive'] == username]
        else:
            filtered_df = filtered_df[filtered_df['Executive'].isin(allowed_executives)]
    elif username in restricted_users:
        # Force the Executive filter to the username
        filtered_df = filtered_df[filtered_df['Executive'] == username]
    else:
        if selected_executive != 'All':
            filtered_df = filtered_df[filtered_df['Executive'] == selected_executive]
        # If 'All' is selected, no filtering on Executive is applied

    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['Region'] == selected_region]

    if selected_potential_code != 'All':
        filtered_df = filtered_df[filtered_df['Potential Code'] == selected_potential_code]

    today = datetime.today()

    # Initialize variables for displaying date range
    date_info = ""

    if selected_criterion == 'Last Week':
        # Calculate last Sunday
        last_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        # Calculate second last Sunday
        second_last_sunday = last_sunday - timedelta(days=7)
        start_date = datetime.combine(second_last_sunday, datetime.min.time())
        end_date = datetime.combine(last_sunday, datetime.max.time())
        date_info = f"Last Week: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    elif selected_criterion == 'Current Week':
        # Calculate last Sunday
        last_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        # Calculate next Sunday
        next_sunday = last_sunday + timedelta(days=7)
        start_date = datetime.combine(last_sunday, datetime.min.time())
        end_date = datetime.combine(next_sunday, datetime.max.time())
        date_info = f"Current Week: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    elif selected_criterion == 'Current Month':
        start_date = today.replace(day=1)
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month - timedelta(days=1)
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
        date_info = f"Current Month: {start_date.strftime('%B %Y')}"
    elif selected_criterion == 'Last Month':
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        start_date = last_day_previous_month.replace(day=1)
        end_date = last_day_previous_month
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
        date_info = f"Last Month: {start_date.strftime('%B %Y')}"
    elif selected_criterion == 'Current Quarter':
        # Determine the current quarter number (1 to 4)
        quarter = (today.month - 1) // 3 + 1

        # Define mapping of quarters to their starting and ending months
        quarter_months = {
            1: ('January', 'March'),
            2: ('April', 'June'),
            3: ('July', 'September'),
            4: ('October', 'December')
        }

        # Calculate the starting and ending dates of the current quarter
        start_month = 3 * (quarter - 1) + 1
        start_date = datetime(today.year, start_month, 1)
        end_month = start_month + 2
        if end_month == 12:
            end_date = datetime(today.year, 12, 31)
        else:
            end_date = datetime(today.year, end_month + 1, 1) - timedelta(days=1)
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
        start_month_name, end_month_name = quarter_months[quarter]
        date_info = f"Current Quarter: Q{quarter} ({start_month_name} - {end_month_name}) {today.year}"
    elif selected_criterion == 'Current FY':
        fy_start_month = 4
        if today.month >= fy_start_month:
            start_date = datetime(today.year, fy_start_month, 1)
            end_date = datetime(today.year + 1, fy_start_month, 1) - timedelta(days=1)
            fy_year = f"{today.year}-{today.year + 1}"
        else:
            start_date = datetime(today.year - 1, fy_start_month, 1)
            end_date = datetime(today.year, fy_start_month, 1) - timedelta(days=1)
            fy_year = f"{today.year - 1}-{today.year}"
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
        date_info = f"Current Financial Year: {fy_year}"
    elif selected_criterion == 'Till date':
        start_date = None
        end_date = None
        date_info = "All Data"
    elif selected_criterion == 'Custom':
        start_date_input = st.sidebar.date_input('Start Date', value=today - timedelta(days=30), key='start_date_input')
        end_date_input = st.sidebar.date_input('End Date', value=today, key='end_date_input')
        if start_date_input > end_date_input:
            st.sidebar.error("Start Date must be before or equal to End Date.")
            st.stop()
        start_date = datetime.combine(start_date_input, datetime.min.time())
        end_date = datetime.combine(end_date_input, datetime.max.time())
        date_info = f"From: {start_date_input.strftime('%Y-%m-%d')} To: {end_date_input.strftime('%Y-%m-%d')}"
    else:
        start_date = None
        end_date = None
        date_info = "All Data"

    # Display the date information
    st.session_state['date_info'] = date_info

    if start_date is not None and end_date is not None:
        mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        for col in date_columns:
            if col in filtered_df.columns:
                mask |= ((filtered_df[col] >= start_date) & (filtered_df[col] <= end_date))
        filtered_df = filtered_df[mask]

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        st.stop()

    if selected_report != 'All':
        if selected_report == 'Follow-up':
            if start_date is not None and end_date is not None:
                mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                for col in ['Last Contact Date', 'CS Contacted On Date']:
                    if col in filtered_df.columns:
                        mask |= ((filtered_df[col] >= start_date) & (filtered_df[col] <= end_date))
                filtered_df = filtered_df[mask]
            else:
                filtered_df = filtered_df[
                    filtered_df[['Last Contact Date', 'CS Contacted On Date']].notna().any(axis=1)
                ]
        elif selected_report == 'Pending':
            mask = pd.Series([True] * len(filtered_df), index=filtered_df.index)
            for col in ['Last Contact Date', 'CS Contacted On Date']:
                if col in filtered_df.columns:
                    mask &= filtered_df[col].isna()
            filtered_df = filtered_df[mask]
        elif selected_report == 'Planned':
            if start_date is not None and end_date is not None:
                mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                for col in ['Next Followup Date', 'CS Follow-up On Date']:
                    if col in filtered_df.columns:
                        mask |= ((filtered_df[col] >= start_date) & (filtered_df[col] <= end_date))
                filtered_df = filtered_df[mask]
            else:
                filtered_df = filtered_df[
                    filtered_df[['Next Followup Date', 'CS Follow-up On Date']].notna().any(axis=1)
                ]
        
        elif selected_report == 'Closure':
            if start_date is not None and end_date is not None:
                # Ensure date columns are in datetime format
                filtered_df['Closing Date'] = pd.to_datetime(filtered_df['Closing Date'], errors='coerce')
                filtered_df['CS Closure Date'] = pd.to_datetime(filtered_df['CS Closure Date'], errors='coerce')
        
                # Create masks for each date column
                mask_closing_date = (filtered_df['Closing Date'] >= start_date) & (filtered_df['Closing Date'] <= end_date)
                mask_cs_closure_date = (filtered_df['CS Closure Date'] >= start_date) & (filtered_df['CS Closure Date'] <= end_date)
        
                # Combine masks using logical OR
                mask = mask_closing_date | mask_cs_closure_date
        
                # Apply the combined mask
                filtered_df = filtered_df[mask]
            else:
                # Filter rows where either 'Closing Date' or 'CS Closure Date' is not null
                filtered_df = filtered_df[
                    filtered_df[['Closing Date', 'CS Closure Date']].notna().any(axis=1)
                ]        
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        st.stop()

    return filtered_df, start_date, end_date

# ---------------------------
# Form 1 Function
# ---------------------------

def form1():
    filtered_df = st.session_state['filtered_df']
    start_date = st.session_state['start_date']
    end_date = st.session_state['end_date']
    
    # ---------------------------
    # Stage Name Processing
    # ---------------------------
    stage_columns = ['Stage', 'Previous Status Stage', 'Current Status Stage']
    available_stage_columns = [col for col in stage_columns if col in filtered_df.columns]
    if not available_stage_columns:
        st.error("None of the stage columns ('Stage', 'Previous Status Stage', 'Current Status Stage') are found in the data.")
        st.stop()
    else:
        stages = pd.unique(filtered_df[available_stage_columns].values.ravel('K'))
        stages = [stage for stage in stages if pd.notna(stage)]
        stages = list(set(stages))
        stages.sort()

    # ---------------------------
    # Calculating Opening Balance
    # ---------------------------
    opening_balance = filtered_df[filtered_df['Flag'] == 'Existing'].groupby('Previous Status Stage').size().rename('Opening Balance')

    # ---------------------------
    # Initializing the Grid DataFrame
    # ---------------------------
    grid_df = pd.DataFrame({'Stage Name': stages})

    grid_df = grid_df.merge(opening_balance.reset_index(), how='left', left_on='Stage Name', right_on='Previous Status Stage', suffixes=('', '_full'))
    grid_df.drop(columns=['Previous Status Stage'], inplace=True)
    grid_df['Opening Balance'] = grid_df['Opening Balance'].fillna(0).astype(int)

    # ---------------------------
    # Calculating Added (New)
    # ---------------------------
    added_new = filtered_df[filtered_df['Flag'] == 'New'].groupby('Previous Status Stage').size().reindex(stages, fill_value=0)
    grid_df['Added (New)'] = grid_df['Stage Name'].map(added_new).fillna(0).astype(int)

    grid_df['Added (Existing)'] = 0
    grid_df['Moved'] = 0
    grid_df['Dropped'] = 0

    # ---------------------------
    # Processing Dropped Records
    # ---------------------------
    all_records = filtered_df
    total_all_records = len(all_records)

    if total_all_records > 0:
        for _, record in all_records.iterrows():
            prev_stage = record.get('Previous Status Stage')
            curr_stage = record.get('Current Status Stage')

            if pd.isna(prev_stage) and pd.isna(curr_stage):
                continue
            elif prev_stage == curr_stage:
                continue
            elif pd.notna(prev_stage) and curr_stage == '0 - Closed':
                if prev_stage in grid_df['Stage Name'].values:
                    grid_df.loc[grid_df['Stage Name'] == prev_stage, 'Dropped'] += 1
    else:
        st.info("No records to process for Dropped.")

    # ---------------------------
    # Processing Added (Existing) and Moved Records
    # ---------------------------
    existing_records = filtered_df[filtered_df['Flag'] == 'Existing']
    total_existing_records = len(existing_records)

    if total_existing_records > 0:
        for _, record in existing_records.iterrows():
            prev_stage = record.get('Previous Status Stage')
            curr_stage = record.get('Current Status Stage')

            if pd.isna(prev_stage) and pd.isna(curr_stage):
                continue
            elif prev_stage == curr_stage:
                continue
            elif pd.notna(prev_stage) and pd.notna(curr_stage):
                if curr_stage == '0 - Closed':
                    continue
                else:
                    if prev_stage in grid_df['Stage Name'].values:
                        grid_df.loc[grid_df['Stage Name'] == prev_stage, 'Moved'] += 1
                    if curr_stage in grid_df['Stage Name'].values:
                        grid_df.loc[grid_df['Stage Name'] == curr_stage, 'Added (Existing)'] += 1
    else:
        st.info("No existing records to process for Added (Existing) and Moved.")

    # ---------------------------
    # Calculating Closing Balance
    # ---------------------------
    grid_df['Closing Balance'] = (
        grid_df['Opening Balance'] +
        grid_df['Added (New)'] +
        grid_df['Added (Existing)'] -
        grid_df['Moved'] -
        grid_df['Dropped']
    )

    # ---------------------------
    # Sorting Stage Names
    # ---------------------------
    def extract_integer(stage_name):
        if pd.isna(stage_name):
            return float('inf')
        match = re.match(r'(\d+)', str(stage_name))
        return int(match.group(1)) if match else float('inf')

    grid_df['Stage_Number'] = grid_df['Stage Name'].apply(extract_integer)
    grid_df = grid_df.sort_values('Stage_Number').reset_index(drop=True)

    grid_df.index = grid_df.index + 1

    # ---------------------------
    # Numbering Columns
    # ---------------------------
    numbered_columns = {
        'Opening Balance': 'OB',
        'Added (New)': 'Added-New',
        'Added (Existing)': 'Added-Old',
        'Moved': 'Moved',
        'Dropped': 'Dropped',
        'Closing Balance': 'CB'
    }
    grid_df.rename(columns=numbered_columns, inplace=True)
    
    # Store numbered_columns in session_state
    st.session_state['numbered_columns'] = numbered_columns

    # ---------------------------
    # Applying Stage Filter to grid_df
    # ---------------------------
    selected_higher_stage = st.session_state.get('selected_higher_stage', 'All')
    if selected_higher_stage != 'All':
        selected_stage_num = get_stage_number(selected_higher_stage)
        grid_df = grid_df[grid_df['Stage_Number'] >= selected_stage_num]

    # Drop 'Stage_Number' column as it's no longer needed
    grid_df.drop(columns=['Stage_Number'], inplace=True)

    # ---------------------------
    # Excluding Certain Stages
    # ---------------------------
    grid_df = grid_df[~grid_df['Stage Name'].isin([
        '100 - Billed',
        '90 - On Hold',
        '20 - Contact in future No plan at present - Closed',
        '50 - Considering for Used Machine',
        '80 - Cancelled'
    ])]
    
    # ---------------------------
    # Adding Total Row excluding '0 - Closed'
    # ---------------------------
    # Exclude '0 - Closed' when calculating total
    grid_df_no_closed = grid_df[grid_df['Stage Name'] != '0 - Closed']
    total_values = grid_df_no_closed[list(numbered_columns.values())].sum()
    total_row = pd.DataFrame({
        'Stage Name': ['Total'],
        **{col: [total_values[col]] for col in total_values.index}
    }, index=[len(grid_df) + 1])

    grid_df = pd.concat([grid_df, total_row])

    grid_df.reset_index(drop=True, inplace=True)
    grid_df.index = grid_df.index + 1

    # ---------------------------
    # Limiting Displayed Rows to Fit Viewport
    # ---------------------------
    max_visible_rows = 20

    if len(grid_df) > max_visible_rows:
        grid_df_display = grid_df.head(max_visible_rows)
        st.warning(f"Displaying the first {max_visible_rows} of {len(grid_df)} total rows to fit the display without scrolling.")
    else:
        grid_df_display = grid_df

    # ---------------------------
    # Applying Styles to the Grid DataFrame
    # ---------------------------
    # Highlight certain cells based on conditions

    # Create masks for the conditions
    dropped_highlight_mask_pink = (grid_df_display['Stage Name'].isin([
        '80 - Final Quote',
        '85 - Order confirmed-Awaiting for PO',
        '90 - Purchase order recd.'
    ])) & (grid_df_display[numbered_columns['Dropped']] >= 1)

    dropped_highlight_mask_red = (grid_df_display['Stage Name'] == '95 - Closed Won-Advance received') & (grid_df_display[numbered_columns['Dropped']] >= 1)

    added_new_highlight_mask = grid_df_display[numbered_columns['Added (New)']] >= 1

    # Initialize styles DataFrame
    styles_df = pd.DataFrame('', index=grid_df_display.index, columns=grid_df_display.columns)

    # Apply styles based on the masks
    styles_df.loc[dropped_highlight_mask_pink, numbered_columns['Dropped']] = 'background-color: lightpink'
    styles_df.loc[dropped_highlight_mask_red, numbered_columns['Dropped']] = 'background-color: lightcoral'
    styles_df.loc[added_new_highlight_mask, numbered_columns['Added (New)']] = 'background-color: lightgreen'

    # Create the styled DataFrame
    grid_df_display_styled = grid_df_display.style.apply(lambda _: styles_df, axis=None)

    # ---------------------------
    # Displaying the Grid in Form 1
    # ---------------------------
    st.write('### FORM 1: GRID')
    # Mention abbreviations
    st.write("First File Date  - 03/12/2024 -- Second File Date - 30/12/2024")
    st.write(" ")
    st.write("OB - Opening Balance, CB - Closing Balance")
    st.write(grid_df_display_styled)

    # ---------------------------
    # Store Available Options in Session State
    # ---------------------------
    stage_names = grid_df['Stage Name'].unique().tolist()
    if 'Total' in stage_names:
        stage_names.remove('Total')
    st.session_state['available_stage_names'] = stage_names

    column_options = list(numbered_columns.values())
    st.session_state['available_columns'] = column_options

    # ---------------------------
    # Selecting Stage Name and Column within Form 1
    # ---------------------------
    if stage_names:
        default_stage_index = stage_names.index('80 - Final Quote') if '80 - Final Quote' in stage_names else 0

        # Create a row of columns for both dropdowns side by side
        col_stage_sel1, col_stage_sel2, col_col1, col_col2 = st.columns([1,0.1,1,0.1])

        # Place the "Select Stage Name(s)" multiselect in the first set of columns
        with col_stage_sel1:
            selected_stages = st.multiselect(
                'Select Stage Name(s)',
                options=stage_names,
                default=[stage_names[default_stage_index]] if stage_names else [],
                key='selected_stages_form1'
            )
        st.session_state['selected_stages'] = selected_stages

        # Retrieve the selected column from session_state or default to 'CB'
        default_column_index = column_options.index('CB') if 'CB' in column_options else 0

        # Place the "Select Column" selectbox next to the first dropdown
        with col_col1:
            selected_column = st.selectbox(
                'Select Column',
                options=column_options,
                index=default_column_index,
                key='selected_column_form1'
            )
        st.session_state['selected_columns'] = [selected_column]

    else:
        st.warning("No stages available to select.")
        selected_stages = []
        selected_columns = []

    # ---------------------------
    # Download Button for Grid Table in Form 1
    # ---------------------------
    filters_info = {
        'Filters': ['Region', 'Executive', 'Potential Code', 'Stage Filter', 'Criterion Date', 'Report'],
        'Selected': [
            st.session_state.get('selected_region', 'All'),
            st.session_state.get('selected_executive', 'All'),
            st.session_state.get('selected_potential_code', 'All'),
            st.session_state.get('selected_higher_stage', 'All'),
            st.session_state.get('selected_criterion', 'Till date'),
            st.session_state.get('selected_report', 'All')
        ]
    }
    excel_data = dataframe_to_excel(grid_df, sheet_name='Form 1', additional_info=filters_info)

    st.download_button(
        label="Download Grid as Excel",
        data=excel_data,
        file_name='grid_table_form1.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Store grid_df for exporting in Form 3
    st.session_state['grid_df_export'] = grid_df

    # Return grid_df
    return grid_df




# ---------------------------
# Form 2 Function
# ---------------------------
def form2():
    """
    FORM 2:
    1) Displays a list of Potentials based on the Stage and Column selections in Form 1.
    2) Provides an editable “BM” checkbox column using st.data_editor for bookmarking.
    3) Pins the “BM” and “Potential No.” columns at the left side (if supported).
    4) In the multi-sheet DSR Excel download, excludes “enq” or any non-digit prefix from sheet names—only numeric part remains.
    """

    filtered_df = st.session_state['filtered_df']
    st.write('### FORM 2: POTENTIALS LIST')

    # Retrieve user selections and column mappings from session_state
    selected_stages = st.session_state.get('selected_stages', [])
    selected_columns = st.session_state.get('selected_columns', [])
    numbered_columns = st.session_state.get('numbered_columns', {})

    if not selected_stages or not selected_columns:
        st.info("Please select at least one Stage Name and a Column from Form 1.")
        st.write('---')
        return

    existing_records = filtered_df[filtered_df['Flag'] == 'Existing']
    all_records = filtered_df
    potential_nos_set = set()

    # Identify Potential Nos from the user’s stage/column selections
    for selected_column in selected_columns:
        original_column_name = [
            key for key, value in numbered_columns.items()
            if value == selected_column
        ][0]

        if original_column_name == 'Opening Balance':
            potential_nos = filtered_df[
                (filtered_df['Previous Status Stage'].isin(selected_stages)) &
                (filtered_df['Flag'] == 'Existing')
            ]['Potential No.'].unique().tolist()

        elif original_column_name == 'Added (New)':
            potential_nos = filtered_df[
                (filtered_df['Previous Status Stage'].isin(selected_stages)) &
                (filtered_df['Flag'] == 'New')
            ]['Potential No.'].unique().tolist()

        elif original_column_name == 'Added (Existing)':
            potential_nos = existing_records[
                (existing_records['Current Status Stage'].isin(selected_stages)) &
                (~existing_records['Previous Status Stage'].isin(selected_stages))
            ]['Potential No.'].unique().tolist()

        elif original_column_name == 'Moved':
            potential_nos = existing_records[
                (existing_records['Previous Status Stage'].isin(selected_stages)) &
                (~existing_records['Current Status Stage'].isin(selected_stages)) &
                (existing_records['Current Status Stage'] != '0 - Closed')
            ]['Potential No.'].unique().tolist()

        elif original_column_name == 'Dropped':
            potential_nos = all_records[
                (all_records['Previous Status Stage'].isin(selected_stages)) &
                (all_records['Current Status Stage'] == '0 - Closed')
            ]['Potential No.'].unique().tolist()

        elif original_column_name == 'Closing Balance':
            potential_nos = filtered_df[
                (filtered_df['Stage'].isin(selected_stages)) &
                (filtered_df['Flag'] == 'Existing')
            ]['Potential No.'].unique().tolist()
        else:
            potential_nos = []

        potential_nos_set.update([pn for pn in potential_nos if pd.notna(pn)])

    potential_nos_list = list(potential_nos_set)

    if not potential_nos_list:
        st.info("No Potential No. found for the selected Stage(s) and Column.")
        st.write('---')
        return

    st.write(f"Number of unique Potential No.(s) for the selected criteria: **{len(potential_nos_list)}**")

    # Load from modified_rdb.db
    home_dir = st.session_state['home_dir']
    modified_rdb_file_path = home_dir / "new" / "modified_rdb.db"

    if not modified_rdb_file_path.exists():
        st.error(f"Database file not found at: {modified_rdb_file_path}")
        return

    with st.spinner('Loading data from modified_rdb.db...'):
        df_form2 = load_modified_rdb_data(modified_rdb_file_path, potential_nos_list)

    if df_form2.empty:
        st.info("No matching records found in modified_rdb.db for the selected Potential No.(s).")
        st.write('---')
        return

    # Drop columns we don't want
    columns_to_drop = [
        'Description (Potential Details)',
        'Modified Date',
        'Region',
        'Campaign Source',
        'Lead Source'
    ]
    df_form2.drop(columns=[col for col in columns_to_drop if col in df_form2.columns],
                  inplace=True)

    # Convert date columns to date only
    date_columns_form2 = ['Created Date', 'Last Contact Date', 'Next Followup Date', 'Enquiry Date', 'Closing Date']
    for col in date_columns_form2:
        if col in df_form2.columns:
            df_form2[col] = df_form2[col].dt.date

    # Must be logged in to bookmark
    if 'username' not in st.session_state or not st.session_state['username']:
        st.warning("You must be logged in to see and edit bookmarks.")
        st.dataframe(df_form2, use_container_width=True)
        st.write('---')
        return

    username = st.session_state['username']
    bookmarks_db_path = home_dir / "new" / "bookmarks.db"

    # Insert a “BM” column for bookmarking
    bookmark_status = []
    for pn in df_form2['Potential No.']:
        if is_potential_bookmarked(bookmarks_db_path, str(pn)):
            bookmark_status.append(True)
        else:
            bookmark_status.append(False)
    df_form2['BM'] = bookmark_status

    # Reorder columns: 'BM' after 'Potential No.' if you wish
    desired_order = ['Potential No.', 'BM']
    other_cols = [c for c in df_form2.columns if c not in desired_order]
    df_form2 = df_form2[desired_order + other_cols]

    # Build column_config with pinned columns if supported
    column_config = {}
    for col in df_form2.columns:
        if col == 'BM':
            column_config[col] = st.column_config.CheckboxColumn(
                label="BM",
                help="Check to bookmark this Potential. Uncheck to remove bookmark.",
                default=False,
                # locked="left"  # If pinned columns are supported
            )
        elif col == 'Potential No.':
            column_config[col] = st.column_config.Column(
                label="Potential No.",
                disabled=True,
                # locked="left"  # If pinned columns are supported
            )
        else:
            column_config[col] = st.column_config.Column(
                label=col,
                disabled=True
            )

    # Display the data in st.data_editor
    st.write('#### Potential Details:')
    edited_df = st.data_editor(
        df_form2,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        key='form2_data_editor'
    )

    # Detect changes in BM
    changed_rows = (edited_df['BM'] != df_form2['BM'])
    if changed_rows.any():
        changed_potentials = edited_df[changed_rows]
        for idx, row in changed_potentials.iterrows():
            # Potential No. from the new row
            pn = str(row['Potential No.'])
            new_value = row['BM']
            old_value = df_form2.loc[idx, 'BM']  # same row in the old DF
            if new_value != old_value:
                if new_value:
                    add_bookmark(bookmarks_db_path, pn)
                    st.success(f"Bookmarked Potential No. {pn}")
                else:
                    remove_bookmark(bookmarks_db_path, pn)
                    st.warning(f"Removed bookmark for Potential No. {pn}")

        # Update reference
        df_form2['BM'] = edited_df['BM']

    # For Excel download, keep "Potential No." as a column
    selection_info = {
        'Selection': ['Stage Name(s)', 'Column'],
        'Selected': [', '.join(selected_stages), ', '.join(selected_columns)]
    }
    excel_data_form2 = dataframe_to_excel(
        df_form2,
        sheet_name='Form 2',
        additional_info=selection_info
    )
    st.download_button(
        label="Download Form 2 Data as Excel",
        data=excel_data_form2,
        file_name='form2_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # ---------------------------
    # IMPORTANT:
    # Save df_form2 in st.session_state so Form 3 can access it
    # ---------------------------
    st.session_state['df_form2'] = df_form2.copy()  # <--- This ensures Form 3 sees the same DF

    # Optional: Set index for multi-sheet logic
    df_copy = df_form2.copy()
    df_copy.set_index('Potential No.', inplace=True)

    # Multi-sheet DSR export
    dsr_data_dict = {}
    for potential_no in df_copy.index.unique():
        df_dsr = load_dsr_stage_history(modified_rdb_file_path, potential_no)
        if not df_dsr.empty:
            if 'Created Date' in df_dsr.columns:
                df_dsr['Created Date'] = df_dsr['Created Date'].dt.date
            if 'Closing Date' in df_dsr.columns:
                df_dsr['Closing Date'] = pd.to_datetime(df_dsr['Closing Date'], errors='coerce').dt.date
            dsr_data_dict[potential_no] = df_dsr

    if dsr_data_dict:
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        workbook = writer.book
        header_format = workbook.add_format({'bold': True, 'bg_color': 'yellow'})

        for potential_no, df_dsr in dsr_data_dict.items():
            numeric_part = re.sub(r'\D+', '', str(potential_no))
            if not numeric_part:
                numeric_part = 'Sheet1'
            sheet_name = numeric_part[:31]

            df_dsr.to_excel(writer, index=False, sheet_name=sheet_name)
            worksheet = writer.sheets[sheet_name]

            for col_num, col_val in enumerate(df_dsr.columns):
                worksheet.write(0, col_num, col_val, header_format)

            for idx, col in enumerate(df_dsr.columns):
                series = df_dsr[col].astype(str)
                max_width = min(series.map(len).max() + 2, 80)
                if col == 'Description':
                    cell_format = workbook.add_format({'text_wrap': True})
                    worksheet.set_column(idx, idx, max_width, cell_format)
                else:
                    worksheet.set_column(idx, idx, max_width)

            worksheet.freeze_panes(1, 0)

        writer.close()
        processed_data = output.getvalue()

        st.download_button(
            label="Download DSR Data for Potentials as Excel",
            data=processed_data,
            file_name='form2_potentials_dsr_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.info("No DSR data found for the potentials in Form 2.")

    st.write('---')


# ---------------------------
# Form 3 Function
# ---------------------------
def form3():
    """
    FORM 3:
    1) Retrieves the df_form2 DataFrame from st.session_state to get Potential Nos.
    2) Lets user select a Potential No. from that list.
    3) Displays potential details and DSR stage history for the selected Potential No.
    4) Also includes bookmarking (add/remove).
    """

    st.write('### FORM 3: DSR STAGE HISTORY')

    # 1) Ensure that df_form2 is available
    df_form2 = st.session_state.get('df_form2', None)
    if df_form2 is None or df_form2.empty:
        st.info("Please complete Form 2 so that Potential Nos are available for Form 3.")
        return

    # 2) Retrieve Potential Nos from df_form2
    potential_nos_form2 = df_form2['Potential No.'].dropna().unique().tolist()
    potential_nos_form2 = [str(pn) for pn in potential_nos_form2]
    potential_nos_form2.sort()

    if not potential_nos_form2:
        st.info("No Potential Nos available from Form 2.")
        return

    # Default selection if not already in session_state
    if 'selected_potential_no_form3' not in st.session_state or \
       st.session_state['selected_potential_no_form3'] not in potential_nos_form2:
        st.session_state['selected_potential_no_form3'] = potential_nos_form2[0]

    # 3) Let user select Potential No.
    selected_potential_no = st.selectbox(
        'Select Potential No.',
        options=potential_nos_form2,
        key='selected_potential_no_form3'
    )
    st.write(f"Selected Potential No.: **{selected_potential_no}**")

    # 4) Load potential details from DB
    home_dir = st.session_state['home_dir']
    modified_rdb_file_path = home_dir / "new" / "modified_rdb.db"

    if not modified_rdb_file_path.exists():
        st.error(f"Database file not found at the path: {modified_rdb_file_path}")
        return

    with st.spinner('Loading potential details...'):
        df_potential_details = load_potential_details(modified_rdb_file_path, selected_potential_no)

    # 5) Display potential details (if found)
    if not df_potential_details.empty:
        potential_details_columns = [
            'Region', 'Potential Code', 'Billing City',
            'Executive', 'Potential Owner',
            'Campaign Source', 'Lead Source',
            'Stage', 'Probability (%)', 'Category',
            'Full Name', 'Mobile', 'Email',
            'Enquiry Date', 'Created Date', 'Modified Date',
            'Next Followup Date', 'Closing Date', 'Last Contact Date'
        ]
        existing_cols = [c for c in potential_details_columns if c in df_potential_details.columns]
        df_potential_details = df_potential_details[existing_cols]

        # Convert date columns to remove time portion
        date_cols = [
            'Enquiry Date', 'Created Date', 'Modified Date',
            'Next Followup Date', 'Closing Date', 'Last Contact Date'
        ]
        for col in date_cols:
            if col in df_potential_details.columns:
                df_potential_details[col] = df_potential_details[col].dt.date

        # Define groups
        group1 = ['Region', 'Potential Code', 'Billing City']
        group2 = ['Executive', 'Potential Owner']
        group3 = ['Campaign Source', 'Lead Source']
        group4 = ['Stage', 'Probability (%)', 'Category']
        group5 = ['Full Name', 'Mobile', 'Email']
        group6 = ['Enquiry Date', 'Created Date', 'Modified Date']
        group7 = ['Next Followup Date', 'Closing Date', 'Last Contact Date']

        def display_fields_in_columns(fields, num_columns):
            cols = st.columns(num_columns)
            row = df_potential_details.iloc[0]
            for i, field_name in enumerate(fields):
                if field_name in row:
                    with cols[i]:
                        st.markdown(
                            f"<p style='margin: 0; padding: 0;'><strong>{field_name}:</strong> {row.get(field_name, '')}</p>",
                            unsafe_allow_html=True
                        )

        st.markdown(
            """
            <style>
            .stMarkdown p {
                margin: 0;
                padding: 0;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Display Potential Details in groups
        display_fields_in_columns(group1, 4)
        display_fields_in_columns(group2, 4)
        display_fields_in_columns(group3, 4)
        display_fields_in_columns(group4, 4)
        display_fields_in_columns(group5, 4)
        display_fields_in_columns(group6, 4)
        display_fields_in_columns(group7, 4)
    else:
        st.info("No potential details found for the selected Potential No.")

    # 6) Load DSR Stage History
    df_dsr = load_dsr_stage_history(modified_rdb_file_path, selected_potential_no)

    if not df_dsr.empty:
        # Move 'Description' to last column, if exists
        if 'Description' in df_dsr.columns:
            cols_except_desc = [c for c in df_dsr.columns if c != 'Description']
            df_dsr = df_dsr[cols_except_desc + ['Description']]

        # Remove time portion from date columns
        if 'Created Date' in df_dsr.columns:
            df_dsr['Created Date'] = df_dsr['Created Date'].dt.date
        if 'Closing Date' in df_dsr.columns:
            df_dsr['Closing Date'] = pd.to_datetime(df_dsr['Closing Date'], errors='coerce').dt.date

        st.write('#### DSR Stage History:')

        # ------------------- AGGRID INTEGRATION -------------------
        builder = GridOptionsBuilder.from_dataframe(df_dsr)
        builder.configure_default_column(wrapText=True, autoHeight=True)
        builder.configure_column("Description", wrapText=True, autoHeight=True)
        grid_options = builder.build()

        AgGrid(
            df_dsr,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,
        )
        # ----------------------------------------------------------

        # ----- Code to download DSR data as Excel -----
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        workbook = writer.book
        header_format = workbook.add_format({'bold': True, 'bg_color': 'yellow'})

        # Potential Details (if you want them in the same Excel)
        if not df_potential_details.empty:
            df_details_for_excel = df_potential_details.reset_index(drop=True)
            df_details_for_excel.to_excel(writer, index=False, sheet_name='Potential Details')
            ws_details = writer.sheets['Potential Details']
            for col_num, val in enumerate(df_details_for_excel.columns):
                ws_details.write(0, col_num, val, header_format)
            # Adjust widths for Potential Details sheet
            for idx, col in enumerate(df_details_for_excel.columns):
                series = df_details_for_excel[col].astype(str)
                maxw = min(series.map(len).max() + 2, 50)
                ws_details.set_column(idx, idx, maxw)
            ws_details.freeze_panes(1, 0)

        # DSR Stage History
        df_dsr.to_excel(writer, index=False, sheet_name='DSR Stage History')
        ws_dsr = writer.sheets['DSR Stage History']

        # Write headers with formatting
        for col_num, val in enumerate(df_dsr.columns):
            ws_dsr.write(0, col_num, val, header_format)

        # --- NEW COLUMN WIDTH LOGIC ---
        # Fixed width of 15 for: Created Date, Closing Date, Original Stage, New Stage
        # Wider (e.g., 80) for Description, auto-calc for others
        for idx, col in enumerate(df_dsr.columns):
            if col in ["Created Date", "Closing Date", "Original Stage", "New Stage"]:
                ws_dsr.set_column(idx, idx, 10)
            elif col == 'Description':
                cfmt = workbook.add_format({'text_wrap': True})
                ws_dsr.set_column(idx, idx, 80, cfmt)
            else:
                series = df_dsr[col].astype(str)
                maxw = min(series.map(len).max() + 2, 50)  # or 80 if you want bigger columns
                ws_dsr.set_column(idx, idx, maxw)

        ws_dsr.freeze_panes(00, 0)

        writer.close()
        processed_data = output.getvalue()

        st.download_button(
            label="Download Data as Excel",
            data=processed_data,
            file_name='form3_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.info("No records found for the selected Potential No. in the database.")

    # 7) Bookmarking Feature
    bookmarks_db_path = home_dir / "new" / "bookmarks.db"
    if is_potential_bookmarked(bookmarks_db_path, selected_potential_no):
        st.info("This potential is already bookmarked.")
        if st.button('Remove Bookmark'):
            remove_bookmark(bookmarks_db_path, selected_potential_no)
            st.success(f"Bookmark for Potential {selected_potential_no} removed.")
    else:
        if st.button('Add Bookmark'):
            add_bookmark(bookmarks_db_path, selected_potential_no)
            st.success(f"Potential {selected_potential_no} bookmarked.")

# ---------------------------
# Find Potential Function
# ---------------------------
def find_potential():
    """
    Modified Find Potential function with the following dropdown layout:
       Row 1:  [State/UT]          [Company Name]
       Row 2:  [Potential Code]    [Potential No.]
    Then, the function loads the Potential Details and DSR history.
    """

    # Access variables from st.session_state
    filtered_df = st.session_state['filtered_df']
    start_date = st.session_state['start_date']
    end_date = st.session_state['end_date']
    selected_region = st.session_state.get('selected_region', 'All')
    selected_executive = st.session_state.get('selected_executive', 'All')
    selected_potential_code = st.session_state.get('selected_potential_code', 'All')

    # Home directory
    home_dir = st.session_state.get('home_dir', Path.home())

    # -------------------------------------------
    # Path to the NEW DB: sales_reporting_logic_rdb.db
    # -------------------------------------------
    sales_reporting_logic_rdb_file_path = home_dir / "new" / "sales_reporting_logic.db"
    if not sales_reporting_logic_rdb_file_path.exists():
        st.error(f"Database file not found at the path: {sales_reporting_logic_rdb_file_path}")
        return

    # -------------------------------------------
    # Identify the table that contains 'Region', 'Company Name', and 'Potential Code'
    # (We still search for 'Region', but your table now has [State/UT]. Adjust as needed.)
    # -------------------------------------------
    table_with_company = None
    with sqlite3.connect(sales_reporting_logic_rdb_file_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        # Look for a table that has Region, Company Name, Potential Code, and State/UT
        for tbl in tables:
            cursor.execute(f"PRAGMA table_info('{tbl}')")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            if 'Region' in columns and 'Company Name' in columns and 'Potential Code' in columns and 'State/UT' in columns:
                table_with_company = tbl
                break

    if not table_with_company:
        st.warning("No table with 'Region', 'Company Name', 'Potential Code', and 'State/UT' found in sales_reporting_logic_rdb.db.")
        return

    # -------------------------------------------
    # Query all State/UT values
    # -------------------------------------------
    with sqlite3.connect(sales_reporting_logic_rdb_file_path) as conn:
        query_state = f"""
        SELECT DISTINCT [State/UT]
        FROM '{table_with_company}'
        WHERE [State/UT] IS NOT NULL
              AND TRIM([State/UT]) <> ''
        ORDER BY [State/UT]
        """
        state_df = pd.read_sql_query(query_state, conn)

    if state_df.empty:
        st.info("No states found in the sales_reporting_logic_rdb.db database.")
        return

    state_list = state_df['State/UT'].tolist()

    # -------------------------------------------
    # ROW 1: Select State/UT and then Select Company
    # -------------------------------------------
    col_state, col_company = st.columns(2)

    with col_state:
        selected_state = st.selectbox("Select State/UT", options=state_list, key='selected_state_in_find')

    # Default empty list for Company in case state not selected
    company_list = []
    selected_company = ""

    if selected_state:
        # Fetch companies for this state
        with sqlite3.connect(sales_reporting_logic_rdb_file_path) as conn:
            query_companies = f"""
            SELECT DISTINCT [Company Name]
            FROM '{table_with_company}'
            WHERE [State/UT] = ?
                  AND [Company Name] IS NOT NULL
                  AND TRIM([Company Name]) <> ''
            ORDER BY [Company Name]
            """
            companies_df = pd.read_sql_query(query_companies, conn, params=(selected_state,))
        company_list = companies_df['Company Name'].tolist() if not companies_df.empty else []

    with col_company:
        if company_list:
            selected_company = st.selectbox("Select Company Name", options=company_list, key='selected_company_name_in_find')
        else:
            st.info("No Company Names found for the selected State.")

    if not selected_company:
        # If user hasn't selected a company, we stop here.
        return

    # -------------------------------------------
    # ROW 2: Select Potential Code and Potential No.
    # -------------------------------------------
    col_code, col_potential = st.columns(2)

    with col_code:
        potential_code_list = []
        selected_code = ""

        # Fetch Potential Codes once we have selected_company
        with sqlite3.connect(sales_reporting_logic_rdb_file_path) as conn:
            query_codes = f"""
            SELECT DISTINCT [Potential Code]
            FROM '{table_with_company}'
            WHERE [Company Name] = ?
                  AND [Potential Code] IS NOT NULL
                  AND TRIM([Potential Code]) <> ''
            ORDER BY [Potential Code]
            """
            codes_df = pd.read_sql_query(query_codes, conn, params=(selected_company,))

        if not codes_df.empty:
            potential_code_list = codes_df['Potential Code'].tolist()

        if potential_code_list:
            selected_code = st.selectbox("Select Potential Code", options=potential_code_list, key='selected_code_in_find')
        else:
            st.info("No Potential Codes found for the selected Company.")
            return

    with col_potential:
        potential_list = []
        selected_potential_no = ""

        if selected_code:
            # Fetch Potential No. for the selected company & code
            with sqlite3.connect(sales_reporting_logic_rdb_file_path) as conn:
                query_potentials = f"""
                SELECT DISTINCT [Potential No.]
                FROM '{table_with_company}'
                WHERE [Company Name] = ?
                      AND [Potential Code] = ?
                      AND [Potential No.] IS NOT NULL
                      AND TRIM([Potential No.]) <> ''
                ORDER BY [Potential No.]
                """
                potentials_df = pd.read_sql_query(query_potentials, conn, params=(selected_company, selected_code))
            if not potentials_df.empty:
                potential_list = potentials_df['Potential No.'].tolist()

            if potential_list:
                selected_potential_no = st.selectbox("Select Potential No.", options=potential_list, key='selected_potential_no_for_company_code')
            else:
                st.info("No Potential Numbers found for the selected Company and Potential Code.")
                return

    if not selected_potential_no:
        # If user hasn't selected a potential, we stop here.
        return

    # -------------------------------------------
    # After selecting the Potential No., load details from modified_rdb.db
    # -------------------------------------------
    modified_rdb_file_path = home_dir / "new" / "modified_rdb.db"
    if not modified_rdb_file_path.exists():
        st.error(f"Database file not found at the path: {modified_rdb_file_path}")
        return

    # ---------------------------
    # Load potential details from modified_rdb.db
    # ---------------------------
    with st.spinner('Loading potential details from modified_rdb.db...'):
        df_potential_details = load_potential_details(modified_rdb_file_path, selected_potential_no)

    st.write("---")
    st.subheader("Potential Details")
    df_combined = pd.DataFrame()
    if not df_potential_details.empty:
        # Keep the columns you need
        potential_details_columns = [
            'Region', 'Potential Code', 'Billing City',
            'Executive', 'Potential Owner',
            'Campaign Source', 'Lead Source',
            'Stage', 'Probability (%)', 'Category',
            'Full Name', 'Mobile', 'Email',
            'Enquiry Date', 'Created Date', 'Modified Date',
            'Next Followup Date', 'Closing Date', 'Last Contact Date'
        ]
        df_potential_details = df_potential_details[potential_details_columns]

        # Display only date part for date columns
        date_columns_list = [
            'Enquiry Date', 'Created Date', 'Modified Date',
            'Next Followup Date', 'Closing Date', 'Last Contact Date'
        ]
        for col in date_columns_list:
            if col in df_potential_details.columns and pd.api.types.is_datetime64_any_dtype(df_potential_details[col]):
                df_potential_details[col] = df_potential_details[col].dt.date

        df_combined = df_potential_details

        # Group fields for display
        group1 = ['Region', 'Potential Code', 'Billing City']
        group2 = ['Executive', 'Potential Owner']
        group3 = ['Campaign Source', 'Lead Source']
        group4 = ['Stage', 'Probability (%)', 'Category']
        group5 = ['Full Name', 'Mobile', 'Email']
        group6 = ['Enquiry Date', 'Created Date', 'Modified Date']
        group7 = ['Next Followup Date', 'Closing Date', 'Last Contact Date']

        def display_fields_in_columns(fields, num_columns):
            cols = st.columns(num_columns)
            for i, field_name in enumerate(fields):
                with cols[i]:
                    st.markdown(
                        f"<p style='margin: 0; padding: 0;'><strong>{field_name}:</strong> {row.get(field_name, '')}</p>",
                        unsafe_allow_html=True
                    )

        # Apply custom CSS to minimize spacing
        st.markdown(
            """
            <style>
            .stMarkdown p {
                margin: 0;
                padding: 0;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Display Potential Details (taking first row if multiple)
        row = df_combined.iloc[0]
        display_fields_in_columns(group1, 4)
        display_fields_in_columns(group2, 4)
        display_fields_in_columns(group3, 4)
        display_fields_in_columns(group4, 4)
        display_fields_in_columns(group5, 4)
        display_fields_in_columns(group6, 4)
        display_fields_in_columns(group7, 4)
    else:
        st.info("No potential details found in modified_rdb.db for the selected Potential No.")

    # ---------------------------
    # Load DSR stage history from modified_rdb.db
    # ---------------------------
    st.write("---")
    st.subheader("DSR Stage History")

    df_dsr = load_dsr_stage_history(modified_rdb_file_path, selected_potential_no)
    if not df_dsr.empty:
        # Ensure 'Description' is the last column
        columns_order = [col for col in df_dsr.columns if col != 'Description'] + ['Description']
        df_dsr = df_dsr[columns_order]

        # Convert date columns to date only
        if 'Created Date' in df_dsr.columns and pd.api.types.is_datetime64_any_dtype(df_dsr['Created Date']):
            df_dsr['Created Date'] = df_dsr['Created Date'].dt.date
        if 'Closing Date' in df_dsr.columns:
            df_dsr['Closing Date'] = pd.to_datetime(df_dsr['Closing Date'], errors='coerce').dt.date

        df_dsr_styled = df_dsr.style.set_properties(
            subset=['Description'],
            **{'white-space': 'pre-wrap', 'max-width': '1020px'}
        )

        st.dataframe(df_dsr_styled)
    else:
        st.info("No DSR history found in modified_rdb.db for the selected Potential No.")

    # ---------------------------
    # Download Button for the Data
    # ---------------------------
    if not df_combined.empty or not df_dsr.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})

            # Potential Details Sheet
            if not df_combined.empty:
                df_combined.to_excel(writer, index=False, sheet_name='Potential Details', startrow=1)
                worksheet = writer.sheets['Potential Details']
                # Write group row headers
                group_headers = [
                    ('Group 1', 0, 2),
                    ('Group 2', 3, 4),
                    ('Group 3', 5, 6),
                    ('Group 4', 7, 9),
                    ('Group 5', 10, 12),
                    ('Group 6', 13, 15),
                    ('Group 7', 16, 18)
                ]
                row_header = 0
                for group_name, start_col, end_col in group_headers:
                    worksheet.merge_range(row_header, start_col, row_header, end_col, group_name, header_format)

                # Apply bold for columns in row 1
                for col_num, value in enumerate(df_combined.columns):
                    worksheet.write(1, col_num, value, header_format)
                # Auto-size columns
                for idx, col in enumerate(df_combined.columns):
                    series = df_combined[col].astype(str)
                    max_width = series.map(len).max()
                    adjusted_width = min(max_width + 2, 30)
                    worksheet.set_column(idx, idx, adjusted_width)

                worksheet.freeze_panes(2, 0)

            # DSR Stage History Sheet
            if not df_dsr.empty:
                df_dsr.to_excel(writer, index=False, sheet_name='DSR Stage History')
                worksheet = writer.sheets['DSR Stage History']
                for col_num, value in enumerate(df_dsr.columns):
                    worksheet.write(0, col_num, value, header_format)
                for idx, col in enumerate(df_dsr.columns):
                    series = df_dsr[col].astype(str)
                    max_width = series.map(len).max()
                    adjusted_width = min(max_width + 2, 50)
                    if col == 'Description':
                        cell_format = workbook.add_format({'text_wrap': True})
                        worksheet.set_column(idx, idx, adjusted_width, cell_format)
                    else:
                        worksheet.set_column(idx, idx, adjusted_width)
                worksheet.freeze_panes(1, 0)

        processed_data = output.getvalue()

        st.download_button(
            label="Download Potential Details as Excel",
            data=processed_data,
            file_name=f'{selected_potential_no}_details.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.info("No data available to download.")

    # ---------------------------
    # Bookmarking Feature (Optional)
    # ---------------------------
    if st.session_state.get('logged_in', False):
        bookmarks_db_path = home_dir / "new" / "bookmarks.db"
        if is_potential_bookmarked(bookmarks_db_path, selected_potential_no):
            st.info("This potential is already bookmarked.")
            if st.button('Remove Bookmark'):
                remove_bookmark(bookmarks_db_path, selected_potential_no)
                st.success(f"Bookmark for Potential {selected_potential_no} removed.")
        else:
            if st.button('Add Bookmark'):
                add_bookmark(bookmarks_db_path, selected_potential_no)
                st.success(f"Potential {selected_potential_no} bookmarked.")
# ---------------------------
# Bookmarks Function
# ---------------------------
def bookmarks():
    st.title('My Bookmarked Potentials')
    
    # Ensure the user is logged in
    if not st.session_state.get('logged_in', False):
        st.warning("Please log in to view your bookmarks.")
        return

    user_bookmarks_data = get_user_bookmarks(bookmarks_db_path)
    if user_bookmarks_data:
        user_bookmarks = [item['potential_no'] for item in user_bookmarks_data]
        # Update session state for selected potential no
        if 'selected_potential_no_bookmarks' not in st.session_state or st.session_state['selected_potential_no_bookmarks'] not in user_bookmarks:
            st.session_state['selected_potential_no_bookmarks'] = user_bookmarks[0]
        
        # Allow user to select a bookmarked potential
        selected_potential_no = st.selectbox('Select Bookmarked Potential No.', user_bookmarks, 
                                             index=user_bookmarks.index(st.session_state['selected_potential_no_bookmarks']),
                                             key='selected_potential_no_bookmarks')

        # Get the timestamp of the selected bookmark
        bookmark_timestamp = next((item['timestamp'] for item in user_bookmarks_data if item['potential_no'] == selected_potential_no), None)
        # Display the date and time of the bookmark
        if bookmark_timestamp:
            bookmark_datetime = datetime.strptime(bookmark_timestamp, '%Y-%m-%d %H:%M:%S')
            st.write(f"Bookmarked on: **{bookmark_datetime.strftime('%Y-%m-%d %H:%M:%S')}**")

        # Load potential details and DSR history (similarly to Search Potential)
        modified_rdb_file_path = st.session_state['home_dir'] / "new" / "modified_rdb.db"

        if not modified_rdb_file_path.exists():
            st.error(f"Database file not found at the path: {modified_rdb_file_path}")
            return

        with st.spinner('Loading potential details...'):
            df_potential_details = load_potential_details(modified_rdb_file_path, selected_potential_no)

        if not df_potential_details.empty:
            # Define potential details columns and groups
            potential_details_columns = [
                'Region', 'Potential Code', 'Billing City',
                'Executive', 'Potential Owner',
                'Campaign Source', 'Lead Source',
                'Stage', 'Probability (%)', 'Category',
                'Full Name', 'Mobile', 'Email',
                'Enquiry Date', 'Created Date', 'Modified Date',
                'Next Followup Date', 'Closing Date', 'Last Contact Date'
            ]

            df_potential_details = df_potential_details[potential_details_columns]

            # Display only the date part for date columns
            date_columns = [
                'Enquiry Date', 'Created Date', 'Modified Date',
                'Next Followup Date', 'Closing Date', 'Last Contact Date'
            ]
            for col in date_columns:
                if col in df_potential_details.columns:
                    df_potential_details[col] = df_potential_details[col].dt.date

            # Define field groups as in the search potential function
            group1 = ['Region', 'Potential Code', 'Billing City']
            group2 = ['Executive', 'Potential Owner']
            group3 = ['Campaign Source', 'Lead Source']
            group4 = ['Stage', 'Probability (%)', 'Category']
            group5 = ['Full Name', 'Mobile', 'Email']
            group6 = ['Enquiry Date', 'Created Date', 'Modified Date']
            group7 = ['Next Followup Date', 'Closing Date', 'Last Contact Date']

            def display_fields_in_columns(fields, num_columns):
                cols = st.columns(num_columns)
                for i, field_name in enumerate(fields):
                    with cols[i]:
                        st.markdown(
                            f"<p style='margin: 0; padding: 0;'><strong>{field_name}:</strong> {row.get(field_name, '')}</p>",
                            unsafe_allow_html=True
                        )

            # Apply custom CSS to minimize spacing
            st.markdown(
                """
                <style>
                .stMarkdown p {
                    margin: 0;
                    padding: 0;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Display Potential Details
            st.write('#### Potential Details:')
            row = df_potential_details.iloc[0]
            display_fields_in_columns(group1, 4)
            display_fields_in_columns(group2, 4)
            display_fields_in_columns(group3, 4)
            display_fields_in_columns(group4, 4)
            display_fields_in_columns(group5, 4)
            display_fields_in_columns(group6, 4)
            display_fields_in_columns(group7, 4)
        else:
            st.info("No potential details found for the selected Potential No.")

        # Load DSR history
        df_dsr = load_dsr_stage_history(modified_rdb_file_path, selected_potential_no)
        if not df_dsr.empty:
            # Ensure 'Description' is last column
            columns_order = [col for col in df_dsr.columns if col != 'Description'] + ['Description']
            df_dsr = df_dsr[columns_order]

            # Convert Created Date and Closing Date to date only
            if 'Created Date' in df_dsr.columns:
                df_dsr['Created Date'] = df_dsr['Created Date'].dt.date
            if 'Closing Date' in df_dsr.columns:
                df_dsr['Closing Date'] = pd.to_datetime(df_dsr['Closing Date'], errors='coerce').dt.date

            df_dsr_styled = df_dsr.style.set_properties(subset=['Description'], **{'white-space': 'pre-wrap', 'max-width': '1020px'})

            st.write('#### DSR Stage History:')
            st.dataframe(df_dsr_styled)
        else:
            st.info("No DSR history found for the selected Potential No.")

        # Add the Remove Bookmark Option
        if is_potential_bookmarked(bookmarks_db_path, selected_potential_no):
            if st.button('Remove Bookmark'):
                remove_bookmark(bookmarks_db_path, selected_potential_no)
                st.success(f"Bookmark for Potential {selected_potential_no} removed.")
                # Refresh the bookmarks list
                user_bookmarks_data = get_user_bookmarks(bookmarks_db_path)
                if user_bookmarks_data:
                    user_bookmarks = [item['potential_no'] for item in user_bookmarks_data]
                    st.session_state['selected_potential_no_bookmarks'] = user_bookmarks[0]
                else:
                    st.info("You have no bookmarks.")
                    return
        else:
            # If needed, user can bookmark again, though by definition we are in bookmarks
            # This condition might not occur because we already know it was bookmarked.
            # But let's keep the logic intact.
            if st.button('Add Bookmark'):
                add_bookmark(bookmarks_db_path, selected_potential_no)
                st.success(f"Potential {selected_potential_no} bookmarked.")

    else:
        st.info("You have no bookmarks.")

# ---------------------------
# Main Execution
# ---------------------------
def main():
    
    # Display the title only on the login page
    st.title("SUBA SOLUTIONS CRM DASHBOARD")

    # Logout button in top right corner
    if st.session_state.logged_in:
        col1, col2 = st.columns([6, 1])
        with col2:
            st.button("Logout", key='logout_button', on_click=logout)

    st.markdown("""
    <style>
    .stDownloadButton > button {
        background-color: green;
        color: white;
    }
    .stDownloadButton > button:hover {
        background-color: #006400; /* Darker green on hover */
        color: white;
    }
    /* Style for Add Bookmark and Remove Bookmark buttons */
    .add-bookmark-button button, .remove-bookmark-button button {
        background-color: orange;
        color: white;
    }
    .add-bookmark-button button:hover, .remove-bookmark-button button:hover {
        background-color: #FF8C00; /* Darker orange on hover */
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)


    # Set menu options based on login status
    if st.session_state.logged_in:
        menu = ["Home"]
        default_index = 0  # Home
    else:
        menu = ["Login", "Register","Reset Password"]
        default_index = 0  # Login

    # Sidebar menu
    choice = st.sidebar.selectbox("Menu", menu, index=default_index)

    # Update page based on menu selection
    st.session_state.page = choice

    # Render pages based on session state
    if st.session_state.page == "Home":
        #st.subheader("Welcome to the Dashboard!")
        if st.session_state.logged_in:
            #st.success(f"Logged in as {st.session_state.username}")
            main_app()  # Call the main application function
        else:
            st.info("Please login to view the dashboard.")
            st.session_state.page = 'Login'  # Redirect to Login if not logged in

    elif st.session_state.page == "Login":
        
        if st.session_state.logged_in:
            st.success(f"You are already logged in as {st.session_state.username}.")
            st.session_state.page = 'Home'  # Redirect to Home if already logged in
        else:
            st.subheader("Login Section")

            username = st.text_input("Username", key='login_username')
            password = st.text_input("Password", type='password', key='login_password')

            st.button("Login", key='login_button', on_click=login, args=(username, password))

            # Reset Password Option
            #if st.button("Forgot Password?", key='forgot_password_button'):
            #    st.session_state.reset_password = True
            #    st.session_state.page = 'Reset Password'

    elif st.session_state.page == "Register":
        st.subheader("Create New Account")

        new_user = st.text_input("Username", key='register_username')
        new_email = st.text_input("Email", key='register_email')
        new_password = st.text_input("Password", type='password', key='register_password')

        st.button("Sign Up", key='signup_button', on_click=signup, args=(new_user, new_email, new_password))

    elif st.session_state.page == "Reset Password":
        st.subheader("Reset Password")
        username = st.text_input("Username", key='reset_username')
        email = st.text_input("Email", key='reset_email')
        new_password = st.text_input("New Password", type='password', key='reset_new_password')
        confirm_password = st.text_input("Confirm Password", type='password', key='reset_confirm_password')

        if st.button("Reset Password", key='reset_password_button'):
            if new_password == confirm_password:
                reset_password(username, email, new_password)
            else:
                st.error("Passwords do not match.")

        #if st.button("Back to Login", key='back_to_login_button'):
            #st.session_state.reset_password = False
            #st.session_state.page = 'Login'

if __name__ == '__main__':
    main()
