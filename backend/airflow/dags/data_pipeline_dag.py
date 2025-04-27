import sys
import os

# Add the backend directory (which contains 'services') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from services.get_cleaning_schedules import load_cleaning_schedules
from services.get_hawker_centres import extract_hawker_centres, load_hawker_centres
from services.get_hawker_stalls import get_hawkerstalls_df
from services.get_reviews import get_all_reviews
from transformers_folder.transform_datasets import transform_hawkers, transform_reviews, transform_stalls
from transformers_folder.normalisation import normalise_stalls, normalise_reviews
from recommenders.BERT import BERTRecommender
from recommenders.deepFM import DeepFMRecommender
from recommenders.NGCF import NGCFRecommender
from transformers_folder.analytics_transformer import transform_hc_geographical_data, transform_hs_review_stats
from recommenders.BERT import BERTRecommender, NGCFRecommender, DeepFMRecommender
from database import db
import pandas as pd


def extract_hawker_centres_task(**kwargs):
    df = extract_hawker_centres()
    kwargs['ti'].xcom_push(key='raw_hawker_centres', value=df.to_json())


def transform_hawker_centres_task(**kwargs):
    raw_json = kwargs['ti'].xcom_pull(key='raw_hawker_centres')
    df = pd.read_json(raw_json)
    transformed_df = transform_hawkers(df)
    kwargs['ti'].xcom_push(key='transformed_hawker_centres', value=transformed_df.to_json())

def load_hawker_centres_task(**kwargs):
    transformed_json = kwargs['ti'].xcom_pull(key='transformed_hawker_centres')
    df = pd.read_json(transformed_json)
    load_hawker_centres(df)

def extract_hawker_stalls_task(**kwargs):
    limit_centre = list(db.hawker_centre.find().limit(1))
    df = pd.DataFrame(limit_centre)
    stalls_df = get_hawkerstalls_df(df)
    kwargs['ti'].xcom_push(key='raw_stalls', value=stalls_df.to_json())

def transform_hawker_stalls_task(**kwargs):
    raw_stalls_json = kwargs['ti'].xcom_pull(key='raw_stalls')
    df = pd.read_json(raw_stalls_json)
    print("Transform Stalls: Available columns =>", df.columns)
    print(df.head())
    transformed_df = transform_stalls(df)
    kwargs['ti'].xcom_push(key='transformed_stalls', value=transformed_df.to_json())

def load_hawker_stalls_task(**kwargs):
    stalls_json = kwargs['ti'].xcom_pull(key='transformed_stalls')
    df = pd.read_json(stalls_json)
    db.fake_hawker_stall.insert_many(df.to_dict(orient="records")) # change before submission

def extract_reviews_task(**kwargs):
    df = pd.read_json(kwargs['ti'].xcom_pull(key='transformed_stalls'))
    # df = df.head(10)  # Optional: Limit number of stalls
    all_reviews_df = get_all_reviews(df)
    kwargs['ti'].xcom_push(key='raw_reviews', value=all_reviews_df.to_json())

def transform_reviews_task(**kwargs):
    raw_reviews_json = kwargs['ti'].xcom_pull(key='raw_reviews')
    df = pd.read_json(raw_reviews_json)
    cleaned_df = transform_reviews(df)
    kwargs['ti'].xcom_push(key='transformed_reviews', value=cleaned_df.to_json())

def load_reviews_task(**kwargs):
    reviews_json = kwargs['ti'].xcom_pull(key='transformed_reviews')
    df = pd.read_json(reviews_json)
    db.fake_reviews.insert_many(df.to_dict(orient="records"))  # change before submission
    
def transform_analytics(**kwargs):
    print("transforming hawker centre data for geographical analysis")
    transform_hc_geographical_data()
    print("transforming hawker stall review data")
    transform_hs_review_stats()

