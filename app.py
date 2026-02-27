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

# ------------------ FETCH DATA ------------------
ref = db.reference("readings")
data = ref.get()

if data:
    df = pd.DataFrame(data).T

    # Convert timestamp index to datetime
    df["timestamp"] = pd.to_datetime(df.index.astype(int), unit="s")
    df = df.sort_values("timestamp")

    latest = df.iloc[-1]

    ph = latest.get("ph", "N/A")
    cod = latest.get("cod", "N/A")
    tds = latest.get("tds", "N/A")
    temp = latest.get("temperature", "N/A")

else:
    df = pd.DataFrame()
    ph = cod = tds = temp = "No Data"

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
    st.line_chart(
        df.set_index("timestamp")[["ph", "cod", "tds", "temperature"]]
    )
else:
    st.info("No historical data available yet.")
