import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from growth_analysis import plot_logest_growth_from_csv

st.set_page_config(layout="wide")

st.title("India FoodCrop Dashboard")

# Sidebar selections
main_sector = st.sidebar.selectbox("Select Main Sector", ["Agriculture", "Allied Sectors"])
sub_sectors = {
    "Agriculture": ["Cereals", "Pulses", "Oilseeds"],
    "Allied Sectors": ["Livestock", "Fisheries"]
}

sub_sector = st.sidebar.selectbox("Select Sub-sector", sub_sectors[main_sector])
categories = {
    "Cereals": ["Rice", "Wheat"],
    "Pulses": ["Gram", "Tur"],
    "Oilseeds": ["Groundnut", "Soyabean"],
    "Livestock": ["Milk", "Meat"],
    "Fisheries": ["Inland", "Marine"]
}

category = st.sidebar.selectbox("Select Category", categories[sub_sector])
analysis_options = ["Trend Growth Rate", "Heatmap"]
analysis_type = st.sidebar.radio("Select Analysis Type", analysis_options)

# Optional district/state-wise selectors for Heatmap
state_option = None
if analysis_type == "Heatmap":
    state_option = st.sidebar.selectbox("Select State (for district-wise heatmap)", ["None", "Andhra Pradesh", "Maharashtra", "Uttar Pradesh"])  # Extend as needed

# File path
base_folder = f"data/{main_sector}/{sub_sector}/{category}"
growth_csv = os.path.join(base_folder, "growth.csv")

if analysis_type == "Trend Growth Rate":
    if os.path.exists(growth_csv):
        fig = plot_logest_growth_from_csv(growth_csv, category)
        if fig:
            st.pyplot(fig)
    else:
        st.warning("Data not available for that specific category")

elif analysis_type == "Heatmap":
    if state_option and state_option != "None":
        heatmap_csv = os.path.join(base_folder, f"heatmap_{state_option.replace(' ', '_')}.csv")
    else:
        heatmap_csv = os.path.join(base_folder, "heatmap.csv")

    if os.path.exists(heatmap_csv):
        try:
            df_heat = pd.read_csv(heatmap_csv)
            if {'District', 'Year', 'Value'}.issubset(df_heat.columns):
                pivot_df = df_heat.pivot("District", "Year", "Value")
                plt.figure(figsize=(12, 8))
                sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap="YlGnBu")
                plt.title(f"{category} Heatmap")
                st.pyplot(plt)
            else:
                st.warning("Heatmap file must contain 'District', 'Year', and 'Value' columns")
        except Exception as e:
            st.warning(f"Error reading heatmap: {e}")
    else:
        st.warning("Data not available for that specific category")
