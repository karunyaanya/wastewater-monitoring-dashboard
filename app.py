import os
import json
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db

st.set_page_config(
    page_title="Wastewater Monitoring System",
    page_icon="💧",
    layout="wide"
)

st.title("💧 Wastewater Monitoring Dashboard")

if not firebase_admin._apps:
    firebase_dict = json.loads(os.environ["FIREBASE_KEY"])

    cred = credentials.Certificate(firebase_dict)

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://wastewater-monitoring-sy-default-rtdb.asia-southeast1.firebasedatabase.app/"
        },
    )

# Fetch data
ref = db.reference("/")
data = ref.get()

if data:
    ph = data.get("ph", "N/A")
    cod = data.get("cod", "N/A")
    tds = data.get("tds", "N/A")
    temp = data.get("temperature", "N/A")
else:
    ph = cod = tds = temp = "No Data"

st.subheader("Current Sensor Readings")

st.metric("pH Level", ph)
st.metric("COD (mg/L)", cod)
st.metric("TDS (ppm)", tds)
st.metric("Temperature (°C)", temp)

# Alerts
if ph > 8:
    st.error("⚠ pH level is too high!")
elif ph < 6.5:
    st.warning("⚠ pH level is too low!")
else:
    st.success("✅ pH level is normal")

# Graph
data_graph = pd.DataFrame({
    "Time": range(10),
    "pH": [ph for _ in range(10)]
})

st.subheader("pH Trend")
st.line_chart(data_graph.set_index("Time"))
