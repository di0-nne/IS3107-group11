import pandas as pd
from database import db

async def load_csv_to_db():
    df = pd.read_csv("data/DatesofHawkerCentresClosure.csv")
    records = df.to_dict(orient="records")
    #TODO: configure csv to fit document attributes
    await db.hawkers_centre.insert_many(records)