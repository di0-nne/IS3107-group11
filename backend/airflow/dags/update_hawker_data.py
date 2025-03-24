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
