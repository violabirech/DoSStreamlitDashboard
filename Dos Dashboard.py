pip install scikit-learn
streamlit
pandas
numpy
matplotlib
scikit-learn
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt

st.set_page_config(page_title="DoS Anomaly Detection Dashboard", layout="wide")
st.title("🚨 DoS Anomaly Detection Dashboard")

# --- Load Dataset ---
df = pd.read_csv("Clean_DOS_Capstone.csv")
df = df[['packet_length', 'inter_arrival_time', 'protocol']]
df['protocol'] = LabelEncoder().fit_transform(df['protocol'])

# --- Display Preview ---
st.subheader("📋 Data Preview")
st.dataframe(df.head(10), use_container_width=True)

# --- Isolation Forest Pipeline ---
model_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', IsolationForest(contamination=0.01, random_state=42))
])

model_pipeline.fit(df)
df['anomaly'] = model_pipeline.predict(df)
df['anomaly'] = df['anomaly'].map({1: 'Normal', -1: 'Anomaly'})

# --- Visualization ---
st.subheader("📊 Anomaly Detection Result")

anomaly_count = df['anomaly'].value_counts()
st.write("🔍 Anomaly Distribution:", anomaly_count.to_dict())

chart_data = df.copy()
chart_data['Index'] = np.arange(len(df))

for feature in ['packet_length', 'inter_arrival_time']:
    st.write(f"### 📈 {feature} with Anomaly Overlay")
    fig, ax = plt.subplots()
    normal = chart_data[chart_data['anomaly'] == 'Normal']
    anomaly = chart_data[chart_data['anomaly'] == 'Anomaly']
    ax.plot(normal['Index'], normal[feature], label='Normal', alpha=0.5)
    ax.scatter(anomaly['Index'], anomaly[feature], color='red', label='Anomaly', s=10)
    ax.set_xlabel("Packet Index")
    ax.set_ylabel(feature)
    ax.legend()
    st.pyplot(fig)

# --- Summary ---
st.subheader("🧾 Summary Statistics")
st.write(df.describe())

st.caption("Built with ❤️ using Streamlit + Isolation Forest")
