import os
import json
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db

st.title("💧 Wastewater Monitoring Dashboard")

if not firebase_admin._apps:

    # ✅ Get secrets as dictionary
    firebase_dict = dict(os.environ["FIREBASE_KEY"])

    # ✅ Fix private key formatting
    firebase_dict["private_key"] = firebase_dict["private_key"].replace("\n", "\\n")

    # ✅ Create credential
    cred = credentials.Certificate(firebase_dict)

    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://wastewater-monitoring-sy-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

# Fetch data
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


