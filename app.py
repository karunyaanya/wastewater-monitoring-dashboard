import os
import json
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

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

states_data = db.reference("states").get()

selected_state = None
selected_company = None

if states_data:
    selected_state = st.selectbox("State", ["Select State"] + list(states_data.keys()))

    if selected_state != "Select State":
        selected_company = st.selectbox(
            "Company",
            ["Select Company"] + list(states_data[selected_state].keys())
        )
else:
    st.error("No states found")

# ------------------ FETCH DATA ------------------
df = pd.DataFrame()

if selected_state and selected_company and selected_company != "Select Company":

    ref = db.reference(f"states/{selected_state}/{selected_company}/readings")
    data = ref.get()

    if data:
        df = pd.DataFrame(data).T

        df["timestamp"] = pd.to_datetime(df.index.astype(int), unit="s")
        df = df.sort_values("timestamp")

        use_filter = st.checkbox("Show only last 24 hours", value=False)

        if use_filter:
            now = datetime.now()
            df = df[df["timestamp"] >= now - timedelta(hours=24)]

    else:
        st.warning("No readings found")

# ------------------ SAFE FUNCTION ------------------
def safe_get(x, key):
    if isinstance(x, dict):
        val = x.get(key)
        try:
            return float(val)
        except:
            return None
    return None

# ------------------ MAIN ------------------
if not df.empty:

    latest = df.iloc[-1]
    st.caption(f"Last Updated: {latest.name}")

    # ------------------ TABLE ------------------
    st.subheader("📋 Water Analysis Report")

    data_type = st.selectbox("Choose Data", ["primary", "secondary", "tertiary"])

    parameters = [
        "ph", "colour", "odour", "turbidity", "conductivity",
        "tds", "suspended_solids", "calcium", "magnesium",
        "alkalinity_ph", "alkalinity_mo", "sulphate",
        "chlorides", "silica", "iron", "cod", "bod",
        "hardness", "chlorine"
    ]

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

    st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    # ------------------ CHARTS ------------------
    st.subheader("📊 Parameter Trends")

    df = df.set_index("timestamp")

    for param in parameters:

        if param in df.columns:

            st.markdown(f"## 📌 {param.upper()}")

            # Extract numeric values
            df[f"{param}_primary"] = df[param].apply(lambda x: safe_get(x, "primary"))
            df[f"{param}_secondary"] = df[param].apply(lambda x: safe_get(x, "secondary"))
            df[f"{param}_tertiary"] = df[param].apply(lambda x: safe_get(x, "tertiary"))

            chart_df = df[
                [f"{param}_primary", f"{param}_secondary", f"{param}_tertiary"]
            ].dropna(how="all")

            if not chart_df.empty:

                # -------- LINE --------
                st.line_chart(chart_df)

                # -------- BAR --------
                latest_vals = chart_df.iloc[-1]
                bar_df = pd.DataFrame({
                    "Type": ["Primary", "Secondary", "Tertiary"],
                    "Value": latest_vals.values
                }).set_index("Type")

                st.bar_chart(bar_df)

                # -------- PIE --------
                pie_vals = latest_vals.dropna()

                if not pie_vals.empty:
                    fig, ax = plt.subplots()
                    ax.pie(
                        pie_vals.values,
                        labels=["Primary", "Secondary", "Tertiary"][:len(pie_vals)],
                        autopct="%1.1f%%"
                    )
                    ax.set_title(param.upper())
                    st.pyplot(fig)
                else:
                    st.warning("No valid data for pie")

            else:
                st.warning("No usable data")

        else:
            st.warning(f"{param.upper()} missing")

else:
    st.info("No data available")
