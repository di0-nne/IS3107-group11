import sys
import os

# Add the backend directory (which contains 'services') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from services.get_cleaning_schedules import load_cleaning_schedules
from services.get_hawker_centres import load_hawker_centres
from services.get_hawker_stalls import get_hawkerstalls_df
from services.get_reviews import get_all_reviews
from database import db
import pandas as pd


def extract_hawker_stalls():
    # Fetch only 1 hawker centre from MongoDB
    single_centre = list(db.hawker_centre.find().limit(1))
    print("Extracted hawker centre:", single_centre)
    df = pd.DataFrame(single_centre)

    # Add zipcode column 
    df["zipcode"] = df["address"].astype(str).str[-6:]
    df.sort_values(by=['latitude'], inplace=True)
    get_hawkerstalls_df(df)

def extract_reviews():
    df = pd.DataFrame(list(db.hawker_stall.find()))
    df = df.head(10)
    get_all_reviews(df)
    print("Extracting reviews for:", df[["name", "url"]])

with DAG(
    dag_id='update_hawker_data',
    start_date = datetime(2025, 1, 1),
    description='ETL pipeline to load hawker data into MongoDB',
    schedule_interval='@weekly',
    catchup=False,
    tags=["hawker"]
) as dag:
    
    t1 = PythonOperator(
        task_id='load_cleaning_schedules',
        python_callable=load_cleaning_schedules,
    )

    t2 = PythonOperator(
        task_id='load_hawker_centres',
        python_callable=load_hawker_centres,
    )

    t3 = PythonOperator(
        task_id='extract_hawker_stalls',
        python_callable=extract_hawker_stalls,
    )

    t4 = PythonOperator(
        task_id='extract_reviews',
        python_callable=extract_reviews,
    )


    [t1, t2] >> t3 >> t4

### example
# 
# from airflow import DAG
# from airflow.operators.python import PythonOperator
# from datetime import datetime
# import requests
# from database import get_mongo_collection

# def fetch_google_places_data():
#     api_key = "YOUR_GOOGLE_PLACES_API_KEY"
#     url = f"https://maps.googleapis.com/maps/api/place/details/json?parameters&key={api_key}"
#     response = requests.get(url)
#     data = response.json()
    
#     collection = get_mongo_collection()
#     for stall in data["results"]:
#         collection.update_one({"place_id": stall["place_id"]}, {"$set": stall}, upsert=True)

# with DAG("update_hawker_data", start_date=datetime(2024, 1, 1), schedule_interval="@daily") as dag:
#     fetch_task = PythonOperator(
#         task_id="fetch_data",
#         python_callable=fetch_google_places_data
#     )
