import os
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import csv
import sys
import pickle
from datetime import datetime, timedelta
from nicheIdentifier import isNiche



COOKIES_FILE = 'insta_cookies.pkl'

def save_cookies(driver, filename):
    with open(filename, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    print("[INFO] Cookies saved.")

def load_cookies(driver, filename):
    try:
        with open(filename, 'rb') as f:
            cookies = pickle.load(f)
            if not cookies:
                print("[ERROR] Cookies file is empty.")
                return False
            for cookie in cookies:
                if 'expiry' in cookie:
                    del cookie['expiry']  # remove expiry to avoid error
                driver.add_cookie(cookie)
        print("[INFO] Cookies loaded.")
        return True
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        print(f"[ERROR] Failed to load cookies: {e}")
        return False



# --- Monkey patch to suppress __del__ crash ---
uc.Chrome.__del__ = lambda self: None

# --- Load environment variables ---
load_dotenv()
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
TARGET_USERNAME = os.getenv('TARGET_USERNAME', 'gymshark')
MAX_USERS = int(os.getenv('MAX_USERS', 50))
CSV_FILENAME = os.getenv('CSV_FILENAME', 'influencers.csv')
NICHE = os.getenv('NICHE')
MAX_FOLLOWERS = int(os.getenv('MAX_FOLLOWERS', 1000000000))
MIN_FOLLOWERS = int(os.getenv('MIN_FOLLOWERS', 1000))

# --- Setup ---
options = uc.ChromeOptions()
options.headless = False
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = uc.Chrome(options=options, use_subprocess=True, version_main=135)

def random_sleep(min_s=2, max_s=5):
    time.sleep(random.uniform(min_s, max_s))

def login():
    driver.get('https://www.instagram.com/')
    random_sleep(3, 5)

    # Try loading cookies if they exist
    if os.path.exists(COOKIES_FILE):
        try:
            load_cookies(driver, COOKIES_FILE)
            driver.refresh()
            random_sleep(3, 5)

            # Check if already logged in
            if driver.current_url.startswith('https://www.instagram.com/accounts/login'):
                print("[INFO] Cookies expired or invalid. Logging in manually...")
            else:
                print("[SUCCESS] Logged in via cookies.")
                return
        except Exception as e:
            print(f"[ERROR] Failed to load cookies: {e}. Logging in manually...")

    # Proceed with manual login
    driver.get('https://www.instagram.com/accounts/login/')
    random_sleep(4, 7)

    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")

    username_input.send_keys(INSTAGRAM_USERNAME)
    password_input.send_keys(INSTAGRAM_PASSWORD)
    password_input.send_keys(Keys.RETURN)

    random_sleep(5, 8)

    save_cookies(driver, COOKIES_FILE)
    print("[SUCCESS] Logged in and cookies saved.")

def parse_followers(text):
    print(f"[DEBUG] Parsing follower text: {text}")
    text = text.lower().replace(',', '').replace('.', '').replace('followers','').strip()
    if 'm' in text:
        return int(float(text.replace('m', '')) * 1_000_000)
    elif 'k' in text:
        return int(float(text.replace('k', '')) * 1_000)
    else:
        try:
            print(int(text))
            return int(text)
        except ValueError:
            print(f"[ERROR] Failed to parse follower count: {text}")
            return 0

def get_follower_count(user_element):
    try:
        print("[DEBUG] Getting follower count for user...")
        # Directly find the follower count element
        followers_element = user_element.find_element(By.XPATH, "//section/main/div/header/section/ul/li[2]/div/a/span")
        followers = followers_element.get_attribute('title') or followers_element.text
        followers = parse_followers(followers)
        return followers
    except Exception as e:
        print(f"[ERROR] Failed to get follower count for user: {e}")
        return None

def scroll_followers_modal():
    print("[DEBUG] Scrolling the followers modal...")

    try:
        # Wait for scrollable followers container
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//div[div[contains(@style, 'overflow: hidden auto')]]"))
        )
        scroll_box = driver.find_element(By.XPATH, "//div[div[contains(@style, 'overflow: hidden auto')]]")
    except Exception as e:
        print(f"[ERROR] Failed to find the scrollable box: {e}")
        return []

    last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_box)
    found_users = len(scroll_box.find_elements(By.TAG_NAME, "a"))

    while found_users < MAX_USERS:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
        time.sleep(2)

        try:
            WebDriverWait(driver, 5).until(
                lambda d: len(scroll_box.find_elements(By.TAG_NAME, "a")) > found_users
            )
        except:
            print("[INFO] No new users loaded after scroll, breaking...")
            break

        new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_box)
        print(f"[DEBUG] Scroll position: {new_height}, User count: {found_users}")

        if new_height == last_height:
            print("[INFO] Reached the bottom of the follower list.")
            break

        last_height = new_height
        found_users = len(scroll_box.find_elements(By.TAG_NAME, "a"))

    links = scroll_box.find_elements(By.TAG_NAME, "a")
    usernames = [link.text.strip() for link in links if link.text.strip()]
    print(f"[INFO] Collected {len(usernames)} usernames.")

    return usernames[:MAX_USERS]


