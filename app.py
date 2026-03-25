import os
import json
import base64
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

# ------------------ CSS ------------------
st.markdown("""
<style>
.block-container {
    padding-top: 0rem;
}

/* CENTER LOGO */
.center-logo {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
}

.center-logo img {
    width: 220px;
}

/* CENTER TITLE */
.center-title {
    text-align: center;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ LOAD IMAGE ------------------
def get_base64(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64("logo.png")

# ------------------ DISPLAY LOGO ------------------
st.markdown(f"""
<div class="center-logo">
    <img src="data:image/png;base64,{img_base64}">
</div>
""", unsafe_allow_html=True)

# ------------------ TITLE ------------------
st.markdown(
    "<h1 class='center-title'>💧 Wastewater Monitoring Dashboard</h1>",
    unsafe_allow_html=True
)

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
        try:
            return float(x.get(key, 0))
        except:
            return 0
    return 0

# ------------------ MAIN ------------------
if not df.empty:

    latest = df.iloc[-1]
    st.caption(f"Last Updated: {latest.name}")

    # ------------------ COMBINED TABLE ------------------
    st.subheader("📋 Water Analysis Report")

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
            primary = latest[p].get("primary", "NA")
            secondary = latest[p].get("secondary", "NA")
            tertiary = latest[p].get("tertiary", "NA")
        else:
            primary = secondary = tertiary = "NA"

        table.append({
            "Sl.No": i,
            "Parameter": p.upper(),
            "Primary": primary,
            "Secondary": secondary,
            "Tertiary": tertiary
        })

    df_table = pd.DataFrame(table)

    st.dataframe(df_table, use_container_width=True)

    # ------------------ CHARTS ------------------
    st.subheader("📊 Parameter Dashboard")

    df = df.set_index("timestamp")

    for param in parameters:

        if param in df.columns:

            with st.expander(f"📌 {param.upper()}"):

                temp_df = pd.DataFrame()
                temp_df["Primary"] = df[param].apply(lambda x: safe_get(x, "primary"))
                temp_df["Secondary"] = df[param].apply(lambda x: safe_get(x, "secondary"))
                temp_df["Tertiary"] = df[param].apply(lambda x: safe_get(x, "tertiary"))

                temp_df = temp_df.fillna(0)
                temp_df.index = df.index

                if not temp_df.empty:

                    col1, col2, col3 = st.columns(3)
                    latest_vals = temp_df.iloc[-1]

                    with col1:
                        st.markdown("📈 Line Chart")
                        if len(temp_df) > 1:
                            st.line_chart(temp_df)

                    with col2:
                        st.markdown("📊 Bar Chart")
                        bar_df = pd.DataFrame({
                            "Type": ["Primary", "Secondary", "Tertiary"],
                            "Value": latest_vals.values
                        }).set_index("Type")
                        st.bar_chart(bar_df)

                    with col3:
                        st.markdown("🥧 Pie Chart")
                        if latest_vals.sum() > 0:
                            fig, ax = plt.subplots()
                            ax.pie(
                                latest_vals.values,
                                labels=["Primary", "Secondary", "Tertiary"],
                                autopct="%1.1f%%"
                            )
                            st.pyplot(fig)
