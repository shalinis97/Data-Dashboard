import os
import pandas as pd
import sqlite3
import streamlit as st
from pathlib import Path
import time

# ==========================
# Function Definitions
# ==========================

def save_df_to_db(df, db_path, table_name):
    """
    Saves a DataFrame (`df`) to a SQLite database (`db_path`) under the specified table name (`table_name`).
    If the table exists, it will be replaced.
    """
    try:
        # Establish a connection to the SQLite database
        conn = sqlite3.connect(db_path)
        
        # Write the DataFrame to the specified table in the database
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Close the connection
        conn.close()
        
        # Indicate success in Streamlit
        st.success(f"Successfully saved '{table_name}' to '{db_path}'")
    except Exception as e:
        # In case of an error, show it in Streamlit
        st.error(f"Error saving '{table_name}' to DB: {e}")

def process_executive_column(df):
    """
    Takes a DataFrame (`df`) and performs the following on the 'Executive' column:
      1. Replace 'Raji' with 'Rajalakshmi' and 'Senthilkumar' with 'Senthil'.
      2. Append the suffix " - (EX)" to a list of specified executives.
    Returns the modified DataFrame.
    """
    # Check if 'Executive' column exists in the DataFrame
    if 'Executive' in df.columns:
        # Replace specific names
        df['Executive'] = df['Executive'].replace({'Raji': 'Rajalakshmi', 'Senthilkumar': 'Senthil'})
        
        # Define a list of executives who need the '- (EX)' suffix
        ex_executives = [
            'A. Sundaram', 'Barish Biswas', 'Bhavnesh', 'CN', 'Deven Verma', 'Dinesh Kumar',
            'Ganesh Pandiyan', 'Gopinath', 'Gundla Indhu', 'Harikrishnan', 'Herbert Anthony',
            'Kamaldeep', 'Kumar Harsh', 'Madhu', 'Manoj Wadiyar', 'Meghraj Andhale', 'Murali',
            'Navdeep', 'Neel Mehta', 'R.D. Gopinath', 'Rakesh Ravi', 'Ram Virendra Subedar',
            'Ramalakshmi', 'Ramji', 'Rinoy', 'Shridhar Nandu Pagare', 'Sivakrishna', 'Subramanian',
            'T. Halder', 'Thomas', 'Tinku Sharma', 'Vijay', 'Yogesh'
        ]
        
        # Apply the suffix only if the executive's name is in `ex_executives`
        df['Executive'] = df['Executive'].apply(lambda x: f"{x} - (EX)" if x in ex_executives else x)
    
    # Return the updated DataFrame
    return df

def process_potential_owner_column(df):
    """
    Takes a DataFrame (`df`) and replaces specific entries in the 'Potential Owner' column
    with corresponding email addresses.
    Returns the modified DataFrame.
    """
    # Check if 'Potential Owner' column exists
    if 'Potential Owner' in df.columns:
        
        # Mapping of text to email addresses
        replacement_mapping = {
            'FP Suba Solutions': 'sales@subasolutions.com',
            'Marketing': 'marketing@subasolutions.com',
            'Mohan Suba': 'mohan@subasolutions.com',
            'S Senthilkumar': 'senthil@subasolutions.com',
            'Suba Suba Solutions Pvt. Ltd.': 'balaji@subasolutions.com',
            'V Vaidyalingam': 'vaidy@subasolutions.com'
        }
        
        # Replace the values in the column using the defined mapping
        df['Potential Owner'] = df['Potential Owner'].replace(replacement_mapping)
    
    # Return the updated DataFrame
    return df