def get_follower_usernames():
    print(f"[ACTION] Scraping followers of @{TARGET_USERNAME}...")
    driver.get(f"https://www.instagram.com/{TARGET_USERNAME}/")
    random_sleep(4, 6)

    try:
        time.sleep(3)
        stats_links = driver.find_elements(By.XPATH, "//ul//li//a")
        print(f"[DEBUG] Found {len(stats_links)} profile stats links.")
        for link in stats_links:
            if 'followers' in link.text.lower():
                followers_button = link
                break
        else:
            print("[ERROR] Followers button not found.")
            return []
        followers_button.click()
    except NoSuchElementException:
        print("[ERROR] Could not locate followers button.")
        return []

    random_sleep(2, 4)

    # Use the scrolling + scraping function
    usernames = scroll_followers_modal()
    return usernames

def scrape_user_info(username):
    print(f"[SCRAPING] Visiting @{username}...")
    driver.get(f"https://www.instagram.com/{username}/")
    random_sleep(3, 5)


    try:
        # Check if the account is private
        try:
            private_message = driver.find_element(By.XPATH, "//h2[contains(text(), 'This Account is Private')]")
            if private_message:
                print(f"[SKIP] @{username} is a private account. Skipping...")
                return None
        except NoSuchElementException:
                try:
                    _ = driver.find_element(By.XPATH, "//section/main/div/header/section/ul/li[2]/div/a/span")
                    if _:
                        print(f"[INFO] @{username} is a public account.")
                except NoSuchElementException:
                    print(f"[SKIP]  @{username} is private.")
                    return None


        # Scrape bio
        try:
            bio_element = driver.find_element(By.XPATH, "//section/main/div/header/section//span[@class='_ap3a _aaco _aacu _aacx _aad7 _aade']")
            bio = bio_element.text.replace("\n", " ")  # Replace newlines with spaces
        except Exception:
            bio = ""
            print("[WARN] Bio not found.")

        if not isNiche(bio, NICHE):
            print(f"[SKIP] @{username} does not match the niche.")
            return None
        else:
            print(f"[INFO] @{username} matches the niche.")

        # Scrape followers
        try:
            followers_element = driver.find_element(By.XPATH, "//ul//li//a")
            followers = followers_element.get_attribute('title') or followers_element.text
            followers = parse_followers(followers)
            if followers > MAX_FOLLOWERS or followers < MIN_FOLLOWERS:
                print(f"[SKIP] @{username} has {followers} followers, outside the specified range.")
                return None
            else:
                print(f"[INFO] @{username} has {followers} followers.")
        except Exception:
            followers = "UNKNOWN"
            print("[WARN] Followers count not found.")

        # Scrape last post date
        try:
            post_container = driver.find_element(By.XPATH, "(//div[contains(@style, 'position: relative') and .//img])[1]")

            # Iterate over rows
            for row_index in range(1, 10):
                try:
                    row = post_container.find_element(By.XPATH, f"./div[{row_index}]")

                    # Iterate over posts in the row
                    posts = row.find_elements(By.XPATH, "./div")
                    for post_index, post_candidate in enumerate(posts, start=1):
                        pinned = post_candidate.find_elements(By.XPATH, ".//*[@aria-label='Pinned post icon']")
                        if not pinned:
                            post = post_candidate
                            print(f"[INFO] Selected post in row {row_index}, column {post_index} without pinned icon.")
                            raise StopIteration  # Exit both loops
                        else:
                            print(f"[DEBUG] Post in row {row_index}, column {post_index} is pinned. Skipping...")
                except NoSuchElementException:
                    print(f"[DEBUG] Row div[{row_index}] not found or empty.")
                    break
            else:
                raise Exception("No post found without 'Pinned post icon'.")

        except StopIteration:
            pass


            post.click()
            random_sleep(2, 4)
            post_time_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//time[contains(@datetime, 'T')]"))
            )
            post_time_element = driver.find_element(By.XPATH, "//time[contains(@datetime, 'T')]")
            last_post_date = post_time_element.get_attribute('datetime').replace("T", " ").replace("Z", "")
            last_post_date = last_post_date.split(".")[0]  # Remove milliseconds
            last_post_date = last_post_date.replace(":", "-")  # Replace colons with dashes for CSV compatibility
            print(f"[DEBUG] Last post date: {last_post_date}")
            # Convert string to datetime object
            try:
                post_datetime = datetime.strptime(last_post_date, "%Y-%m-%d %H-%M-%S")
                if post_datetime < datetime.now() - timedelta(days=60):
                    print(f"[SKIP] @{username} hasn't posted in over 2 months.")
                    return None
            except Exception as e:
                print(f"[WARN] Could not parse last post date: {e}")

        except Exception:
            last_post_date = ""
            print("[WARN] Last post date not found.")

        # Sanitize all text fields to remove newlines
        return {
            "Username": username,
            "Bio": bio.replace("\n", " "),  # Replace newlines with spaces
            "Followers": followers,
            "Last_Post_Date": last_post_date.replace("\n", " ") if last_post_date else "",
            "How_Found": f"@{TARGET_USERNAME}".replace("\n", " ")
        }

    except Exception as e:
        print(f"[ERROR] Failed to scrape @{username}: {e}")
        return None

