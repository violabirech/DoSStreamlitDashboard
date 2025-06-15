
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from influxdb_client import InfluxDBClient
import plotly.express as px

# --- Streamlit Page Setup ---
st.set_page_config(page_title="📡 Real-Time DNS Data Analysis", layout="wide")
st.title("📊 Real-Time DNS Data Analysis Dashboard")

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
|> filter(fn: (r) => r["_measurement"] == "dns_traffic")
|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
"""

df = query_api.query_data_frame(query)
df = pd.concat(df, ignore_index=True) if isinstance(df, list) else df
df = df.dropna().reset_index(drop=True)

if df.empty:
    st.warning("⚠️ No recent DNS traffic data found.")
    st.stop()

# --- Feature Selection ---
numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
selected_feature = st.sidebar.selectbox("Select Feature to Analyze", numeric_cols)

# --- Normalize and Standardize ---
min_max_scaled = MinMaxScaler().fit_transform(df[numeric_cols])
z_score_scaled = StandardScaler().fit_transform(df[numeric_cols])

normalized_df = pd.DataFrame(min_max_scaled, columns=numeric_cols)
standardized_df = pd.DataFrame(z_score_scaled, columns=numeric_cols)

# --- Visualization Section ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 Normalized Histogram")
    fig1 = px.histogram(normalized_df, x=selected_feature, nbins=30,
                        title=f"Histogram of Normalized {selected_feature}")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("📊 Standardized Boxplot")
    fig2 = px.box(standardized_df, y=selected_feature,
                  title=f"Boxplot of Standardized {selected_feature}")
    st.plotly_chart(fig2, use_container_width=True)

# --- Comparison Line Plot ---
st.subheader("📈 Line Plot: Original vs Scaled Values")
fig3 = px.line(title=f"First 50 Values - {selected_feature}")
fig3.add_scatter(x=list(range(50)), y=df[selected_feature][:50], mode='lines', name='Original')
fig3.add_scatter(x=list(range(50)), y=normalized_df[selected_feature][:50], mode='lines', name='Normalized')
fig3.add_scatter(x=list(range(50)), y=standardized_df[selected_feature][:50], mode='lines', name='Standardized')
st.plotly_chart(fig3, use_container_width=True)

# --- Raw Data (optional) ---
with st.expander("🔍 View Raw Data"):
    st.dataframe(df.head(20))
