import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scraper import scrape_data, extract_match_data, driver, start_driver
import os

st.set_page_config(page_title="Ligue 1 Match Analyzer", layout="wide")
st.title("⚽ Ligue 1 Match Analyzer (2024/25)")

# Scrape Button
st.sidebar.header("🔄 Live Scraper")
if st.sidebar.button("Scrape Live Data"):
    with st.spinner("Scraping Soccerway... please wait (~1-2 mins)"):        
        driver = start_driver()  # Initialize the driver
        if not driver:
            st.error("Failed to start the web driver. Please check your setup.")
            st.stop()
        st.success("Web driver started successfully!")
        st.info("Scraping data... This may take a moment.")
        
        # Ensure the driver is passed to the scrape_data function
        try:
            match_hrefs = scrape_data(driver)  # Pass driver in
            if not match_hrefs:
                st.error("No match data found. Please check the scraper.")
            else:
                if not os.path.exists("data"):
                    os.makedirs("data", exist_ok=True)
                
                # Extract all match info, including 'Previous' clicks
                df_zero, df_early, df_late, df_complete = extract_match_data(driver, match_hrefs)

                # Save CSVs
                df_zero.to_csv("~/Work/Development/Projects/football/data/zero_zero_matches.csv", index=False)
                df_early.to_csv("~/Work/Development/Projects/football/data/early_goal_matches.csv", index=False)
                df_late.to_csv("~/Work/Development/Projects/football/data/late_goal_matches.csv", index=False)
                df_complete.to_csv("~/Work/Development/Projects/football/data/complete_matches.csv", index=False)

                st.success("✅ Live data updated!")
        except Exception as e:
            st.error(f"Error extracting match data: {e}")
        finally:
            driver.quit()

# Load data
try:
    df_zero = pd.read_csv("./data/zero_zero_matches.csv", sep=",")
    df_early = pd.read_csv("./data/early_goal_matches.csv", sep=",")
    df_late = pd.read_csv("./data/late_goal_matches.csv", sep=",")
    df_complete = pd.read_csv("./data/complete_matches.csv", sep=",")
    # df_late['Date'] = pd.to_datetime(df_late['Date'], errors='coerce')
    # df_complete['Date'] = pd.to_datetime(df_complete['Date'], errors='coerce')
except Exception as e:
    st.error("Error loading CSV files. Please extract first.")
    st.stop()

# Section 1 – 0-0 Matches
st.subheader("🥱 0-0 Matches")
st.metric(label="Total 0-0 Matches", value=int(df_zero.iloc[0, 0]))

# Section 2 – Early Goals
st.subheader("⚡ Matches with 1–3 Goals & First Goal < 70'")
team_filter_early = st.text_input("Filter by Team Name (Early Goals)").lower().strip()
min_goal_time_early = st.slider("Minimum First Goal Time", 0, 70, 0)

# Section 3 – Late Goals
st.subheader("⏱ Matches with 1–3 Goals & First Goal ≥ 70'")
team_filter_late = st.text_input("Filter by Team Name").lower().strip()
min_goal_time_late = st.slider("Minimum First Goal Time", 70, 90, 70)

filtered_early = df_early[
    (df_early["First Goal Minute"] <= min_goal_time_early) &
    (   df_early["Home Team"].str.lower().str.contains(team_filter_early) |
        df_early["Away Team"].str.lower().str.contains(team_filter_early)
    )
]

filtered_late = df_late[
    (df_late["First Goal Minute"] >= min_goal_time_late) &
    (
        df_late["Home Team"].str.lower().str.contains(team_filter_late) |
        df_late["Away Team"].str.lower().str.contains(team_filter_late)
    )
]

st.dataframe(filtered_early.sort_values(by="Date", ascending=False), use_container_width=True)
st.dataframe(filtered_late.sort_values(by="Date", ascending=False), use_container_width=True)

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