def process_p_data(df):
    """
    Processes p1 and p2 DataFrames with the following steps:
      1. Drop unnecessary columns if they exist.
      2. Rename certain columns for consistency.
      3. Convert specific date columns to datetime format (dayfirst=True).
      4. Apply stage_mapping and category_mapping if those columns exist.
      5. Process the 'Executive' and 'Potential Owner' columns with the respective functions.
      6. Filter entries based on 'Created Date' or 'Modified Date' being >= 01/01/2021.

    Returns the cleaned and processed DataFrame.
    """
    # 1. Drop specified columns if present (safe to ignore if they don't exist)
    df = df.drop(['Record Id', 'Record Id (Contact Name)', 'Record Id (Company Name)'], axis=1, errors='ignore')
    
    # 2. Rename columns for uniformity
    df = df.rename(columns={
        'Sales handled by': 'Executive',
        'Created Time': 'Created Date',
        'Modified Time': 'Modified Date',
        'Company Name (Company Name)': 'Company Name'
    })
    
    # 3. Convert certain columns to datetime with dayfirst=True
    date_columns = ['Created Date', 'Modified Date', 'Closing Date', 'Enquiry Date', 'Last Contact Date', 'Next Followup Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce', infer_datetime_format=True)
    
    # 4. Apply 'Stage' mapping (global dictionary stage_mapping) if 'Stage' column exists
    if 'Stage' in df.columns:
        df['Stage'] = df['Stage'].replace(stage_mapping)
    
    # 4a. Apply 'Category' mapping (global dictionary category_mapping) if 'Category' column exists
    if 'Category' in df.columns:
        df['Category'] = df['Category'].replace(category_mapping)
    
    # 5. Process the 'Executive' column to standardize names
    df = process_executive_column(df)
    
    # 5a. Process the 'Potential Owner' column to convert names to email addresses
    df = process_potential_owner_column(df)
    
    # 6. Filter out records that are older than 01/01/2021 based on either 'Created Date' or 'Modified Date'
    if 'Created Date' in df.columns and 'Modified Date' in df.columns:
        date_threshold = pd.to_datetime('01-01-2021', dayfirst=True)
        df = df[(df['Created Date'] >= date_threshold) | (df['Modified Date'] >= date_threshold)]
    elif 'Created Date' in df.columns:
        df = df[df['Created Date'] >= pd.to_datetime('01-01-2021', dayfirst=True)]
    elif 'Modified Date' in df.columns:
        df = df[df['Modified Date'] >= pd.to_datetime('01-01-2021', dayfirst=True)]
    
    # Return the processed DataFrame
    return df

def process_dsr_data(df):
    """
    Processes dsr1 and dsr2 DataFrames with the following steps:
      1. Drop unnecessary columns if they exist.
      2. Rename columns for consistency (aligning with the main data).
      3. Remove records that have empty 'Potential No.'.
      4. Convert certain columns to datetime (dayfirst=True).
      5. Merge or rename the 'Mode of Contact' columns if needed.
      6. Map stages in 'Original Stage' and 'New Stage' columns.
      7. If 'New Stage' is null and 'Original Stage' is not, copy 'Original Stage' to 'New Stage'.
      8. Process 'Executive' and 'Potential Owner' columns with respective functions.
      9. Filter entries based on 'Created Date' or 'Modified Date' >= 01/01/2021.
      10. Add a 'DSR Type' column with a constant value 'DSR' to identify DSR records.

    Returns the cleaned and processed DataFrame.
    """
    # 1. Drop specified columns if they exist
    df = df.drop(['Record Id', 'Record Id (Potential Details)', 'Next Followup Date', 
                  'Sales Handled By (Potential Details)', 'Record Id (Company Name)'], axis=1, errors='ignore')
    
    # 2. Rename columns for consistency
    df = df.rename(columns={
        'Sales Person Name': 'Executive',
        'Next Followup Date (Potential Details)': 'Next Followup Date',
        'Created Time': 'Created Date'
    })
    
    # 3. Remove records where 'Potential No.' is empty or NaN
    if 'Potential No.' in df.columns:
        df = df[df['Potential No.'].notna()]
    
    # 4. Convert specified columns to datetime format
    date_columns = ['Created Date', 'Contacted Date', 'Next Followup Date', 'Closing Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce', infer_datetime_format=True)
    
    # 5. Merge 'Mode of Contact (DSR)' column with 'Mode of Contact' if both exist
    if 'Mode of Contact (DSR)' in df.columns and 'Mode of Contact' in df.columns:
        # If 'Mode of Contact' is NaN, use 'Mode of Contact (DSR)'
        df['Mode of Contact'] = df['Mode of Contact (DSR)'].combine_first(df['Mode of Contact'])
        df = df.drop(['Mode of Contact (DSR)'], axis=1)
    elif 'Mode of Contact (DSR)' in df.columns:
        # If only 'Mode of Contact (DSR)' exists, rename it
        df = df.rename(columns={'Mode of Contact (DSR)': 'Mode of Contact'})
    
    # 6. Apply 'Stage' mapping to 'Original Stage' and 'New Stage' if they exist
    if 'Original Stage' in df.columns:
        df['Original Stage'] = df['Original Stage'].replace(stage_mapping)
    if 'New Stage' in df.columns:
        df['New Stage'] = df['New Stage'].replace(stage_mapping)
    
    # 7. If 'New Stage' is null and 'Original Stage' is not, copy 'Original Stage' to 'New Stage'
    if 'Original Stage' in df.columns and 'New Stage' in df.columns:
        condition = df['New Stage'].isna() & df['Original Stage'].notna()
        df.loc[condition, 'New Stage'] = df.loc[condition, 'Original Stage']
    
    # 8. Process 'Executive' to standardize naming
    df = process_executive_column(df)
    
    # 8a. Process 'Potential Owner' to replace with emails
    df = process_potential_owner_column(df)
    
    # 9. Filter out records older than 01/01/2021 based on 'Created Date' or 'Modified Date'
    if 'Created Date' in df.columns and 'Modified Date' in df.columns:
        date_threshold = pd.to_datetime('01-01-2021', dayfirst=True)
        df = df[(df['Created Date'] >= date_threshold) | (df['Modified Date'] >= date_threshold)]
    elif 'Created Date' in df.columns:
        df = df[df['Created Date'] >= pd.to_datetime('01-01-2021', dayfirst=True)]
    elif 'Modified Date' in df.columns:
        df = df[df['Modified Date'] >= pd.to_datetime('01-01-2021', dayfirst=True)]
    
    # 10. Add a 'DSR Type' column with a fixed value 'DSR'
    df['DSR Type'] = 'DSR'
    
    # Return the processed DSR DataFrame
    return df

