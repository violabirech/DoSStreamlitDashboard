

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from influxdb_client import InfluxDBClient
import plotly.express as px

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
st.subheader("🧾 Available Columns from InfluxDB")
st.write(df.columns.tolist())


if df.empty:
    st.warning("⚠️ No DNS data found in the last 5 minutes.")
    st.stop()

# --- Isolation Forest Anomaly Detection ---
st.subheader("🧠 Anomaly Detection on Fields: dns_rate, inter_arrival_time")

features = ["dns_rate", "inter_arrival_time"]
if not all(f in df.columns for f in features):
    st.error("Required fields not found in data.")
    st.write("Available columns:", df.columns.tolist())
    st.stop()

X = df[features]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = IsolationForest(contamination=0.05, random_state=42)
df["anomaly"] = model.fit_predict(X_scaled)
df["anomaly"] = df["anomaly"].apply(lambda x: 1 if x == -1 else 0)

# --- Visualization: dns_rate over time ---
st.subheader("📈 DNS Rate with Anomaly Overlay")

fig = px.line(df, x="_time", y="dns_rate",
              color=df["anomaly"].map({1: "Anomaly", 0: "Normal"}),
              title="DNS Rate with Detected Anomalies",
              labels={"_time": "Time", "dns_rate": "DNS Rate"})
st.plotly_chart(fig, use_container_width=True)

# --- Show Recent Records ---
st.subheader("🔍 Recent Records")
st.dataframe(df[["_time", "dns_rate", "inter_arrival_time", "packet_length", "anomaly"]].tail(10))
