import os
import json
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Wastewater Monitoring System",
    page_icon="💧",
    layout="wide"
)

st.title("💧 Wastewater Monitoring Dashboard")

# ------------------ FIREBASE INIT ------------------
if not firebase_admin._apps:
    firebase_dict = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate(firebase_dict)

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://wastewater-monitoring-sy-default-rtdb.asia-southeast1.firebasedatabase.app/"
        },
    )

# ------------------ LOCATION SELECT ------------------
st.subheader("🌍 Select Location")

country = st.selectbox("Country", ["India"])

states_ref = db.reference("states")
states_data = states_ref.get()

selected_state = None
selected_company = None

if states_data:
    states = list(states_data.keys())
    selected_state = st.selectbox("State", ["Select State"] + states)

    if selected_state != "Select State":
        companies = list(states_data[selected_state].keys())
        selected_company = st.selectbox("Company", ["Select Company"] + companies)
else:
    st.error("No states found in database")

# ------------------ FETCH DATA ------------------
df = pd.DataFrame()

if selected_state and selected_company and selected_company != "Select Company":

    ref = db.reference(f"states/{selected_state}/{selected_company}/readings")
    data = ref.get()

    if data:
        df = pd.DataFrame(data).T

        # Convert timestamp safely
        try:
            df["timestamp"] = pd.to_datetime(df.index.astype(int), unit="s")
        except:
            st.error("Invalid timestamp format")
            st.stop()

        df = df.sort_values("timestamp")

        # ------------------ OPTIONAL FILTER ------------------
        use_filter = st.checkbox("Show only last 24 hours", value=False)

        if use_filter:
            now = datetime.now()
            last_24 = now - timedelta(hours=24)
            df = df[df["timestamp"] >= last_24]

    else:
        st.warning("No readings found")

# ------------------ MAIN LOGIC ------------------
if not df.empty:

    # ------------------ SAFE LATEST ------------------
    if len(df) > 0:
        latest = df.iloc[-1]
    else:
        st.warning("No recent data found")
        st.stop()

    st.caption(f"Last Updated: {latest.name}")

    # ------------------ SELECT TYPE ------------------
    st.subheader("⚙️ Select Data Type")
    data_type = st.selectbox("Choose Data", ["primary", "secondary", "tertiary"])

    # ------------------ PARAMETERS ------------------
    parameters = [
        "ph", "colour", "odour", "turbidity", "conductivity",
        "tds", "suspended_solids", "calcium", "magnesium",
        "alkalinity_ph", "alkalinity_mo", "sulphate",
        "chlorides", "silica", "iron", "cod", "bod",
        "hardness", "chlorine"
    ]

    # ------------------ TABLE ------------------
    table_data = []

    for i, param in enumerate(parameters, start=1):

        if param in latest and isinstance(latest[param], dict):
            value = latest[param].get(data_type, "NA")
        else:
            value = "NA"

        table_data.append({
            "Sl.No": i,
            "Parameter": param.upper(),
            "Value": value
        })

    table_df = pd.DataFrame(table_data)

    st.subheader("📋 Water Analysis Report")
    st.dataframe(table_df, use_container_width=True)

    # ------------------ CHARTS ------------------
    st.subheader("📊 24 Hour Trends")

    df = df.set_index("timestamp")

    for param in ["ph", "cod", "tds"]:
        st.markdown(f"### 📈 {param.upper()} Trend")

        if param in df.columns:
            df[f"{param}_sel"] = df[param].apply(
                lambda x: x.get(data_type, None) if isinstance(x, dict) else None
            )

            st.line_chart(df[f"{param}_sel"])
        else:
            st.warning(f"{param.upper()} data not available")

    # ------------------ DEBUG (REMOVE LATER) ------------------
    with st.expander("🔍 Debug Data"):
        st.write(df.tail())

else:
    st.info("No data available for selected company")