# ==========================
# Start of Streamlit App
# ==========================

# Start timing the execution
start_time = time.time()

# Streamlit title
st.title('Sales Data Processing App')

# Get the current user's home directory via Path.home()
home_dir = Path.home()

# Construct the dynamic path to the 'new' folder inside the home directory
base_path = home_dir / "new"

# Print to logs for debugging (not displayed in Streamlit, but visible in console logs)
print(f"Base path is set to: {base_path}")

# Define the path to the 'database files' subfolder
database_path = base_path / 'database files'

# Ensure the subfolder for database files exists (create if it doesn't)
os.makedirs(database_path, exist_ok=True)

# Attempt to load CSV files into pandas DataFrames
try:
    # `p1.csv`, `p2.csv`, `dsr1.csv`, `dsr2.csv` must exist in `base_path`
    p1 = pd.read_csv(base_path / 'p1.csv')
    p2 = pd.read_csv(base_path / 'p2.csv')
    dsr1 = pd.read_csv(base_path / 'dsr1.csv')
    dsr2 = pd.read_csv(base_path / 'dsr2.csv')
except FileNotFoundError as e:
    # If any CSV file is not found, display the error in Streamlit and stop execution
    st.error(f"Error loading CSV files: {e}")
    st.stop()

# Define the global stage mapping dictionary
stage_mapping = {
    "2 Final Quote": "80 - Final Quote",
    "3 Negotiation/Review": "75 - Negotiation/Review",
    "4 Id. Decision Makers": "40 - Needs & problems understanding",
    "5 Value Proposition": "60 - Value Proposition",
    "6 Needs Analysis": "35 - Needs Analysis",
    "7 First Quote": "60 - Value Proposition",
    "8 Qualification": "20 - Qualification",
    "9 Prospecting": "10 - Prospecting",
    "Closed Customer not interested": "0 - Closed",
    "Closed Lost": "0 - Closed",
    "Closed Lost to Competition": "0 - Closed",
    "Closed Model Changed": "0 - Closed",
    "Closed Won": "100 - Billed",
    "Needs Analysis": "35 - Needs Analysis",
    "Perception Analysis": "35 - Needs Analysis",
    "0 - Closed - Customer not interested": "0 - Closed",
    "0 - Closed - customer placed order in another company name": "0 - Closed",
    "0 - Closed - Lost to Competition": "0 - Closed",
    "0 - Closed - Model Changed": "0 - Closed",
    "0 - Closed - our solution not suitable for customer": "0 - Closed",
    "0 - Closed - Product dropped from Portfolio": "0 - Closed",
    "0 - Closed - Project dropped": "0 - Closed",
    "0 - Closed -Project drop/too old /non core product/not very competitive. So potential being closed.": "0 - Closed",
    "100 - Closed Won-Full payment completed": "100 - Billed"
}

