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

# ------------------ LOCATION ------------------
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

        if st.checkbox("Show last 24 hours"):
            df = df[df["timestamp"] >= datetime.now() - timedelta(hours=24)]

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

    table = []
    for i, p in enumerate(parameters, 1):
        if p in latest and isinstance(latest[p], dict):
            val = latest[p].get(data_type, "NA")
        else:
            val = "NA"

        table.append({"Sl.No": i, "Parameter": p.upper(), "Value": val})

    st.dataframe(pd.DataFrame(table), use_container_width=True)

    # ------------------ CHARTS ------------------
    st.subheader("📊 Parameter Dashboard")

    df = df.set_index("timestamp")

    for param in parameters:

        if param in df.columns:

            with st.expander(f"📌 {param.upper()}"):

                df[f"{param}_p"] = df[param].apply(lambda x: safe_get(x, "primary"))
                df[f"{param}_s"] = df[param].apply(lambda x: safe_get(x, "secondary"))
                df[f"{param}_t"] = df[param].apply(lambda x: safe_get(x, "tertiary"))

                chart_df = df[[f"{param}_p", f"{param}_s", f"{param}_t"]].dropna(how="all")

                if not chart_df.empty:

                    col1, col2, col3 = st.columns(3)

                    # -------- LINE --------
                    with col1:
                        st.markdown("📈 Line")
                        st.line_chart(chart_df)

                    # -------- BAR --------
                    with col2:
                        st.markdown("📊 Bar")
                        latest_vals = chart_df.iloc[-1]

                        bar_df = pd.DataFrame({
                            "Type": ["Primary", "Secondary", "Tertiary"],
                            "Value": latest_vals.values
                        }).set_index("Type")

                        st.bar_chart(bar_df)

                   # -------- PIE --------
with col3:
    st.markdown("🥧 Pie")

    pie_vals = pd.to_numeric(latest_vals, errors="coerce")

    # clean data
    pie_vals = pie_vals.dropna()
    pie_vals = pie_vals[pie_vals > 0]

    # STRICT CHECK (IMPORTANT)
    if len(pie_vals) >= 2 and pie_vals.sum() > 0:

        fig, ax = plt.subplots()

        ax.pie(
            pie_vals.values,
            labels=pie_vals.index,
            autopct="%1.1f%%"
        )

        ax.set_title(param.upper())
        st.pyplot(fig)

    else:
        st.info("Not enough valid data for pie chart")
