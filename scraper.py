from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchElementException
)
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

driver = start_driver()

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

def extract_minute(text):
    if not text:
        return None
    for t in text.split():
        if "'" in t:
            try:
                return int(t.replace("'", "").strip())
            except:
                return None
    return None

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
    
    
def parse_minute(minute_str):
    # Handle "90+3'" -> 93, "45'" -> 45
    minute_str = minute_str.replace("'", "").strip()
    if "+" in minute_str:
        base, extra = minute_str.split("+")
        return int(base) + int(extra)
    return int(minute_str)
    
    
def safe_click(xpath):
    """Wait and click element, fallback to JS click if normal click fails."""
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        try:
            btn.click()
        except:
            driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)  # allow content to load
        return True
    except Exception:
        return False


def scrape_data(driver):
    # Handle consent popup once
    try:
        consent_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Consent')]"))
        )
        consent_button.click()
        print("✅ Consent button clicked.")
    except:
        print("❌ No consent button found.")

    match_hrefs = set()
    prev_btn_xpath = "//button[contains(., 'Show previous')]"

    while True:
        try:
            previous_count = len(match_hrefs)

            # Wait until no overlay
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "fc-dialog-overlay"))
            )

            # Click Load Previous
            if not safe_click(prev_btn_xpath):
                print("⚠️ No 'Show previous' button found. Stopping.")
                break
            print("🔄 Clicked 'Show previous'")

            # Wait until new matches appear
            WebDriverWait(driver, 10).until(
                lambda d: len(get_match_hrefs([2023, 2024, 2025])) > previous_count
            )

            # Update match list
            new_hrefs = get_match_hrefs([2023, 2024, 2025])
            before_count = len(match_hrefs)
            match_hrefs.update(new_hrefs)
            print(f"📊 Collected so far: {len(match_hrefs)} matches")

            if len(match_hrefs) == before_count:
                print("⚠️ No new matches after click. Stopping.")
                break

        except Exception as e:
            print("❌ Error or no more button:", e)
            break

    return match_hrefs


# def scrape_data(driver):
#     match_hrefs = set()

#     def safe_click(xpath):
#         """Wait and safely click an element via JavaScript if needed."""
#         try:
#             btn = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, xpath))
#             )
#             driver.execute_script("arguments[0].click();", btn)  # JS click bypasses overlays
#             time.sleep(2)
#             return True
#         except Exception:
#             return False

#     # Handle consent pop-up once
#     try:
#         consent_button = WebDriverWait(driver, 5).until(
#             EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Consent')]"))
#         )
#         consent_button.click()
#         print("✅ Consent button clicked.")
#     except:
#         pass

#     prev_btn_xpath = "//button[contains(text(), 'Show previous')]"

#     while True:
#         # Extract match hrefs before clicking
#         new_hrefs = get_match_hrefs([2023, 2024, 2025])
#         before_count = len(match_hrefs)
#         match_hrefs.update(new_hrefs)
#         print(f"Collected so far: {len(match_hrefs)} matches")

#         # Try to click Load Previous
#         if not safe_click(prev_btn_xpath):
#             print("No more 'Load Previous' button. Stopping.")
#             break

#         # If no new matches were added after click, stop loop
#         if len(match_hrefs) == before_count:
#             print("No new matches loaded. Stopping.")
#             break

#     return match_hrefs


def load_all_matches(driver, get_match_hrefs, years=[2023, 2024, 2025], match_hrefs=match_hrefs):
    """
    Clicks 'Load Previous' until no more matches are found.
    
    Args:
        driver: Selenium WebDriver instance
        get_match_hrefs: Function returning a set of hrefs for given years
        years: List of years (default [2023, 2024, 2025])
        match_hrefs: Existing set of match hrefs; if None, will be initialized
    """
    # if match_hrefs is None:
    #     match_hrefs = set(get_match_hrefs(years))  # start with what’s already loaded

    while True:
        # Handle consent popup (if it appears)
        try:
            consent_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Consent')]"))
            )
            consent_button.click()
            print("✅ Consent button clicked.")
        except:
            pass

        try:
            previous_count = len(match_hrefs)

            # Wait for overlays to disappear
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "fc-dialog-overlay"))
            )

            # Find and click 'Load Previous'
            load_prev_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='block_match_list']//button"))
            )
            try:
                load_prev_btn.click()
            except:
                driver.execute_script("arguments[0].click();", load_prev_btn)
            print("🔄 Clicked 'Load Previous'")

            # Wait for more matches
            WebDriverWait(driver, 10).until(
                lambda d: len(get_match_hrefs(years)) > previous_count
            )

            # Update matches
            new_hrefs = get_match_hrefs(years)
            added = len(new_hrefs - match_hrefs)
            match_hrefs.update(new_hrefs)
            print(f"📈 Loaded {added} new matches. Total: {len(match_hrefs)}")

            if added == 0:
                print("⚠️ No new matches after click. Stopping.")
                break

        except Exception as e:
            print("❌ No more 'Load Previous' button or stopped due to error:", e)
            break

    print(f"✅ Total matches found: {len(match_hrefs)}")
    for href in sorted(match_hrefs):
        print(href)

    return match_hrefs



