from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd


url = "https://ca.soccerway.com/national/france/ligue-1/20242025/regular-season/r81802/matches/"

def start_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_experimental_option("detach", True)
    
    # If chromedriver is in PATH, you don’t need to specify it
    driver = webdriver.Chrome(options=chrome_options)

    return driver

driver = start_driver(url)

match_hrefs = set()
europe_ligues = ['france/ligue-1', 'germany/bundesliga']


def get_match_hrefs(years):
    all_hrefs = set()
    for year in years:
        for ligue in europe_ligues:
            match_links = driver.find_elements(By.CSS_SELECTOR, f"a[href*='{ligue}'][href*='/matches/{year}/']")
            hrefs = {a.get_attribute('href') for a in match_links}
            all_hrefs.update(hrefs)
    return all_hrefs


def get_teams(driver):
    try:
        team_a = driver.find_element(By.XPATH, "//div[@class='team team-a']//a").text.strip()
        team_b = driver.find_element(By.XPATH, "//div[@class='team team-b']//a").text.strip()
        return f"{team_a} vs {team_b}"
    except:
        return "Unknown vs Unknown"

# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_experimental_option("detach", True)

def get_goal_minutes(goal_events_div_xpath):  # arg: goal_events_div_xpath
    try:
        team_div = driver.find_element(By.XPATH, goal_events_div_xpath)
        spans = team_div.find_elements(By.XPATH, ".//span")
        minutes = []
        for span in spans:
            text = span.text.strip()
            if "'" in text:
                try:
                    minute = int(text.replace("'", "").split('+')[0])
                    minutes.append(minute)
                except ValueError:
                    continue
        return minutes
    except NoSuchElementException:
        return []
    
    
def scrape_data():
    for _ in range(38): # 38 weeks(match days) in Ligue 1
        try:
            # Load previous button
            btn = driver.find_element(By.XPATH, f"/html/body/div[3]/div/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div/div[2]/div[1]/div/div/div/button")
            btn.click()
            time.sleep(2)
        except:
            break

    # single match div
    match = driver.find_element(By.XPATH, f"/html/body/div[3]/div/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div/div[2]/div[2]/div/div/div[3]/div/div/div/a")
    
    while True:
        try:
            consent_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[8]/div[2]/div[2]/div[2]/button"))
                )
            consent_button.click()    # trigger consent button to remove modal
            print("✅ Consent button clicked.")
        except:
            pass    # consent may have been handled
            
        try:
            previous_count = len(match_hrefs)
            # remove the pop-up modal, cookie modal, consent button
            WebDriverWait(driver, 15).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "fc-dialog-overlay"))
            )
            load_prev_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div/div[2]/div[1]/div/div/div/button"))
            )
            load_prev_btn.click()   # trigger load previous button
            # driver.execute_script("arguments[0].click();", load_prev_btn)
            
            # Wait for new content to load
            time.sleep(4)  # Or better: wait for a new match element to appear
            # Get new hrefs
            new_hrefs = get_match_hrefs([2023, 2024, 2025])
            print(f"Loaded {len(new_hrefs - match_hrefs)} matches")
            match_hrefs.update(new_hrefs)
        except Exception as e:
            print("No more 'Load Previous' button or loading stopped:", e)
            break
    
    # print(f"Total matches found for 2025 in france/ligue-1: {len(match_hrefs)}")
    # for href in sorted(match_hrefs):
    #     print(href)

zero_zero_count = 0
late_goals_count = 0
valid_scores = {'0 - 1', '1 - 0', '1 - 1', '0 - 2', '2 - 0', '1 - 2', '2 - 1'}
late_goal_teams = []

for href in match_hrefs:
    driver.get(href)
    time.sleep(2)
    
    try:
        # Handle consent popup
        consent_button = driver.find_element(By.XPATH, "/html/body/div[8]/div[2]/div[2]/div[2]/button")
        consent_button.click()
        time.sleep(1)
    except:
        pass  # Consent may have already been handled

    try:
        home_score_elem = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div")
        away_score_elem = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[3]/div/div/div/div[3]/div")
        home_team_elem = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[3]/div/a[1]/div")
        away_team_elem = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[3]/div/a[2]/div")

        home_score = int(home_score_elem.text.strip())
        away_score = int(away_score_elem.text.strip())
        score = f"{home_score} - {away_score}"
        total_goals = home_score + away_score

        if score == "0 - 0":
            zero_zero_count += 1
            continue

        if score in valid_scores and 1 <= total_goals <= 3:
            home_goals_minutes = get_goal_minutes("/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[5]/div[1]")
            away_goals_minutes = get_goal_minutes("/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[5]/div[2]")

            all_goals = sorted(home_goals_minutes + away_goals_minutes)

            if all_goals and all(minute >= 70 for minute in all_goals):
                late_goals_count += 1
                late_goal_teams.append(f"{home_team_elem.text.strip()} vs {away_team_elem.text.strip()}")

    except Exception as e:
        print(f"Error processing {href}: {e}")
        continue

    print(f"\n✅ Total 0-0 games: {zero_zero_count}")
    print(f"✅ Total 1-3 goal games with first goal after 70th minute: {late_goals_count}")
    print("✅ Matches where all goals were after 70th minute:")
    for match in late_goal_teams:
        print(f" - {match}")


    for match in matches:
        try:
            score = match.find_element(By.CLASS_NAME, 'score-time').text.strip()
            teams = match.find_elements(By.CLASS_NAME, 'team-name')
            if len(teams) != 2:
                continue
            home = teams[0].text.strip()
            away = teams[1].text.strip()

            date = match.find_element(By.CLASS_NAME, 'score-time').get_attribute("data-dt").split(" ")[0]

            if score in ['0 - 0', '0-0']:
                zero_zero_count += 1
                continue

            allowed_scores = ['0 - 1', '1 - 0', '1 - 1', '0 - 2', '2 - 0', '1 - 2', '2 - 1']
            if score not in allowed_scores:
                continue

            link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(3)

            goal_events = driver.find_elements(By.CSS_SELECTOR, '.event .minute')
            minutes = []
            for event in goal_events:
                m = event.text.replace("'", "").replace("+", "")
                try:
                    minutes.append(int(m))
                except:
                    continue

            if minutes and min(minutes) >= 70:
                late_goal_matches.append({
                    "Date": date,
                    "Home Team": home,
                    "Away Team": away,
                    "Score": score,
                    "First Goal Minute": min(minutes),
                    "Match Link": link
                })

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            continue

    driver.quit()

    df_zero = pd.DataFrame([{"0-0 Count": zero_zero_count}])
    df_late = pd.DataFrame(late_goal_matches)

    df_zero.to_csv("data/zero_zero_matches.csv", index=False)
    df_late.to_csv("data/late_goal_matches.csv", index=False)

    return df_zero, df_late