def transform_recommenders(**kwargs):
    # stalls_json = kwargs['ti'].xcom_pull(key='transformed_stalls')
    stalls_cursor = db.hawker_stall.find({})
    stalls_list = list(stalls_cursor)
    stalls_df = pd.DataFrame(stalls_list)
    normalised_stalls_df = normalise_stalls(stalls_df)
    if '_id' in normalised_stalls_df.columns:
        normalised_stalls_df = normalised_stalls_df.drop(columns=['_id'])   # remove if required
    kwargs['ti'].xcom_push(key='normalised_stalls', value=normalised_stalls_df.to_json())

    # reviews_json = kwargs['ti'].xcom_pull(key='transformed_reviews')
    reviews_cursor = db.reviews.find({})
    reviews_list = list(reviews_cursor)
    reviews_df = pd.DataFrame(reviews_list)
    normalised_reviews_df = normalise_reviews(reviews_df)
    if '_id' in normalised_reviews_df.columns:
        normalised_reviews_df = normalised_reviews_df.drop(columns=['_id'])   # remove if required
    kwargs['ti'].xcom_push(key='normalised_reviews', value=normalised_reviews_df.to_json())

def run_recommenders(**kwargs):
    stalls_json = kwargs['ti'].xcom_pull(key='normalised_stalls')
    stalls = pd.read_json(stalls_json)
    reviews_json = kwargs['ti'].xcom_pull(key='normalised_reviews')
    reviews = pd.read_json(reviews_json)

    BERTrecommender = BERTRecommender()
    hitrate_df, metric_df = BERTrecommender.run(stalls, reviews)
    hr_records = hitrate_df.to_dict(orient='records')
    mr_records = metric_df.to_dict(orient='records')
    db.bert_hitrate.insert_many(hr_records)
    db.bert_metrics.insert_many(mr_records)

    NGCFrecommender = NGCFRecommender()
    hitrate_df, metric_df = NGCFrecommender.run(stalls, reviews)
    hr_records = hitrate_df.to_dict(orient='records')
    mr_records = metric_df.to_dict(orient='records')
    db.ngcf_hitrate.insert_many(hr_records)
    db.ngcf_metrics.insert_many(mr_records)

    DeepFMrecommender = DeepFMRecommender()
    hitrate_df, metric_df = DeepFMrecommender.run(stalls, reviews)
    hr_records = hitrate_df.to_dict(orient='records')
    mr_records = metric_df.to_dict(orient='records')
    db.deepfm_hitrate.insert_many(hr_records)
    db.deepfm_metrics.insert_many(mr_records)


with DAG(
    dag_id='update_hawker_data',
    start_date = datetime(2025, 1, 1),
    description='ETL pipeline to load hawker data into MongoDB',
    schedule_interval='@weekly',
    catchup=False,
    tags=["hawker"]
) as dag:
    
    t1 = PythonOperator(task_id='load_cleaning_schedules', python_callable=load_cleaning_schedules)

    t2a = PythonOperator(task_id='extract_hawker_centres', python_callable=extract_hawker_centres_task)
    t2b = PythonOperator(task_id='transform_hawker_centres', python_callable=transform_hawker_centres_task)
    t2c = PythonOperator(task_id='load_hawker_centres', python_callable=load_hawker_centres_task)

    t3a = PythonOperator(task_id='extract_hawker_stalls', python_callable=extract_hawker_stalls_task)
    t3b = PythonOperator(task_id='transform_hawker_stalls', python_callable=transform_hawker_stalls_task)
    t3c = PythonOperator(task_id='load_hawker_stalls', python_callable=load_hawker_stalls_task)

    t4a = PythonOperator(task_id='extract_reviews', python_callable=extract_reviews_task)
    t4b = PythonOperator(task_id='transform_reviews', python_callable=transform_reviews_task)
    t4c = PythonOperator(task_id='load_reviews', python_callable=load_reviews_task)

    t5 = PythonOperator(task_id='transform_analytics', python_callable=transform_analytics)
    
    t6a = PythonOperator(task_id='transform_recommenders', python_callable=transform_recommenders)
    t6b = PythonOperator(task_id='run_recommenders', python_callable=run_recommenders)


    t1 >> t2a >> t2b >> t2c >> t3a >> t3b >> t3c >> t4a >> t4b >> t4c
    t4c >> [t5, t6a]
    t6a >> t6b
    
