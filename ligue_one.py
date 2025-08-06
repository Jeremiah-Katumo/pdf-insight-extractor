import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scraper import scrape_data
import os

st.set_page_config(page_title="Ligue 1 Match Analyzer", layout="wide")
st.title("⚽ Ligue 1 Match Analyzer (2024/25)")

# Scrape Button
st.sidebar.header("🔄 Live Scraper")
# chromedriver_path = st.sidebar.text_input("Enter path to chromedriver", value="/usr/bin/chromedriver")
if st.sidebar.button("Scrape Live Data"):
    with st.spinner("Scraping Soccerway... please wait (~1-2 mins)"):
        df_zero, df_late = scrape_data()
        st.success("✅ Live data updated!")

# Load data
try:
    df_zero = pd.read_csv("data/zero_zero_matches.csv")
    df_late = pd.read_csv("data/late_goal_matches.csv")
    df_late['Date'] = pd.to_datetime(df_late['Date'], errors='coerce')
except Exception as e:
    st.error("Error loading CSV files. Please scrape first.")
    st.stop()

# Section 1 – 0-0 Matches
st.subheader("🥱 0-0 Matches")
st.metric(label="Total 0-0 Matches", value=int(df_zero.iloc[0, 0]))

# Section 2 – Late Goals
st.subheader("⏱ Matches with 1–3 Goals & First Goal ≥ 70'")
team_filter = st.text_input("Filter by Team Name").lower().strip()
min_goal_time = st.slider("Minimum First Goal Time", 70, 90, 70)

filtered = df_late[
    (df_late["First Goal Minute"] >= min_goal_time) &
    (
        df_late["Home Team"].str.lower().str.contains(team_filter) |
        df_late["Away Team"].str.lower().str.contains(team_filter)
    )
]

st.dataframe(filtered.sort_values(by="Date", ascending=False), use_container_width=True)

# Charts
st.subheader("📊 Goal Minute Distribution")
fig, ax = plt.subplots()
df_late["Minute Bucket"] = pd.cut(df_late["First Goal Minute"], bins=[70,75,80,85,90], labels=["70-74","75-79","80-84","85-90"])
df_late["Minute Bucket"].value_counts().sort_index().plot(kind='bar', ax=ax, color="skyblue")
ax.set_ylabel("Match Count")
ax.set_xlabel("First Goal Time Bucket")
st.pyplot(fig)

st.subheader("📈 Late Goal Matches Over Time")
line_fig, ax2 = plt.subplots()
df_late["Date"].value_counts().sort_index().plot(ax=ax2, marker='o', color="orange")
ax2.set_ylabel("Number of Matches")
ax2.set_xlabel("Date")
st.pyplot(line_fig)

# Downloads
st.download_button("📥 Download 0-0 Count", df_zero.to_csv(index=False), "zero_zero_matches.csv", "text/csv")
st.download_button("📥 Download Late Goals Data", df_late.to_csv(index=False), "late_goal_matches.csv", "text/csv")

# Footer
st.markdown("---")
st.markdown("📊 Built with ❤️ by [Your Name]")