# Define the global category mapping dictionary
category_mapping = {
    '1. Hot': 'Hot',
    '2. Followup': 'Followup',
    '3. Cold': 'Cold',
    '4. Yet to Contact': 'Yet to Contact',
    '5. NR-No Response/Reply': 'NR-No Response/Reply'
}

# ==========================
# Data Processing
# ==========================

# Process p1 and p2 DataFrames using the `process_p_data()` function
p1rdb = process_p_data(p1).copy()
p2rdb = process_p_data(p2).copy()

# Define the new columns that will be added to p2rdb
new_columns = [
    'Previous Status Stage', 'PS Contacted On Date', 'PS Follow-up On Date', 
    'PS Closure Date', 'Current Status Stage', 'CS Contacted On Date', 
    'CS Follow-up On Date', 'CS Closure Date'
]

# Ensure these new columns are in p2rdb (if not, create them with NaN)
for col in new_columns:
    if col not in p2rdb.columns:
        p2rdb[col] = pd.NA  # Use pd.NA to represent missing data consistently

# Check for duplicates in p2rdb based on 'Potential No.'
duplicate_potentials = p2rdb[p2rdb.duplicated(subset=['Potential No.'], keep=False)]

# If duplicates exist, warn the user and display the duplicates
if not duplicate_potentials.empty:
    st.warning("There are duplicate 'Potential No.' entries in p2rdb. Please review these duplicates below:")
    st.dataframe(duplicate_potentials)
    
    # Option to remove duplicates by keeping the first occurrence
    p2rdb = p2rdb.drop_duplicates(subset=['Potential No.'], keep='first')
    st.warning(f"Removed {len(duplicate_potentials)} duplicate records from p2rdb by keeping the first occurrence.")
else:
    st.success("No duplicate 'Potential No.' entries found in p2rdb.")

# Process dsr1 and dsr2 DataFrames using the `process_dsr_data()` function
dsr1rdb = process_dsr_data(dsr1).copy()
dsr2rdb = process_dsr_data(dsr2).copy()

# Create main_rdb by concatenating p1rdb and dsr1rdb. This acts like a 'base' table.
main_rdb = pd.concat([p1rdb, dsr1rdb], ignore_index=True)

# Get the latest 'Created Date' from main_rdb to use as a filter boundary
if 'Created Date' in main_rdb.columns:
    latest_created_date_main = main_rdb['Created Date'].max()
else:
    # If 'Created Date' doesn't exist, use the earliest possible date
    latest_created_date_main = pd.Timestamp.min

# Filter p2rdb to include only records where 'Modified Date' is strictly greater than the latest_created_date_main
# This helps to ensure we only pick up newly modified records
if 'Modified Date' in p2rdb.columns:
    p2rdb_filtered = p2rdb[p2rdb['Modified Date'] > latest_created_date_main]
else:
    p2rdb_filtered = pd.DataFrame()

# Filter dsr2rdb to include only records where 'Created Date' is greater than latest_created_date_main
# Similarly, to pick up new DSR entries
if 'Created Date' in dsr2rdb.columns:
    dsr2rdb_filtered = dsr2rdb[dsr2rdb['Created Date'] > latest_created_date_main]
else:
    dsr2rdb_filtered = pd.DataFrame()

# Create weekly_rdb by concatenating p2rdb_filtered and dsr2rdb_filtered
# This DataFrame represents newly added or modified records for the "week"
weekly_rdb = pd.concat([p2rdb_filtered, dsr2rdb_filtered], ignore_index=True)

