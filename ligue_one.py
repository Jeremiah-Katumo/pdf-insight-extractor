from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import pandas as pd

# Setup
url = "https://ca.soccerway.com/national/france/ligue-1/20242025/regular-season/r81802/matches/"
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=chrome_options)
driver.get(url)

# Click “Load previous” until all weeks load
for _ in range(40):  # up to 38 weeks
    try:
        load_button = driver.find_element(By.CLASS_NAME, 'btn-more')
        load_button.click()
        time.sleep(2)
    except:
        break

# Extract match links and final scores
matches = driver.find_elements(By.CSS_SELECTOR, 'tr.match')

zero_zero_count = 0
late_goal_matches = []

for match in matches:
    try:
        score = match.find_element(By.CLASS_NAME, 'score-time').text.strip()
        teams = match.find_elements(By.CLASS_NAME, 'team-name')
        if len(teams) != 2:
            continue
        home = teams[0].text.strip()
        away = teams[1].text.strip()

        if score in ['0 - 0', '0-0']:
            zero_zero_count += 1
            continue

        # Parse only low-goal games
        allowed_scores = ['0 - 1', '1 - 0', '1 - 1', '0 - 2', '2 - 0', '1 - 2', '2 - 1']
        if score not in allowed_scores:
            continue

        # Click match to view goal times
        link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
        driver.execute_script("window.open(arguments[0]);", link)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(3)

        # Find goal times
        goal_events = driver.find_elements(By.CSS_SELECTOR, '.event .minute')
        if not goal_events:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        minutes = []
        for event in goal_events:
            minute_text = event.text.replace("'", "").replace("+", "")
            try:
                minutes.append(int(minute_text))
            except:
                continue

        if minutes and min(minutes) >= 70:
            late_goal_matches.append({
                "Home": home,
                "Away": away,
                "Score": score,
                "First Goal Minute": min(minutes),
                "Link": link
            })

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        continue

driver.quit()

# Create DataFrames
df_zero = pd.DataFrame([{"0-0 Count": zero_zero_count}])
df_late = pd.DataFrame(late_goal_matches)

# Save to Excel/Google Sheets
df_zero.to_csv("zero_zero_matches.csv", index=False)
df_late.to_csv("late_goal_matches.csv", index=False)
