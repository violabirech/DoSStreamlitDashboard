@st.cache_data
def load_dns_data_from_influx():
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.warnings import MissingPivotFunction
    import warnings
    warnings.simplefilter("ignore", MissingPivotFunction)

    url = "https://us-east-1-1.aws.cloud2.influxdata.com"
    token = "6gjE97dCC24hgOgWNmRXPqOS0pfc0pMSYeh5psL8e5u2T8jGeV1F17CU-U1z05if0jfTEmPRW9twNPSXN09SRQ=="
    org = "Anormally Detection"
    bucket = "realtime_dns"

    client = InfluxDBClient(url=url, token=token, org=org)

    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -7d)
      |> filter(fn: (r) => r._measurement == "dns")
      |> filter(fn: (r) => r._field == "dns_rate" or r._field == "inter_arrival_time" or r._field == "label")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> limit(n: 10000)
    '''

    try:
        tables = client.query_api().query_data_frame(query)
        df = pd.concat(tables) if isinstance(tables, list) else tables
        client.close()

        # Rename and check required columns
        df = df.rename(columns={
            "dns_rate": "dns_rate",
            "inter_arrival_time": "inter_arrival_time",
            "label": "label"
        })

        required = ["inter_arrival_time", "dns_rate", "label"]
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing columns in InfluxDB response: {df.columns.tolist()}")

        # Feature engineering
        df["request_rate"] = 1 / df["inter_arrival_time"]
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.fillna(method="ffill", inplace=True)
        return df

    except Exception as e:
        st.error(f"❌ Failed to load DNS data from InfluxDB: {e}")
        return pd.DataFrame(columns=["inter_arrival_time", "dns_rate", "request_rate", "label"])
