# Install required libraries
!pip install streamlit scikit-learn pandas matplotlib --quiet


import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import time

# --- Set Page Config ---
st.set_page_config(page_title="DoS Anomaly Detection Dashboard", layout="wide")
st.title("🚨 Real-Time DoS Anomaly Detection Dashboard")

# --- Model Setup ---
model = IsolationForest(contamination=0.05, random_state=42)
scaler = StandardScaler()

# --- Simulated Live Data Function ---
def simulate_dos_traffic(batch_size=10):
    np.random.seed(int(time.time()) % 100000)
    return pd.DataFrame({
        'packet_length': np.random.normal(loc=500, scale=100, size=batch_size),
        'inter_arrival_time': np.random.exponential(scale=1.5, size=batch_size)
    })

# --- App State ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["packet_length", "inter_arrival_time", "anomaly"])

# --- Stream Simulation ---
st.sidebar.subheader("Simulation Settings")
batch_size = st.sidebar.slider("Packets per refresh", min_value=5, max_value=50, value=10, step=5)
refresh_interval = st.sidebar.slider("Refresh interval (sec)", min_value=1, max_value=10, value=3)

if st.sidebar.button("Start Simulation"):
    st.session_state.run = True

if st.sidebar.button("Stop Simulation"):
    st.session_state.run = False

# --- Main Display Loop ---
if st.session_state.get("run", False):
    placeholder = st.empty()
    for _ in range(100):  # simulate 100 refresh cycles
        new_data = simulate_dos_traffic(batch_size)
        full_data = pd.concat([st.session_state.data.drop(columns="anomaly", errors="ignore"), new_data], ignore_index=True)

        scaled = scaler.fit_transform(full_data)
        preds = model.fit_predict(scaled)
        full_data["anomaly"] = preds

        st.session_state.data = full_data

        with placeholder.container():
            st.subheader("📊 Live Traffic Data")
            st.dataframe(full_data.tail(20), use_container_width=True)

            st.subheader("🔍 Anomaly Count")
            st.bar_chart(full_data['anomaly'].value_counts())

            fig, ax = plt.subplots()
            ax.scatter(full_data["packet_length"], full_data["inter_arrival_time"],
                       c=full_data["anomaly"], cmap="coolwarm", alpha=0.7)
            ax.set_xlabel("Packet Length")
            ax.set_ylabel("Inter-Arrival Time")
            ax.set_title("Packet Distribution with Anomaly Label")
            st.pyplot(fig)

        time.sleep(refresh_interval)

# Download the dashboard script
from google.colab import files
files.download("dos_dashboard.py")
