import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
import os
import re

st.set_page_config(page_title="CloudMart Tagging & Cost Visibility", layout="wide")

# -------------------------
# Helpers
# -------------------------
DEFAULT_PATH = "week10/cloudmart_multi_account.csv"
REMIDIATED_SAVE_PATH = "week10/remediated_cloudmart.csv"

TAG_FIELDS = [
    "Department",
    "Project",
    "Owner",
    "CostCenter",
    "CreatedBy"
]

COST_COL = "MonthlyCostUSD"
TAGGED_COL = "Tagged"


# Ensure dataset always has expected tag fields
def ensure_tag_fields(df, tag_fields):
    for f in tag_fields:
        if f not in df.columns:
            df[f] = np.nan
    return df


@st.cache_data(show_spinner=False)
def load_csv_from_path(path):
    # Your CSV uses quotes around every field → must specify quotechar + utf-8-sig
    with open(path, "r", encoding="utf-8-sig") as f:
        df = pd.read_csv(f, sep=",", quotechar='"', skipinitialspace=True, engine="python")
        return df


def compute_basic_stats(df):
    total_resources = len(df)
    tagged_counts = df[TAGGED_COL].value_counts(dropna=False).to_dict()
    num_tagged = tagged_counts.get("Yes", 0)
    num_untagged = tagged_counts.get("No", 0)
    return {
        "total_resources": total_resources,
        "num_tagged": num_tagged,
        "num_untagged": num_untagged
    }


def normalize_tagged_column(df):
    df[TAGGED_COL] = df[TAGGED_COL].astype(str).str.strip().str.capitalize()
    df.loc[~df[TAGGED_COL].isin(["Yes", "No"]), TAGGED_COL] = "No"
    return df


def ensure_cost_numeric(df):
    df[COST_COL] = pd.to_numeric(df[COST_COL], errors="coerce").fillna(0.0)
    return df


def tag_completeness_score(df, tag_fields=TAG_FIELDS):
    def non_empty_count(row):
        return sum(
            1 for f in tag_fields if f in row and pd.notna(row[f]) and str(row[f]).strip() != ""
        )

    df["_tag_completeness_score"] = df.apply(non_empty_count, axis=1)
    df["_tag_completeness_pct"] = df["_tag_completeness_score"] / len(tag_fields)
    return df


def compute_tagging_cost_summary(df):
    grouped = df.groupby(TAGGED_COL)[COST_COL].sum().reset_index(name="TotalCostUSD")
    total_cost = df[COST_COL].sum()
    untagged_cost = grouped[grouped[TAGGED_COL] == "No"]["TotalCostUSD"].sum()
    pct_untagged = (untagged_cost / total_cost * 100) if total_cost > 0 else 0.0
    return total_cost, untagged_cost, pct_untagged, grouped


def safe_save_df_to_csv(df, path):
    try:
        df.to_csv(path, index=False)
        return True, path
    except Exception as e:
        return False, str(e)


# -------------------------
# Load data
# -------------------------
st.title("📊 CloudMart — Resource Tagging & Cost Visibility")

uploaded_file = st.sidebar.file_uploader("Upload dataset CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(
        uploaded_file,
        sep=",",
        quotechar='"',
        skipinitialspace=True,
        engine="python",
        encoding="utf-8-sig"
    )
else:
    df = load_csv_from_path(DEFAULT_PATH)

df = ensure_tag_fields(df, TAG_FIELDS)
df = normalize_tagged_column(df)
df = ensure_cost_numeric(df)

df_original = df.copy()

# -------------------------
# Sidebar Filters
# -------------------------
services = sorted(df["Service"].dropna().unique())
regions = sorted(df["Region"].dropna().unique())
departments = sorted(df["Department"].dropna().unique())

selected_services = st.sidebar.multiselect("Service", services, services)
selected_regions = st.sidebar.multiselect("Region", regions, regions)
selected_departments = st.sidebar.multiselect("Department", departments, departments)

df_working = df[
    df["Service"].isin(selected_services) &
    df["Region"].isin(selected_regions) &
    df["Department"].isin(selected_departments)
]

# -------------------------
# Task Set 1
# -------------------------
st.header("Task Set 1 — Data Exploration")

st.subheader("Preview dataset")
st.dataframe(df_working.head())

st.subheader("Missing values summary")
st.dataframe(df_working.isnull().sum().sort_values(ascending=False))

# -------------------------
# Task Set 2
# -------------------------
st.header("Task Set 2 — Cost Visibility")

total_cost, untagged_cost, pct_untagged, cost_grouped = compute_tagging_cost_summary(df_working)

st.metric("Total Untagged Cost", f"${untagged_cost:.2f}")
st.metric("Percent Untagged", f"{pct_untagged:.2f}%")

st.dataframe(cost_grouped)

# -------------------------
# Task Set 3
# -------------------------
st.header("Task Set 3 — Tagging Compliance")

df_tc = tag_completeness_score(df_working.copy())
df_tc = ensure_tag_fields(df_tc, TAG_FIELDS)

cols = ["ResourceID"] + TAG_FIELDS + ["_tag_completeness_score"]
cols = [c for c in cols if c in df_tc.columns]

st.subheader("Completeness Table")
st.dataframe(df_tc[cols].head())

# -------------------------
# Task Set 4 — Visualization
# -------------------------
st.header("Task Set 4 — Visualization Dashboard")

tag_counts = df_working[TAGGED_COL].value_counts().reset_index()
tag_counts.columns = ["TagStatus", "Count"]

fig = px.pie(tag_counts, names="TagStatus", values="Count", title="Tagged vs Untagged")
st.plotly_chart(fig)

# -------------------------
# Task Set 5 — REMEDIATION WORKFLOW
# -------------------------
st.header("Task Set 5 — Tag Remediation Workflow")

global_untagged = df[df[TAGGED_COL] == "No"].copy()
global_untagged = ensure_tag_fields(global_untagged, TAG_FIELDS)

if global_untagged.empty:
    st.success("No untagged resources left!")
else:
    st.write("Edit missing tags below:")
    editable = st.data_editor(
        global_untagged[
            ["ResourceID", "Service", "Region", "Environment"] + TAG_FIELDS
        ].copy(),
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("Apply Remediation"):
        df_remediated = df.copy()

        # --------------------------------------------
        # SAFE MERGE (fixes InvalidIndexError)
        # --------------------------------------------
        df_remediated = df_remediated.merge(
            editable[["ResourceID"] + TAG_FIELDS],
            on="ResourceID",
            how="left",
            suffixes=("", "_edited")
        )

        # Apply edited fields where available
        for col in TAG_FIELDS:
            if col + "_edited" in df_remediated.columns:
                df_remediated[col] = df_remediated[col + "_edited"].combine_first(df_remediated[col])
                df_remediated.drop(columns=[col + "_edited"], inplace=True)

        # Update tagging status
        df_remediated[TAGGED_COL] = df_remediated.apply(
            lambda row: "Yes"
            if str(row["Department"]).strip() and str(row["Owner"]).strip()
            else row[TAGGED_COL],
            axis=1
        )

        ok, msg = safe_save_df_to_csv(df_remediated, REMIDIATED_SAVE_PATH)

        if ok:
            st.success(f"Remediation saved → {REMIDIATED_SAVE_PATH}")
            st.dataframe(df_remediated.head())
        else:
            st.error("Failed to save: " + msg)
