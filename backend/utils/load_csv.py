import pandas as pd
from database import db
from datetime import datetime
from models.docs import Cleaning_Schedule
from models.docs import Hawker_Centre
import uuid
import requests

def parse_date(date_str):
    try:
        # Converts a string (like "15/03/2024") into a proper datetime object.
        return pd.to_datetime(date_str, dayfirst=True, errors='coerce')  # errors='coerce' turns invalid dates into NaT instead of crashing.
    except:
        return None


def load_cleaning_schedules():
    dataset_id = "d_bda4baa634dd1cc7a6c7cad5f19e2d68"
    url = "https://data.gov.sg/api/action/datastore_search?resource_id="  + dataset_id

    response = requests.get(url)
    records_json = response.json()

    # Extract records from JSON
    raw_records = records_json["result"]["records"]
    df = pd.DataFrame(raw_records)

    records = []

    for index, row in df.iterrows():  # iterate through each row
        centre_id = str(row["serial_no"])

        for quarter in ["q1", "q2", "q3", "q4"]:
            start = parse_date(row[f"{quarter}_cleaningstartdate"])
            end = parse_date(row[f"{quarter}_cleaningenddate"])
            remarks = row.get(f"remarks_{quarter}", "")

            if pd.notna(start) and pd.notna(end):
                validated = Cleaning_Schedule(
                    schedule_id=str(uuid.uuid4()),  # generates a unique schedule_id
                    centre_id=centre_id,
                    stall_name= row.get("name"),
                    cleaning_quarter=quarter.upper(),
                    cleaning_startdate=start,
                    cleaning_enddate=end,
                    remarks=remarks
                )
                records.append(validated.model_dump())  # convert pydantic model to regular python dictionary

    if records:
        db.cleaning_schedule.insert_many(records)
        print(f"Inserted {len(records)} cleaning schedules into MongoDB.")
    else:
        print("No valid records found.")

def load_hawker_centres():
    dataset_id = "d_bda4baa634dd1cc7a6c7cad5f19e2d68"
    url = "https://data.gov.sg/api/action/datastore_search?resource_id="  + dataset_id

    response = requests.get(url)
    records_json = response.json()

    # Extract records from JSON
    raw_records = records_json["result"]["records"]
    df = pd.DataFrame(raw_records)

    records = []

    for index, row in df.iterrows():
        validated = Hawker_Centre(
            centre_id=str(row["serial_no"]),
            name=row.get("name", ""),
            address=row.get("address_myenv", ""),
            latitude=str(row.get("latitude_hc", "")),
            longitude=str(row.get("longitude_hc", "")),
            description=row.get("description_myenv", ""),
            status=row.get("status", "")
        )

        records.append(validated.model_dump())

    if records:
        db.hawker_centre.insert_many(records)
        print(f"Inserted {len(records)} hawker centres into MongoDB.")
    else:
        print("No hawker centre records found.")

if __name__ == "__main__":
    load_cleaning_schedules()
    load_hawker_centres()



# async def load_csv_to_db():
#     df = pd.read_csv("data/DatesofHawkerCentresClosure.csv")
#     records = df.to_dict(orient="records")
#     #TODO: configure csv to fit document attributes
#     await db.hawkers_centre.insert_many(records)