def save_to_csv(user_data_list):
    # Ensure the 'data' folder exists
    data_folder = "data"
    os.makedirs(data_folder, exist_ok=True)

    # Save the CSV file in the 'data' folder
    csv_path = os.path.join(data_folder, CSV_FILENAME)
    keys = ["Username", "Bio", "Followers", "Last_Post_Date", "How_Found"]
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(user_data_list)
        print(f"[INFO] Saved {len(user_data_list)} users to {csv_path}")
    except PermissionError:
        print(f"[ERROR] Cannot write to {csv_path}. Close the file and retry.")

# --- Run Script ---
try:
    print("[INFO] Starting script...")
    login()
    users_with_followers = get_follower_usernames()
    print(users_with_followers)
    user_data = []

    for username in users_with_followers:  # Assuming users_with_followers is a list of usernames
        print(f"[DEBUG] Scraping info for {username}...")
        info = scrape_user_info(username)
        if info:
            # Directly fetch follower count
            followers = get_follower_count(driver.find_element(By.LINK_TEXT, username))
            info['Followers'] = followers
            user_data.append(info)
            save_to_csv(user_data)  # Save incrementally

    print(f"✅ DONE! Collected and saved {len(user_data)} users successfully.")

finally:
    try:
        if driver:
            print("[EXIT] Closing the browser...")
            driver.quit()
            del driver  # ensures __del__ doesn't trigger
            print("[EXIT] Browser closed successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to close the browser: {e}")
    sys.exit()