# Create modified_rdb by concatenating the entire main_rdb with the newly filtered data (weekly_rdb)
# This ensures we have an up-to-date DataFrame with all records
modified_rdb = pd.concat([main_rdb, weekly_rdb], ignore_index=True)

# ==========================
# Apply Category Mapping to modified_rdb
# ==========================
# After creating `modified_rdb`, ensure the 'Category' column is mapped (for consistency)
if 'Category' in modified_rdb.columns:
    modified_rdb['Category'] = modified_rdb['Category'].replace(category_mapping)
    st.info("Applied category mapping to 'Category' column in modified_rdb.")
else:
    st.warning("'Category' column not found in modified_rdb. Skipping category mapping.")

# ==========================
# Initialize sales_reporting_logic DataFrame
# ==========================

# Define the columns required for `sales_reporting_logic`
columns_required = [
    'Region', 'Executive', 'Potential No.', 'Potential Code','Potential Name', 'Campaign Source','Mobile','Billing City','State/UT','Email', 
    'Lead Source', 'Company Name', 'Enquiry Date', 'Last Contact Date', 
    'Next Followup Date', 'Created Date', 'Modified Date', 'Closing Date', 'Stage',
    'Previous Status Stage', 'PS Contacted On Date', 'PS Follow-up On Date', 
    'PS Closure Date', 'Current Status Stage', 'CS Contacted On Date', 
    'CS Follow-up On Date', 'CS Closure Date'
]

# Make sure that all required columns are present in p2rdb. If any are missing, create them with pd.NA
for col in columns_required:
    if col not in p2rdb.columns:
        p2rdb[col] = pd.NA

# Create sets of Potential No. for quick membership checks
p1_potential_nos = set(p1rdb['Potential No.'].dropna())
p2_potential_nos = set(p2rdb['Potential No.'].dropna())

# Count how many potentials in p2rdb also exist in p1rdb (common) and how many are new
common_potentials_count = p2rdb['Potential No.'].isin(p1rdb['Potential No.']).sum()
new_potentials_count = (~p2rdb['Potential No.'].isin(p1rdb['Potential No.'])).sum()

# Define a helper function to flag whether a Potential No. is 'Existing' or 'New'
def flag_potential(potential_no):
    if potential_no in p1_potential_nos:
        return 'Existing'
    else:
        return 'New'

# Apply the flag to each row in p2rdb
p2rdb['Flag'] = p2rdb['Potential No.'].apply(flag_potential)

# Populate `sales_reporting_logic` DataFrame with a subset of columns from p2rdb plus the 'Flag' column
sales_reporting_logic = p2rdb[columns_required + ['Flag']].copy()

# Ensure specific date columns are in datetime format in `sales_reporting_logic`
date_columns_srl = [
    'Enquiry Date', 'Last Contact Date', 'Next Followup Date', 
    'Created Date', 'Modified Date', 'Closing Date',
    'PS Contacted On Date', 'PS Follow-up On Date', 'PS Closure Date',
    'CS Contacted On Date', 'CS Follow-up On Date', 'CS Closure Date'
]
for col in date_columns_srl:
    if col in sales_reporting_logic.columns:
        sales_reporting_logic[col] = pd.to_datetime(
            sales_reporting_logic[col], dayfirst=True, errors='coerce', infer_datetime_format=True
        )

# ==========================
# Populating Remaining Stages Based on Cases
# ==========================
# Explanation:
# We need to look at both dsr2rdb and modified_rdb to figure out the "Previous Status" and "Current Status" for each potential.

# Create a copy of `sales_reporting_logic` to avoid potential SettingWithCopyWarning
sales_reporting_logic = sales_reporting_logic.copy()

# For faster lookups, group dsr2rdb and modified_rdb by 'Potential No.'
dsr2rdb_grouped = dsr2rdb.groupby('Potential No.')
modified_rdb_grouped = modified_rdb.groupby('Potential No.')

