import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scraper import scrape_data, extract_match_data, driver, start_driver, load_all_matches_hrefs, get_match_hrefs
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
            # match_hrefs = load_all_matches_hrefs(driver, get_match_hrefs)  # Pass driver in
            # print(f"Found {len(match_hrefs)} matches to scrape.")
            # if not match_hrefs:
            #     st.error("No match data found. Please check the scraper.")
            # else:
            if not os.path.exists("data"):
                os.makedirs("data", exist_ok=True)
            
            # Extract all match info, including 'Previous' clicks
            df_zero, df_early, df_late, df_complete = extract_match_data(driver)
            df_complete["first_goal_minute"] = pd.to_numeric(df_complete["first_goal_minute"], errors='coerce').fillna(0).astype(int)
            df_complete["last_goal_minute"] = pd.to_numeric(df_complete["last_goal_minute"], errors='coerce').fillna(0).astype(int)
            
            st.success("✅ Live data updated!")
        except Exception as e:
            st.error(f"Error extracting match data: {e}")
        # finally:
        #     driver.quit()

# Load data
try:
    df_zero = df_zero
    df_early = df_early
    df_late = df_late
    df_complete = df_complete
    # df_late['Date'] = pd.to_datetime(df_late['Date'], errors='coerce')
    # df_complete['Date'] = pd.to_datetime(df_complete['Date'], errors='coerce')
except Exception as e:
    st.error("Error loading CSV files.")
    st.stop()

# Section 1 – 0-0 Matches
st.subheader("🥱 0-0 Matches")
if df_zero.empty:
    st.warning("No 0-0 matches found.")
else:
    st.metric(label="Total Matches", value=len(df_zero))
    st.metric(label="Total 0-0 Matches", value=int(df_zero["0_0_count"].iloc[0]))
    st.dataframe(df_zero.sort_values(by="Date", ascending=False), use_container_width=True)
    st.markdown("### Match Details")
    st.markdown("This section shows all matches that ended in a 0-0 draw.")
# st.metric(label="Total 0-0 Matches", value=int(df_zero["zero_zero_count"].iloc[0]))

# Section 2 – Early Goals
st.subheader("⚡ Matches with 1–3 Goals & First Goal < 70'")
team_filter_early = st.text_input("Filter by Team Name (Early Goals)").lower().strip()
min_goal_time_early = st.slider("Minimum First Goal Time", 0, 70, 0)

# Section 3 – Late Goals
st.subheader("⏱ Matches with 1–3 Goals & First Goal ≥ 70'")
team_filter_late = st.text_input("Filter by Team Name").lower().strip()
min_goal_time_late = st.slider("Maximum First Goal Time", 70, 90, 70)

st.dataframe(df_complete, use_container_width=True)

filtered_early = df_early[
    (df_complete["first_goal_minute"] <= min_goal_time_early) &
    (   
        df_complete["home_team"].str.lower().str.contains(team_filter_early) |
        df_complete["away_team"].str.lower().str.contains(team_filter_early)
    )
]

filtered_late = df_late[
    (df_complete["first_goal_minute"] >= min_goal_time_late) &
    (
        df_complete["home_team"].str.lower().str.contains(team_filter_late) |
        df_complete["away_team"].str.lower().str.contains(team_filter_late)
    )
]

st.dataframe(filtered_early, use_container_width=True)
st.dataframe(filtered_late, use_container_width=True)

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
