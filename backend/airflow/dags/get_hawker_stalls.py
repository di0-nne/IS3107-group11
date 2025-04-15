from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import time
import googlemaps
import pandas as pd 
from bs4 import BeautifulSoup
import os 

### Set paths
mongo_link = "mongodb+srv://db_user:db_user123@cluster0.4e885.mongodb.net/?"
hawker_path = ""

### Set variables
API_KEY = os.environ['GOOGLE_API_KEY']
map_client = googlemaps.Client(API_KEY)

################################### clean dataset ###################################
# Clean DatesofHawkerCentresClosure.csv
df = pd.read_csv(hawker_path)
dfc = df[['name', 'address_myenv', 'latitude_hc', 'longitude_hc']]

# Load cleaned csv
dfc['zipcode'] = dfc['address_myenv'].astype(str).str[-6:]
dfc.rename(columns={
    'address_myenv':'address', 
    'latitude_hc':'latitude', 
    'longitude_hc':'longitude'}, inplace=True)
dfc.sort_values(by=['latitude'], inplace=True)

################################### extracting stalls ###################################

def get_place_response(place_id):
    """
    Retrieves place details from the Google Places API using a given place ID.

    Args:
        place_id (str): The place ID for which details are to be retrieved.

    Returns:
        dict: A dictionary containing the details of the place as returned by the API.
              Returns None if an error occurs.
    """

    try:
        response = map_client.place (
            place_id = place_id
        )    
        response = response['result']
        return response
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Use zipcode to find places with the same zipcode => get place_ids
def get_place_ids(zipcode, lat, lon):
    """
    Retrieves the place IDs of all places with the given zipcode.

    Args:
        zipcode (str): The zipcode for which the place IDs are to be retrieved.
        lat (float): The latitude of the starting point.
        lon (float): The longitude of the starting point.

    Returns:
        dict: A dictionary where the keys are the place IDs and the values are the details of the places.
              Returns an empty dictionary if no places are found.
    """
    def get_ids(curr, response):
        main_zip = str(zipcode)
        print(main_zip)
        result = response.get('results')
        for i in result:
            curr_id = i.get("place_id")
            new_response = get_place_response(curr_id)
            soup = BeautifulSoup(new_response['adr_address'], 'html.parser')
            postal_span = soup.find('span', class_='postal-code')
            if postal_span:
                postal_code = postal_span.text.strip()
                if postal_code == main_zip:
                    sub_result = {
                        "name": i.get("name"),
                        "place_id": curr_id,
                        "address": new_response['formatted_address'],
                        "business_status": i.get("business_status"),
                        "rating": i.get('rating'),
                        "url": new_response['url']
                    }
                    curr[curr_id] = sub_result
            else: 
                zip = new_response['formatted_address'][:-6]
                if str(zip) == main_zip:
                    sub_result = {
                        "name": i.get("name"),
                        "place_id": curr_id,
                        "address": new_response['formatted_address'],
                        "business_status": i.get("business_status"),
                        "rating": i.get('rating'),
                        "url": new_response['url']
                    }
                    curr[curr_id] = sub_result
        return curr

    curr = {}

    response = map_client.places_nearby(
        location=(lat, lon),
        rank_by="distance",
        type="food"
    )

    curr = get_ids(curr, response)
    next_page_token = response.get('next_page_token')
    while next_page_token:
        time.sleep(2)
        response = map_client.places_nearby(
            location=(lat, lon),
            page_token=next_page_token,
            rank_by="distance",
            type="food"
        )   
        curr = get_ids(curr, response)
        next_page_token = response.get('next_page_token')
    return curr

def get_hawkerstalls_df(hawker_df):
    """
    Retrieves a pandas DataFrame containing hawker stall details given a
    DataFrame of hawker centers.

    Args:
        hawker_df: A pandas DataFrame with columns 'latitude', 'longitude',
            and 'zipcode' where each row represents a hawker center.

    Returns:
        A pandas DataFrame with columns 'name', 'place_id', 'address',
        'business_status', and 'url' where each row represents a hawker
        stall.
    """
    columns = ['name', 'place_id', 'address', 'business_status', 'url']
    result_df = pd.DataFrame(columns=columns)
    for index, row in hawker_df.iterrows():
        idx = row.serial_no
        lan = row.latitude
        lon = row.longitude
        zip = row.zipcode
        hawker_dict = get_place_ids(zip, lan, lon)
        
        for hawker_id, details in hawker_dict.items():
            if 'rating' in details.keys():
                r = details['rating']
            else:
                r = "NIL"
            result_df.loc[len(result_df)] = {
                'name': details['name'],
                'stall_id': details['place_id'],
                'hawker_centre_id': idx,
                'business_status': details['business_status'],
                'url':details['url'],
                'rating': r
            }

    if not result_df.empty:
        client = MongoClient(mongo_link)
        db = client["IS3107-GROUP11"]
        collection = db["hawker_centre"]
        collection.insert_many(result_df.to_dict(orient="records"))