def apply_cases(row):
    """
    For each row in `sales_reporting_logic`, apply Cases 1-6 as per the logic:
      - Check if DSR records exist (in dsr2rdb).
      - Compare 'Modified Date' and 'DSR Contacted Date'.
      - Decide how to populate the 'Previous Status' and 'Current Status' columns accordingly.
    """
    # Extract values from the row for readability
    potential_no = row['Potential No.']
    modified_date = row['Modified Date']
    stage = row['Stage']
    last_contact_date = row['Last Contact Date']
    next_followup_date = row['Next Followup Date']
    closing_date = row['Closing Date']
    
    # Fetch DSR records for this potential from dsr2rdb_grouped
    dsr2_records = dsr2rdb_grouped.get_group(potential_no) if potential_no in dsr2rdb_grouped.groups else pd.DataFrame()
    
    # Fetch modified_rdb records for this potential
    mod_records = modified_rdb_grouped.get_group(potential_no) if potential_no in modified_rdb_grouped.groups else pd.DataFrame()
    
    # Filter mod_records to include only rows where 'DSR Type' is not set (i.e., not DSR, but main data)
    mod_records = mod_records[mod_records['DSR Type'].isna()]
    
    # ---------- Case 1: No DSR, Single Potential ----------
    if dsr2_records.empty and len(mod_records) == 1:
        # If there is exactly one main record and no DSR:
        # previous status == current status
        # copy last_contact_date and next_followup_date to both previous & current status fields
        row['Previous Status Stage'] = stage
        row['Current Status Stage'] = stage
        row['PS Contacted On Date'] = last_contact_date
        row['CS Contacted On Date'] = last_contact_date
        row['PS Follow-up On Date'] = next_followup_date
        row['CS Follow-up On Date'] = next_followup_date
        row['PS Closure Date'] = closing_date
        row['CS Closure Date'] = closing_date
        
    # ---------- Case 2: No DSR, Two or More Potentials ----------
    elif dsr2_records.empty and len(mod_records) >= 2:
        # Sort by 'Modified Date' in descending order to identify the latest and second-latest record
        mod_records_sorted = mod_records.sort_values('Modified Date', ascending=False)
        
        # latest_record = row with the most recent 'Modified Date'
        latest_record = mod_records_sorted.iloc[0]
        
        # second_latest_record = row with the second most recent 'Modified Date'
        second_latest_record = mod_records_sorted.iloc[1]
        
        # Populate Current Status from the latest record
        row['Current Status Stage'] = latest_record['Stage']
        row['CS Contacted On Date'] = latest_record['Last Contact Date']
        row['CS Follow-up On Date'] = latest_record['Next Followup Date']
        row['CS Closure Date'] = latest_record['Closing Date']
        
        # Populate Previous Status from the second latest record
        row['Previous Status Stage'] = second_latest_record['Stage']
        row['PS Contacted On Date'] = second_latest_record['Last Contact Date']
        row['PS Follow-up On Date'] = second_latest_record['Next Followup Date']
        row['PS Closure Date'] = second_latest_record['Closing Date']
        
    # ---------- Cases 3 & 4: DSR exists, compare 'Modified Date' with 'Contacted Date' ----------
    elif not dsr2_records.empty:
        # Create a new column for the DSR records to compare only the date part
        dsr2_records['Contacted Date DatePart'] = dsr2_records['Contacted Date'].dt.date
        
        # Get the date part from the row's 'Modified Date'
        modified_date_datepart = modified_date.date() if pd.notna(modified_date) else None
        
        # Filter dsr2_records where the Contacted Date's date part matches the Modified Date's date part
        dsr_same_date = dsr2_records[dsr2_records['Contacted Date DatePart'] == modified_date_datepart]
        
        # ---------- Case 3 & 4: If there are DSR records that match the date part ----------
        if not dsr_same_date.empty:
            # Sort them in descending order by 'Created Date' to find the latest DSR
            dsr_same_date_sorted = dsr_same_date.sort_values('Created Date', ascending=False)
            
            # If there's only one DSR record for that date
            if len(dsr_same_date_sorted) == 1:
                dsr_record = dsr_same_date_sorted.iloc[0]
                
                row['Previous Status Stage'] = dsr_record['Original Stage']
                row['Current Status Stage'] = dsr_record['New Stage']
                row['CS Contacted On Date'] = dsr_record['Contacted Date']
                row['CS Follow-up On Date'] = dsr_record['Next Followup Date']
                row['CS Closure Date'] = dsr_record['Closing Date']
            
            # If there are two or more DSR records for that date
            else:
                latest_dsr = dsr_same_date_sorted.iloc[0]
                second_latest_dsr = dsr_same_date_sorted.iloc[1]
                
                # Latest DSR for Current Status
                row['Current Status Stage'] = latest_dsr['New Stage']
                row['CS Contacted On Date'] = latest_dsr['Contacted Date']
                row['CS Follow-up On Date'] = latest_dsr['Next Followup Date']
                row['CS Closure Date'] = latest_dsr['Closing Date']
                
                # Second-latest DSR for Previous Status
                row['Previous Status Stage'] = second_latest_dsr['New Stage']
                row['PS Contacted On Date'] = second_latest_dsr['Contacted Date']
                row['PS Follow-up On Date'] = second_latest_dsr['Next Followup Date']
                row['PS Closure Date'] = second_latest_dsr['Closing Date']
        
        # ---------- Cases 5 & 6: If no matching date part, then Modified Date > Contacted Date ----------
        else:
            # Filter for DSR records where 'Contacted Date' is strictly less than the row's 'Modified Date'
            dsr_before_mod_date = dsr2_records[dsr2_records['Contacted Date DatePart'] < modified_date_datepart]
            
            # If there are any DSR records before the row's 'Modified Date'
            if not dsr_before_mod_date.empty:
                # Sort them in descending order by 'Contacted Date' to find the most recent DSR before the current record
                dsr_before_mod_date_sorted = dsr_before_mod_date.sort_values('Contacted Date', ascending=False)
                latest_dsr = dsr_before_mod_date_sorted.iloc[0]
                
                # Current Status from the row (sales_reporting_logic)
                row['Current Status Stage'] = stage
                row['CS Contacted On Date'] = last_contact_date
                row['CS Follow-up On Date'] = next_followup_date
                row['CS Closure Date'] = closing_date
                
                # Previous Status from the latest DSR
                row['Previous Status Stage'] = latest_dsr['New Stage']
                row['PS Contacted On Date'] = latest_dsr['Contacted Date']
                row['PS Follow-up On Date'] = latest_dsr['Next Followup Date']
                row['PS Closure Date'] = latest_dsr['Closing Date']
    
    # Return the updated row with the logic applied
    return row

