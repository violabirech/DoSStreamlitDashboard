pip install influxdb-client


import streamlit as st
import pandas as pd
import time
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from influxdb_client import InfluxDBClient, Point, WritePrecision

# --- CONFIG ---
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUXDB_TOKEN = "6gjE97dCC24hgOgWNmRXPqOS0pfc0pMSYeh5psL8e5u2T8jGeV1F17CU-U1z05if0jfTEmPRW9twNPSXN09SRQ=="
INFLUXDB_ORG = "Anormally Detection"
INFLUXDB_BUCKET = "realtime_dns"

# --- STREAMLIT SETUP ---
st.set_page_config(page_title="DNS Anomaly Dashboard", layout="wide")
st.title("🚨 Real-Time DNS Anomaly Detection")

# --- InfluxDB client ---
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()
from influxdb_client import WriteOptions
write_api = client.write_api(write_options=WriteOptions(batch_size=1))


@st.cache_resource
def load_model():
    return Pipeline([
        ('scaler', StandardScaler()),
        ('clf', IsolationForest(contamination=0.01, random_state=42))
    ])

model_pipeline = load_model()

def fetch_dns_data():
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -10m)
      |> filter(fn: (r) => r._measurement == "dns")
      |> filter(fn: (r) => r._field == "dns_rate" or r._field == "inter_arrival_time")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> limit(n: 5000)
    '''
    try:
        df = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        if isinstance(df, list):  # if multiple tables returned
            df = pd.concat(df, ignore_index=True)
        if not df.empty:
            df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
        return df
    except Exception as e:
        st.error(f"❌ Failed to fetch data from InfluxDB: {e}")
        return pd.DataFrame()

def detect_with_latency(data):
    start = time.time()
    preds = model_pipeline.fit_predict(data)
    latency = time.time() - start
    return preds, latency

def log_latency(latency):
    point = Point("model_latency").field("latency_sec", latency)
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

# --- MAIN LOGIC ---
dns_df = fetch_dns_data()

if not dns_df.empty and "dns_rate" in dns_df.columns and "inter_arrival_time" in dns_df.columns:
    try:
        features = dns_df[["dns_rate", "inter_arrival_time"]].dropna()
        preds, latency = detect_with_latency(features)
        dns_df["anomaly"] = preds
        log_latency(latency)

        st.metric("⏱ Model Latency (s)", f"{latency:.4f}")
        st.subheader("🚨 Detected Anomalies")
        st.dataframe(dns_df[dns_df["anomaly"] == -1])

        st.subheader("📈 DNS Rate Over Time")
        st.line_chart(dns_df.set_index("_time")["dns_rate"])

    except Exception as e:
        st.error(f"⚠️ Error during processing: {e}")
else:
    st.warning("⚠️ No valid data returned or required fields missing.")
