import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import credentials, db

st.title("💧 Wastewater Monitoring Dashboard")

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://wastewater-monitoring-sy-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

# Fetch data from Firebase
ref = db.reference("/")
data = ref.get()

ph = data["ph"]
cod = data["cod"]
tds = data["tds"]
temperature = data["temperature"]

st.subheader("Current Sensor Readings")

st.metric("pH Level", ph)
st.metric("COD (mg/L)", cod)
st.metric("TDS (ppm)", tds)
st.metric("Temperature (°C)", temperature)

# Alert system
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