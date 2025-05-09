import streamlit as st
import pandas as pd
import glob
from pathlib import Path
import os

st.set_page_config(page_title="Parquet File Inspector", page_icon="🔍", layout="wide")


def get_parquet_files():
    """Get all parquet files in the data directory."""
    parquet_files = glob.glob("data/*.parquet")
    return sorted(parquet_files, key=os.path.getctime, reverse=True)


def load_parquet_file(file_path):
    """Load a parquet file into a pandas DataFrame."""
    return pd.read_parquet(file_path)


# Title and description
st.title("🔍 Parquet File Inspector")
st.markdown("""
This tool helps you inspect the contents of parquet files in the data directory.
You can:
- Select a file to inspect
- Choose which columns to display
- Navigate through the data
- Search and filter the contents
""")

# File selection
parquet_files = get_parquet_files()
if not parquet_files:
    st.error("No parquet files found in the data directory.")
    st.stop()

selected_file = st.selectbox(
    "Select a parquet file to inspect",
    parquet_files,
    format_func=lambda x: Path(x).name,
)

# Load the selected file
df = load_parquet_file(selected_file)

# Display file info
st.subheader("File Information")
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Rows", len(df))
with col2:
    st.metric("Total Columns", len(df.columns))

# Column selection
st.subheader("Column Selection")
all_columns = df.columns.tolist()
selected_columns = st.multiselect(
    "Select columns to display", all_columns, default=all_columns
)

if not selected_columns:
    st.warning("Please select at least one column to display.")
    st.stop()

# Filter the DataFrame to selected columns
df_display = df[selected_columns]

# Search functionality
st.subheader("Search")
search_term = st.text_input("Search in all columns", "")
if search_term:
    # Create a mask for each column
    mask = pd.Series(False, index=df_display.index)
    for col in df_display.columns:
        # Convert column to string and search
        mask |= (
            df_display[col].astype(str).str.contains(search_term, case=False, na=False)
        )
    df_display = df_display[mask]

# Pagination
st.subheader("Data Preview")
rows_per_page = st.slider("Rows per page", 5, 100, 20)
total_pages = len(df_display) // rows_per_page + (
    1 if len(df_display) % rows_per_page > 0 else 0
)
page = st.number_input("Page", 1, total_pages, 1)

# Calculate start and end indices
start_idx = (page - 1) * rows_per_page
end_idx = min(start_idx + rows_per_page, len(df_display))

# Display the data
st.dataframe(df_display.iloc[start_idx:end_idx], use_container_width=True, height=400)

# Pagination info
st.caption(f"Showing rows {start_idx + 1} to {end_idx} of {len(df_display)}")

# Column statistics
st.subheader("Column Statistics")
for col in selected_columns:
    with st.expander(f"Statistics for {col}"):
        st.write(df[col].describe())
