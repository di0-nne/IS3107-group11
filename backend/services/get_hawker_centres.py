import pandas as pd
from database import db
from models.docs import Hawker_Centre
import requests

def extract_hawker_centres():
    dataset_id = "d_bda4baa634dd1cc7a6c7cad5f19e2d68"
    url = "https://data.gov.sg/api/action/datastore_search?resource_id="  + dataset_id

    response = requests.get(url)
    records_json = response.json()

    # Extract records from JSON
    raw_records = records_json["result"]["records"]
    df = pd.DataFrame(raw_records)

    df.rename(columns={
        "serial_no": "centre_id",
        "name": "name",
        "address_myenv": "address",
        "latitude_hc": "latitude",
        "longitude_hc": "longitude",
        "description_myenv": "description",
        "status": "status"
    }, inplace=True)

    return df


def load_hawker_centres(df):
    # db.hawker_centre.delete_many({})
    records = []

    for index, row in df.iterrows():
        validated = Hawker_Centre(
            centre_id=float(row["centre_id"]),
            name=row.get("name", ""),
            address=row.get("address", ""),
            latitude=str(row.get("latitude", "")),
            longitude=str(row.get("longitude", "")),
            zipcode=str(row.get("zipcode", "")),
            description=row.get("description", ""),
            status=row.get("status", "")
        )
        records.append(validated.model_dump())
        print("Inserting hawker centre with zip:", row.get("zipcode"))

    if records:
        db.hawker_centre.insert_many(records)
        print(f"Inserted {len(records)} hawker centres into MongoDB.")


    # records = []

    # for index, row in df.iterrows():
    #     validated = Hawker_Centre(
    #         centre_id=float(row["serial_no"]),
    #         name=row.get("name", ""),
    #         address=row.get("address_myenv", ""),
    #         latitude=str(row.get("latitude_hc", "")),
    #         longitude=str(row.get("longitude_hc", "")),
    #         description=row.get("description_myenv", ""),
    #         status=row.get("status", "")
    #     )

    #     records.append(validated.model_dump())

    # if records:
    #     db.hawker_centre.insert_many(records)
    #     print(f"Inserted {len(records)} hawker centres into MongoDB.")
    # else:
    #     print("No hawker centre records found.")