# Apply the above `apply_cases` function to each row in `sales_reporting_logic`
sales_reporting_logic = sales_reporting_logic.apply(apply_cases, axis=1)

# Remove the temporary 'Contacted Date DatePart' column from dsr2rdb if it exists
if 'Contacted Date DatePart' in dsr2rdb.columns:
    dsr2rdb = dsr2rdb.drop(columns=['Contacted Date DatePart'])

# ==========================
# Calculating Discrepancies Between sales_reporting_logic and dsr2rdb
# ==========================

# We want to see if there are potentials in one DataFrame but not in the other
if 'Potential No.' not in dsr2rdb.columns:
    st.error("'Potential No.' column is missing in dsr2rdb. Cannot compute discrepancies.")
else:
    # Create sets for quick membership checks
    sales_potentials = set(sales_reporting_logic['Potential No.'].dropna())
    dsr2_potentials = set(dsr2rdb['Potential No.'].dropna())
    
    # Potentials in sales_reporting_logic but not in dsr2rdb
    sales_not_in_dsr2 = sales_potentials - dsr2_potentials
    count_sales_not_in_dsr2 = len(sales_not_in_dsr2)
    
    # Potentials in dsr2rdb but not in sales_reporting_logic
    dsr2_not_in_sales = dsr2_potentials - sales_potentials
    count_dsr2_not_in_sales = len(dsr2_not_in_sales)
    
    # Display discrepancy counts in the Streamlit app
    st.header('Discrepancy Counts Between Sales Reporting Logic and dsr2rdb')
    st.write(f"Number of 'Potential No.' in Sales Reporting Logic not present in dsr2rdb: {count_sales_not_in_dsr2}")
    st.write(f"Number of 'Potential No.' in dsr2rdb not present in Sales Reporting Logic: {count_dsr2_not_in_sales}")
    
    # Give the option to expand and see the actual Potential No. lists
    with st.expander("Show 'Potential No.' in Sales Reporting Logic not in dsr2rdb"):
        st.write(list(sales_not_in_dsr2))
    
    with st.expander("Show 'Potential No.' in dsr2rdb not in Sales Reporting Logic"):
        st.write(list(dsr2_not_in_sales))

