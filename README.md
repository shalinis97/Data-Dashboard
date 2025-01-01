
# Data Processing and Streamlit Application Workflow

## Overview

This document outlines the workflow of two Python scripts:
1. **data_processing.py** - Handles data preprocessing and generates database files.
2. **demo9.py** - A Streamlit application that takes the output from `data_processing.py` and provides an interactive user interface.

---

## Workflow Details

### Step 1: Data Processing (`data_processing.py`)

1. **Objective**: Prepares and processes CSV files, performs data cleaning, and stores the results in SQLite databases.

2. **Input**:
   - Four CSV files (`p1.csv`, `p2.csv`, `dsr1.csv`, `dsr2.csv`) stored in the `new` folder in the user's home directory.

3. **Output**:
   - Three SQLite database files:
     - `sales_reporting_logic.db`
     - `modified_rdb.db`
     - `weekly_rdb.db`

4. **Key Functions**:
   - `process_p_data()`: Cleans and processes `p1` and `p2`.
   - `process_dsr_data()`: Cleans and processes `dsr1` and `dsr2`.
   - `save_df_to_db()`: Saves the processed DataFrame to an SQLite database.

5. **Additional Features**:
   - Filters records based on specific date thresholds.
   - Maps values in columns like `Stage` and `Category`.
   - Handles duplicate records.

---

### Step 2: Streamlit Application (`demo9.py`)

1. **Objective**: Provides an interactive UI for users to analyze and manage the data stored in the SQLite databases.

2. **Input**:
   - Database files:
     - `sales_reporting_logic.db`
     - `modified_rdb.db`

3. **Key Features**:
   - **Login and User Authentication**:
     - Users can log in with credentials.
     - Supports password hashing and reset functionality.
   - **Data Loading and Filtering**:
     - Loads data from the databases using efficient SQL queries.
     - Provides multiple filtering options for `Region`, `Executive`, `Stage`, and date criteria.
   - **Interactive Grids**:
     - Uses `AgGrid` for displaying and editing data interactively.
   - **Export and Bookmarking**:
     - Allows exporting filtered data to Excel.
     - Enables bookmarking specific records for quick access.

4. **Utility Functions**:
   - `dataframe_to_excel()`: Converts DataFrame to an Excel file with additional formatting.
   - `apply_filters()`: Applies cascading filters to the loaded data.

---

## How to Run

1. **Execute `data_processing.py`**:
   - Run this script to preprocess data and generate the required database files.

2. **Start the Streamlit Application (`demo9.py`)**:
   - Launch the Streamlit app using:
     ```bash
     streamlit run demo9.py
     ```
   - Interact with the UI to filter, analyze, and export data.

---

## Requirements

- Python 3.x
- Libraries:
  - `pandas`
  - `sqlite3`
  - `streamlit`
  - `st_aggrid`
  - `xlsxwriter`

---

## Notes

- Ensure the input CSV files (`p1.csv`, `p2.csv`, `dsr1.csv`, `dsr2.csv`) are placed in the `new` directory.
- The database files will be generated in the same directory.
- The Streamlit app provides a seamless interface for working with processed data.
