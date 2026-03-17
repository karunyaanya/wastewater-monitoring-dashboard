import os
import json
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db

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
load_data = False

if states_data:
    states = list(states_data.keys())
    selected_state = st.selectbox("State", ["Select State"] + states)

    if selected_state != "Select State":
        companies = list(states_data[selected_state].keys())
        selected_company = st.selectbox("Company", ["Select Company"] + companies)

        if selected_company != "Select Company":
            load_data = st.button("✅ Load Data")
else:
    st.error("No states found in database")


# ------------------ FETCH DATA ------------------
df = pd.DataFrame()

if load_data:
    ref = db.reference(f"states/{selected_state}/{selected_company}/readings")
    data = ref.get()

    if data:
        df = pd.DataFrame(data).T
        df["timestamp"] = pd.to_datetime(df.index.astype(int), unit="s")
        df = df.sort_values("timestamp")
    else:
        st.warning("No readings found for this company")

   # from datetime import datetime, timedelta
    #now = datetime.now()
    #last_24_hours = now - timedelta(hours=24)

    #df = df[df["timestamp"] >= last_24_hours]

# ---------- SAFE METRIC EXTRACTION ----------
if not df.empty:
    latest = df.iloc[-1]
    ph = latest.get("ph", "N/A")
    cod = latest.get("cod", "N/A")
    tds = latest.get("tds", "N/A")
    temp = latest.get("temperature", "N/A")
else:
    ph = cod = tds = temp = "No Recent Data"
# ------------------ METRICS DISPLAY ------------------
st.subheader("Current Sensor Readings")

col1, col2, col3, col4 = st.columns(4)

col1.metric("pH Level", ph)
col2.metric("COD (mg/L)", cod)
col3.metric("TDS (ppm)", tds)
col4.metric("Temperature (°C)", temp)

# ------------------ ALERT SYSTEM ------------------
if isinstance(ph, (int, float)):
    if ph > 8:
        st.error("⚠ pH level is too high!")
    elif ph < 6.5:
        st.warning("⚠ pH level is too low!")
    else:
        st.success("✅ pH level is normal")

# ------------------ TREND GRAPH ------------------
if not df.empty:
    st.subheader("Sensor Trends Over Time")

    df = df.set_index("timestamp")

    # -------- LINE CHART --------
    st.markdown("### 📈 Line Chart")
    st.line_chart(df[["ph", "cod", "tds", "temperature"]])

    # -------- BAR CHART --------
    st.markdown("### 📊 Bar Chart (Latest Readings)")

    latest_values = df.iloc[-1][["ph", "cod", "tds", "temperature"]]

    bar_df = pd.DataFrame({
        "Parameter": latest_values.index,
        "Value": latest_values.values
    })

    st.bar_chart(bar_df.set_index("Parameter"))

    # -------- PIE CHART --------
    st.markdown("### 🥧 Pie Chart (Latest Distribution)")

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.pie(
        latest_values,
        labels=latest_values.index,
        autopct="%1.1f%%"
    )
    ax.set_title("Sensor Value Distribution")

    st.pyplot(fig)

else:
    st.info("No historical data available yet.")