# ==========================
# Creating Filtered DataFrames for Saving
# ==========================

# The p1rdb_filtered is essentially the same as p1rdb after processing
p1rdb_filtered = p1rdb.copy()

# The dsr1rdb_filtered is the same as dsr1rdb after processing
dsr1rdb_filtered = dsr1rdb.copy()

# p2rdb_filtered and dsr2rdb_filtered are already defined above

# ==========================
# Saving DataFrames
# ==========================

# Save all core DataFrames to their respective SQLite database files in the `database_path`
save_df_to_db(p1rdb, database_path / 'p1rdb.db', 'p1rdb')
save_df_to_db(p2rdb, database_path / 'p2rdb.db', 'p2rdb')
save_df_to_db(dsr1rdb, database_path / 'dsr1rdb.db', 'dsr1rdb')
save_df_to_db(dsr2rdb, database_path / 'dsr2rdb.db', 'dsr2rdb')
save_df_to_db(main_rdb, database_path / 'main_rdb.db', 'main_rdb')
save_df_to_db(weekly_rdb, database_path / 'weekly_rdb.db', 'weekly_rdb')
save_df_to_db(modified_rdb, database_path / 'modified_rdb.db', 'modified_rdb')

# Save filtered DataFrames to their own SQLite database files
save_df_to_db(p1rdb_filtered, database_path / 'p1rdb_filtered.db', 'p1rdb_filtered')
save_df_to_db(p2rdb_filtered, database_path / 'p2rdb_filtered.db', 'p2rdb_filtered')
save_df_to_db(dsr1rdb_filtered, database_path / 'dsr1rdb_filtered.db', 'dsr1rdb_filtered')
save_df_to_db(dsr2rdb_filtered, database_path / 'dsr2rdb_filtered.db', 'dsr2rdb_filtered')

# Save sales_reporting_logic to SQLite under both `database_path` and `base_path`
save_df_to_db(sales_reporting_logic, database_path / 'sales_reporting_logic.db', 'sales_reporting_logic')

# Also save to the root `base_path` for convenience
save_df_to_db(modified_rdb, base_path / 'modified_rdb.db', 'modified_rdb')
save_df_to_db(sales_reporting_logic, base_path / 'sales_reporting_logic.db', 'sales_reporting_logic')
save_df_to_db(dsr2rdb, base_path / 'dsr2rdb.db', 'dsr2rdb')

# ==========================
# Display in Streamlit App
# ==========================

# Calculate total runtime
end_time = time.time()
runtime = end_time - start_time

# Display final data counts and runtime in Streamlit
st.header('Dataframes and Record Counts')

# Display the record count in main_rdb
st.subheader('Main RDB')
st.write(f"Number of records: {len(main_rdb)}")
# st.dataframe(main_rdb)  # Uncomment to display the entire DataFrame

st.subheader('Weekly RDB')
st.write(f"Number of records: {len(weekly_rdb)}")
# st.dataframe(weekly_rdb)  # Uncomment to display the entire DataFrame

st.subheader('Modified RDB')
st.write(f"Number of records: {len(modified_rdb)}")
# st.dataframe(modified_rdb)  # Uncomment to display the entire DataFrame

st.subheader('Sales Reporting Logic')
st.write(f"Number of records: {len(sales_reporting_logic)}")

# Display how many are common vs. new potentials
st.write(f"Number of common potentials (Existing): {common_potentials_count}")
st.write(f"Number of new potentials (New): {new_potentials_count}")

# Display the final sales_reporting_logic DataFrame
st.dataframe(sales_reporting_logic)

# Finally, show how long the script took to run
st.write(f"Runtime of the code: {runtime:.2f} seconds")
