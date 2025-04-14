from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import time
import pandas as pd 
from bs4 import BeautifulSoup


### Set paths
mongo_link = "mongodb+srv://db_user:db_user123@cluster0.4e885.mongodb.net/?"

################################### extracting reviews ###################################


def get_reviews(url):

    """
    Extracts reviews from the given Google Maps URL.

    Parameters
    ----------
    url : str
        The URL of the Google Maps page to extract reviews from.

    Returns
    -------
    results : dict
        A dictionary where the keys are the names of reviewers and the values are
        dictionaries containing the review text, the link to the review, the rating,
        and the relative time of the review.

    Notes
    -----
    - This function uses Selenium to load the page and extract the reviews.
    - It scrolls to the bottom of the reviews page to load all the reviews.
    - It extracts the review text, the link to the review, the rating, and the relative
      time of the review from each review div.
    - It returns a dictionary where the keys are the names of reviewers and the values
      are dictionaries containing the extracted information.
    """
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    driver.get(url)

    try:
        reviews_button = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//button[.//div[contains(text(), "Reviews")]]'
        )))
        reviews_button.click()
    except Exception as e:
        print("could not click 'Reviews' tab:", e, url)
        driver.quit()
        return []

    time.sleep(3)

    try:
        scrollable_div = wait.until(EC.presence_of_element_located((
            By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]'
        )))
    except Exception as e:
        print("could not locate review div:", e)
        driver.quit()
        return []

    try:
        total_reviews_text = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[2]/div/div[2]/div[3]').text
        total_number_of_reviews = int(total_reviews_text.split(" ")[0].replace(",", ""))
        print(total_number_of_reviews)
    except:
        total_number_of_reviews = 30  # in case dh

    if total_number_of_reviews > 500:
        total_number_of_reviews = 500
        
    for i in range(0, round(total_number_of_reviews/10)):
        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', 
                scrollable_div)
        time.sleep(1)

    review_divs = driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf.fontBodyMedium')

    results = {}
    for i, div in enumerate(review_divs):
        try:
            name = div.find_element(By.CLASS_NAME, "d4r55").text
            button = div.find_element(By.CLASS_NAME, "al6Kxe")
            link = button.get_attribute("data-href")
            review_text = div.find_element(By.CSS_SELECTOR, 'div.MyEned span.wiI7pd').text.strip()
            rating_span = div.find_element(By.CLASS_NAME, "kvMYJc")
            rating = rating_span.get_attribute("aria-label")
            curr = {}
            curr['review'] = review_text
            curr['link'] = link
            curr['rating'] = rating.split(" ")[0]
            curr['relative_time'] = div.find_element(By.CLASS_NAME, "rsqaWe").text
            results[name] = curr
        except Exception as e:
            print(f'Failed for {url}', e)
    driver.quit()
    return results

def get_all_reviews(df):
    """
    Retrieves all reviews for each hawker stall in a given DataFrame and saves
    the reviews to separate CSV files.

    Args:
        df: A pandas DataFrame with columns 'name', 'place_id', and 'url' where
            each row represents a hawker stall.
        path: A string representing the directory path to save the review CSV
            files.

    Returns:
        None (saves .csv to output file path)
    """
    df = df.reset_index()
    for idx, row in df.iterrows():
        print(row.name)
        url = row.url
        name = row['name']
        reviews_result = get_reviews(url)
        temp = pd.DataFrame()
        if reviews_result:
            for i in reviews_result.keys():
                curr = reviews_result[i]
                entry = {
                    'author_url' : curr['link'],
                    'stall_id' : row.place_id,
                    'author' : i,
                    'review' : curr['review'],
                    'rating' : curr['rating'],
                    'relative_time' : curr['relative_time']
                }
                temp = pd.concat([temp, pd.DataFrame([entry])], ignore_index=True)

            if not temp.empty:
                client = MongoClient(mongo_link)
                db = client["IS3107-GROUP11"]
                collection = db["reviews"]
                collection.insert_many(temp.to_dict(orient="records"))