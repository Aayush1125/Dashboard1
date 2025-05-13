import streamlit as st 
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from growth_analysis import plot_logest_growth_from_csv

# Page setup
st.set_page_config(layout="wide", page_title="India FoodCrop Dashboard", page_icon="🌾")

# ---------- CUSTOM CSS --------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.toggle-container {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin: 2.5rem 0 1rem;
}

.toggle-button {
    font-size: 2rem;
    padding: 1.2rem 3rem;
    border-radius: 12px;
    border: 2px solid #ccc;
    background-color: white;
    color: black;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}

.toggle-button:hover {
    transform: scale(1.1);
    background-color: #f0f0f0;
}

.toggle-button.selected {
    background-color: black;
    color: white;
    transform: scale(1.2);
}

.sidebar-title {
    background-color: white;
    padding: 1rem;
    font-size: 1.3rem;
    font-weight: 700;
    border-radius: 15px;
    margin-bottom: 1rem;
    text-align: center;
    color: #111;
}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if "selected_type" not in st.session_state:
    st.session_state.selected_type = None

# ---------- TOGGLE BUTTONS ----------
st.markdown('<div class="toggle-container">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("Production", key="prod"):
        st.session_state.selected_type = "Production"
with col2:
    if st.button("Yield", key="yield"):
        st.session_state.selected_type = "Yield"
with col3:
    if st.button("Area", key="area"):
        st.session_state.selected_type = "Area"
st.markdown('</div>', unsafe_allow_html=True)

selected_type = st.session_state.selected_type
if not selected_type:
    st.markdown("<h4 style='text-align:center;'>Please select <b>Production</b>, <b>Yield</b>, or <b>Area</b> to continue.</h4>", unsafe_allow_html=True)
    st.stop()

# ---------- HEADER ----------
st.markdown(f"<h1 style='text-align:center;'>🌾 India FoodCrop Data Dashboard</h1>", unsafe_allow_html=True)

# ---------- FILE SETUP ----------
base_path = f"Data/{selected_type}"
prefix = selected_type.lower() + "_"

categories = [
    f.replace(prefix, "").replace("_", " ").title()
    for f in os.listdir(base_path)
    if os.path.isdir(os.path.join(base_path, f))
]

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown(f"<div class='sidebar-title'>{selected_type} Categories</div>", unsafe_allow_html=True)
    selected_category = st.radio("Select Category", categories, label_visibility="collapsed")

folder_name = f"{prefix}{selected_category.lower()}"
folder_path = os.path.join(base_path, folder_name)

def safe_read(filename):
    full_path = os.path.join(folder_path, filename)
    return pd.read_csv(full_path) if os.path.exists(full_path) else None

# ---------- LOAD DATA ----------
historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
wg_df = safe_read("wg_report.csv")
state_df = safe_read("statewise_data.csv")
district_df = safe_read("districtwise_data.csv")
# Load custom Tableau forecast CSV (if needed globally)
tableau_forecast_df = pd.read_csv("Pulses_forecast_tableau.csv")

# ---------- LOGEST GRAPH ----------
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)
else:
    st.warning("Historical growth data not available for this category.")

# ---------- FORECAST GRAPH ----------
if historical_df is not None and forecast_df is not None:
    st.subheader("📊 Historical and Predicted Forecasts")
    fig = px.line()
    fig.add_scatter(x=historical_df["Year"], y=historical_df["Total"], mode="lines+markers", name="Historical", line=dict(color="black"))

    for col in forecast_df.columns[1:]:
        fig.add_scatter(x=forecast_df["Year"], y=forecast_df[col], mode="lines+markers", name=col)

    if wg_df is not None:
        fig.add_scatter(x=wg_df["Year"], y=wg_df["Value"], mode="markers+text", name="WG Report",
                        marker=dict(color="red", size=10),
                        text=wg_df["Scenario"], textposition="top right")

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Forecast or historical data not available for this category.")
st.subheader("📊 Tableau Forecast Data (Uploaded)")

if not tableau_forecast_df.empty:
    fig_tableau = px.line(
        tableau_forecast_df,
        x="Year",  # Replace with correct column name
        y=tableau_forecast_df.columns[1:],  # Automatically selects all other columns
        title="Forecast from Tableau Model"
    )
    st.plotly_chart(fig_tableau, use_container_width=True)
else:
    st.warning("Uploaded Tableau forecast CSV is empty.")

# ---------- HEATMAPS ----------
st.subheader("🗺️ India Heatmaps")
if state_df is not None:
    fig_state = px.choropleth(state_df, geojson="https://raw.githubusercontent.com/plotly/datasets/master/india_states.geojson",
                              featureidkey="properties.ST_NM",
                              locations="State", color="Value",
                              color_continuous_scale="Viridis",
                              scope="asia",
                              title="State-wise Heatmap")
    fig_state.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig_state, use_container_width=True)

    # State selection for district view
    states = state_df['State'].unique()
    selected_state = st.selectbox("Select State to View District-wise Data", states)

    if district_df is not None and selected_state in district_df['State'].unique():
        district_data = district_df[district_df['State'] == selected_state]
        fig_district = px.choropleth(district_data, geojson="https://raw.githubusercontent.com/plotly/datasets/master/india_districts.geojson",
                                     featureidkey="properties.district",
                                     locations="District", color="Value",
                                     color_continuous_scale="Plasma",
                                     title=f"District-wise Data for {selected_state}")
        fig_district.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_district, use_container_width=True)
    else:
        st.info("District-level data not available for the selected state.")
else:
    st.info("Heatmap data not available for this category.")