def load_all_previous_data(driver, timeout=10):
    """Click the 'Load Previous' button until it disappears or becomes inactive."""
    while True:
        try:
            # Adjust based on real button class or text
            load_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load Previous')]"))
            )
            driver.execute_script("arguments[0].click();", load_button)
            print("Clicked Load Previous")
            time.sleep(2)  # Let content load
        except (TimeoutException, NoSuchElementException):
            print("No more Load Previous button found.")
            break
        except ElementClickInterceptedException as e:
            print(f"Click intercepted: {e}")
            # Optionally scroll into view or dismiss overlays
            driver.execute_script("arguments[0].scrollIntoView();", load_button)
            time.sleep(1)
            
    
def extract_match_data(driver, match_hrefs):
    zero_zero_count = 0
    early_goals_count = 0
    late_goals_count = 0
    valid_scores = {'0 - 1', '1 - 0', '1 - 1', '0 - 2', '2 - 0', '1 - 2', '2 - 1'}
    early_goal_teams = []
    early_goal_matches = []
    late_goal_teams = []
    late_goal_matches = []
    goal_count = 0

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
                print(zero_zero_count)
                continue
            
            if score in valid_scores and 1 <= total_goals <= 3:
                load_all_previous_data(driver)
                # home_goals_minutes = get_goal_minutes("/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[5]/div[1]")
                # away_goals_minutes = get_goal_minutes("/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[5]/div[2]")
                xpaths = [
                    "/html/body/div[3]/div/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div[2]/div/div[2]/div[1]/div[2]/div[2]/span/span",
                    "/html/body/div[3]/div/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[2]/span/span",
                    "/html/body/div[3]/div/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div[2]/div/div[2]/div[1]/div[4]/div[2]/span/span",
                    "/html/body/div[3]/div/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div[2]/div/div[2]/div[1]/div[5]/div[2]/span/span",
                    "/html/body/div[3]/div/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div[2]/div/div[2]/div[1]/div[6]/div[2]/span/span"
                ]

                # === Extract and print scored minutes ===
                minutes_list = []
                for xpath in xpaths:
                    try:
                        scored_minute = driver.find_element(By.XPATH, xpath)
                        scored_minute_text = scored_minute.text.strip()
                        # print([scored_minute_text])
                        if not scored_minute_text:
                            break  # Stop if no more scored minutes
                        minutes_list.append(scored_minute_text)
                        print(minutes_list)
                    except Exception as e:
                        print(f"Could not find element at {xpath} - {e}")
                        
                parsed_minutes = [parse_minute(minute) for minute in minutes_list]  # e.g., [20, 43, 53]
                # print(parsed_minutes)  # e.g., [20, 43, 53]
                
                for minute in parsed_minutes:
                    if minute <= 70:
                        goal_count += 1
                    
                        # Check if goal_count is valid and all goals are after 70th minute
                    if goal_count and 1 <= minute <= 90:
                        early_goals_count += 1
                        early_goal_teams.append(f"{home_team_elem.text.strip()} {int(home_score_elem.text.strip())} vs {int(away_score_elem.text.strip())} {away_team_elem.text.strip()}")

                # all_goals = sorted(home_goals_minutes + away_goals_minutes)

                # if all_goals and all(minute >= 70 for minute in all_goals):
                #     late_goals_count += 1
                #     late_goal_teams.append(f"{home_team_elem.text.strip()} vs {away_team_elem.text.strip()}")
                early_goal_matches.append({
                    "zero_zero_count": zero_zero_count,
                    "early_goals_count": early_goals_count,
                    "early_goal_teams": early_goal_teams,
                    "goal_count": goal_count
                })
                
                df_zero = pd.DataFrame([{"0-0 Count": zero_zero_count}])
                df_early = pd.DataFrame(early_goal_matches)

                df_zero.to_csv("data/zero_zero_matches.csv", index=False)
                df_early.to_csv("data/early_goal_matches.csv", index=False)
                
            if score not in valid_scores and total_goals > 3:
                load_all_previous_data(driver)
                
                all_goals = home_score + away_score
                late_goals_count += 1
                late_goal_teams.append(f"{home_team_elem.text.strip()} {int(home_score_elem.text.strip())} vs {int(away_score_elem.text.strip())} {away_team_elem.text.strip()}")
                
                late_goal_matches.append({
                    "late_goals_count": late_goals_count,
                    "late_goal_teams": late_goal_teams,
                    "home_score": home_score,
                    "away_score": away_score,
                    "all_goals": all_goals,
                })
                
                df_late = pd.DataFrame(late_goal_matches)
                df_late.to_csv("data/late_goal_matches.csv", index=False)
                
            complete_data = {
                "home_team_elem": home_team_elem.text.strip(),
                "away_team_elem": away_team_elem.text.strip(),
                "home_score": home_score,
                "away_score": away_score,
                "score": score,
                "zero_zero_count": zero_zero_count,
                "early_goals_count": early_goals_count,
                "late_goals_count": late_goals_count,
                "goal_count": goal_count,
                "early_goal_teams": early_goal_teams,
                "late_goal_teams": late_goal_teams
            }
            df_complete = pd.DataFrame([complete_data])
            df_complete.to_csv("data/complete_match_data.csv", index=False)

        except Exception as e:
            print(f"Error processing {href}: {e}")
            continue
        
    return df_zero, df_early, df_late, df_complete

    # zero_zero_count = 0
    # late_goals_count = 0
    # valid_scores = {'0 - 1', '1 - 0', '1 - 1', '0 - 2', '2 - 0', '1 - 2', '2 - 1'}
    # late_goal_teams = []

    # for href in match_hrefs:
    #     driver.get(href)
    #     time.sleep(2)
        
    #     try:
    #         # Handle consent popup
    #         consent_button = driver.find_element(By.XPATH, "/html/body/div[8]/div[2]/div[2]/div[2]/button")
    #         consent_button.click()
    #         time.sleep(1)
    #     except:
    #         pass  # Consent may have already been handled

    #     try:
    #         home_score_elem = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div")
    #         away_score_elem = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[3]/div/div/div/div[3]/div")
    #         home_team_elem = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[3]/div/a[1]/div")
    #         away_team_elem = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[3]/div/a[2]/div")

    #         home_score = int(home_score_elem.text.strip())
    #         away_score = int(away_score_elem.text.strip())
    #         score = f"{home_score} - {away_score}"
    #         total_goals = home_score + away_score

    #         if score == "0 - 0":
    #             zero_zero_count += 1
    #             continue

    #         if score in valid_scores and 1 <= total_goals <= 3:
    #             home_goals_minutes = get_goal_minutes("/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[5]/div[1]")
    #             away_goals_minutes = get_goal_minutes("/html/body/div[3]/div/div/div[1]/div/div[1]/div/div[5]/div[2]")

    #             all_goals = sorted(home_goals_minutes + away_goals_minutes)

    #             if all_goals and all(minute >= 70 for minute in all_goals):
    #                 late_goals_count += 1
    #                 late_goal_teams.append(f"{home_team_elem.text.strip()} vs {away_team_elem.text.strip()}")

    #     except Exception as e:
    #         print(f"Error processing {href}: {e}")
    #         continue

    #     print(f"\n✅ Total 0-0 games: {zero_zero_count}")
    #     print(f"✅ Total 1-3 goal games with first goal after 70th minute: {late_goals_count}")
    #     print("✅ Matches where all goals were after 70th minute:")
    #     for match in late_goal_teams:
    #         print(f" - {match}")


    #     for match in matches:
    #         try:
    #             score = match.find_element(By.CLASS_NAME, 'score-time').text.strip()
    #             teams = match.find_elements(By.CLASS_NAME, 'team-name')
    #             if len(teams) != 2:
    #                 continue
    #             home = teams[0].text.strip()
    #             away = teams[1].text.strip()

    #             date = match.find_element(By.CLASS_NAME, 'score-time').get_attribute("data-dt").split(" ")[0]

    #             if score in ['0 - 0', '0-0']:
    #                 zero_zero_count += 1
    #                 continue

    #             allowed_scores = ['0 - 1', '1 - 0', '1 - 1', '0 - 2', '2 - 0', '1 - 2', '2 - 1']
    #             if score not in allowed_scores:
    #                 continue

    #             link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
    #             driver.execute_script("window.open(arguments[0]);", link)
    #             driver.switch_to.window(driver.window_handles[1])
    #             time.sleep(3)

    #             goal_events = driver.find_elements(By.CSS_SELECTOR, '.event .minute')
    #             minutes = []
    #             for event in goal_events:
    #                 m = event.text.replace("'", "").replace("+", "")
    #                 try:
    #                     minutes.append(int(m))
    #                 except:
    #                     continue

    #             if minutes and min(minutes) >= 70:
    #                 late_goal_matches.append({
    #                     "Date": date,
    #                     "Home Team": home,
    #                     "Away Team": away,
    #                     "Score": score,
    #                     "First Goal Minute": min(minutes),
    #                     "Match Link": link
    #                 })

    #             driver.close()
    #             driver.switch_to.window(driver.window_handles[0])

    #         except Exception as e:
    #             continue

    #     driver.quit()

    #     df_zero = pd.DataFrame([{"0-0 Count": zero_zero_count}])
    #     df_late = pd.DataFrame(late_goal_matches)

    #     df_zero.to_csv("data/zero_zero_matches.csv", index=False)
    #     df_late.to_csv("data/late_goal_matches.csv", index=False)

    #     return df_zero, df_late
