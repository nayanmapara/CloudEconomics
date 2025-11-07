import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="AWS EC2 & S3 Dashboard", layout="wide")

st.title("💡 AWS EC2 & S3 Usage EDA Dashboard")

st.markdown("""
### Assignment Insights & Optimization Notes
**EC2 Optimization Suggestions**
- Instances show low CPU Utilization while incurring cost → **Right‑size instance types**
- Non‑prod runs continuously → **stop instances using schedules**

**S3 Optimization Suggestions**
- Large buckets likely not accessed frequently → **enable lifecycle tiering (IA/Glacier)**
- Compression + AES256 → reduces storage + improves security
""")

ec2 = pd.read_csv('./aws_resources_compute.csv')
s3 = pd.read_csv('./aws_resources_S3.csv')

ec2_regions = sorted(ec2['Region'].dropna().unique())
s3_regions = sorted(s3['Region'].dropna().unique())

st.sidebar.header("Filters 🎛️")
ec2_region_filter = st.sidebar.multiselect("EC2 Regions", ec2_regions, default=ec2_regions)
s3_region_filter = st.sidebar.multiselect("S3 Regions", s3_regions, default=s3_regions)

ec2_f = ec2[ec2['Region'].isin(ec2_region_filter)]
s3_f = s3[s3['Region'].isin(s3_region_filter)]

st.subheader("Dataset Info & Summary")
with st.expander("EC2 Shape / Describe / Top 5 expensive / Avg Region Cost"):
    st.write("Shape:", ec2_f.shape)
    st.write(ec2_f.describe())
    st.write("Top 5 Most Expensive:")
    st.write(ec2_f.nlargest(5, 'CostUSD'))
    st.write("Average Cost Per Region:")
    st.write(ec2_f.groupby('Region')['CostUSD'].mean())

with st.expander("S3 Shape / Describe / Top 5 largest / Total Region Storage"):
    st.write("Shape:", s3_f.shape)
    st.write(s3_f.describe())
    st.write("Top 5 Largest Buckets:")
    st.write(s3_f.nlargest(5, 'TotalSizeGB'))
    st.write("Total Storage Per Region:")
    st.write(s3_f.groupby('Region')['TotalSizeGB'].sum())

col1, col2 = st.columns(2)

with col1:
    st.subheader("EC2 CPU Histogram")
    fig1, ax1 = plt.subplots()
    ax1.hist(ec2_f['CPUUtilization'].dropna())
    st.pyplot(fig1)

with col2:
    st.subheader("EC2 CPU vs Cost")
    fig2, ax2 = plt.subplots()
    ax2.scatter(ec2_f['CPUUtilization'], ec2_f['CostUSD'])
    ax2.set_xlabel("CPU Utilization")
    ax2.set_ylabel("Cost USD")
    st.pyplot(fig2)

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.subheader("S3 Storage by Region")
    region_storage = s3_f.groupby('Region')['TotalSizeGB'].sum()
    fig3, ax3 = plt.subplots()
    region_storage.plot(kind='bar', ax=ax3)
    st.pyplot(fig3)

with col4:
    st.subheader("S3 Cost vs Storage")
    fig4, ax4 = plt.subplots()
    ax4.scatter(s3_f['TotalSizeGB'], s3_f['CostUSD'])
    ax4.set_xlabel("Size (GB)")
    ax4.set_ylabel("Cost (USD)")
    st.pyplot(fig4)
