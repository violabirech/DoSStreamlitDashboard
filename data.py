
pip install influxdb-client scikit-learn matplotlib pandas plotly
pip install streamlit pandas numpy 
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from influxdb_client import InfluxDBClient
import plotly.express as px
import requests

# --- Streamlit Page Setup ---
st.set_page_config(page_title="📡 DNS Anomaly Detection", layout="wide")
st.title("📡 Real-Time DNS Anomaly Detection using Isolation Forest")

# --- InfluxDB Configuration ---
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUXDB_TOKEN = "6gjE97dCC24hgOgWNmRXPqOS0pfc0pMSYeh5psL8e5u2T8jGeV1F17CU-U1z05if0jfTEmPRW9twNPSXN09SRQ=="
INFLUXDB_ORG = "Anormally Detection"
INFLUXDB_BUCKET = "realtime_dns"

# --- Query DNS Data from InfluxDB ---
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

query = f"""
from(bucket: "{INFLUXDB_BUCKET}")
|> range(start: -5m)
|> filter(fn: (r) => r["_measurement"] == "dns")
|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
"""

df = query_api.query_data_frame(query)
df = pd.concat(df, ignore_index=True) if isinstance(df, list) else df
df = df.dropna().reset_index(drop=True)

if df.empty:
    st.warning("⚠️ No DNS data found in the last 5 minutes. Please check your InfluxDB source.")
    st.stop()

# --- Isolation Forest Anomaly Detection ---
st.subheader("🧠 Anomaly Detection with Isolation Forest")

features = ["query_rate", "inter_request_time"]
if not all(f in df.columns for f in features):
    st.error("Required features not found in the dataset.")
    st.stop()


# Simulated DNS data stream
def generate_dns_data():
    return {
        "inter_arrival_time": np.random.uniform(0.001, 1.0),  # Realistic range
        "dns_rate": np.random.uniform(0, 100)  # Realistic range
    }

# Input form for manual predictions
st.header("Manual Input")
col1, col2 = st.columns(2)
with col1:
    inter_arrival_time = st.number_input(
        "Inter Arrival Time (seconds)",
        min_value=0.001,
        max_value=10.0,
        value=0.01938,
        step=0.001
    )
with col2:
    dns_rate = st.number_input(
        "DNS Rate",
        min_value=0.0,
        max_value=100.0,
        value=2.0,
        step=0.1
    )

if st.button("Detect Anomaly"):
    payload = {"inter_arrival_time": inter_arrival_time, "dns_rate": dns_rate}
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.predictions.append(result)
        st.success("Manual prediction successful!")
        st.json(result)
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling API: {e}")
# Real-time monitoring
st.header("Real-Time Monitoring")
if st.checkbox("Enable Live Stream", value=True):
    try:
        data = generate_dns_data()
        payload = {
            "inter_arrival_time": data["inter_arrival_time"],
            "dns_rate": data["dns_rate"]
        }
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.predictions.append(result)
        st.session_state.predictions = st.session_state.predictions[-100:]
    except requests.exceptions.RequestException as e:
        st.error(f"Error in live stream: {e}")

# Display predictions
if st.session_state.predictions:
    df = pd.DataFrame(st.session_state.predictions)
    st.subheader("Recent Predictions")
    st.dataframe(df[["timestamp", "inter_arrival_time", "dns_rate", "request_rate", "reconstruction_error", "anomaly"]])
    st.subheader("Reconstruction Error Over Time")
    fig_line = px.line(df, x="timestamp", y="reconstruction_error", color="anomaly",
                       color_discrete_map={0: "blue", 1: "red"},
                       title="Real-Time Reconstruction Error (Red = Attack, Blue = Normal)")
    fig_line.add_hline(y=0.1, line_dash="dash", line_color="green", annotation_text="Threshold (0.1)")
    st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("Anomaly Distribution")
    anomaly_counts = df["anomaly"].value_counts().reset_index()
    anomaly_counts.columns = ["Anomaly", "Count"]
    anomaly_counts["Anomaly"] = anomaly_counts["Anomaly"].map({0: "Normal", 1: "Attack"})
    fig_bar = px.bar(anomaly_counts, x="Anomaly", y="Count",
                     title="Normal vs. Attack Counts", color="Anomaly",
                     color_discrete_map={"Normal": "blue", "Attack": "red"})
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Predictions", len(df))
    col2.metric("Attack Rate", f"{df['anomaly'].mean():.2%}")
    col3.metric("Recent Attacks", df.tail(10)["anomaly"].sum())
else:
    st.info("No predictions yet. Enable live stream or use manual input.")
