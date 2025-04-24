from pydantic import BaseModel
from datetime import datetime

# TODO: do the same for Hawker Stall and User
class Hawker_Centre(BaseModel):
    centre_id: str
    name: str
    address: str
    # type: str
    # owner: str
    latitude: str
    longitude: str
    description: str
    status: str

class Cleaning_Schedule(BaseModel):
    schedule_id: str
    centre_id: str
    cleaning_quarter: str
    cleaning_startdate: datetime
    cleaning_enddate: datetime
    remarks: str

class Hawker_Stall(BaseModel):
    stall_id: str
    name: str
    hawker_centre_id: str
    rating: float
    business_status: str
    url: str
    

class Opening_Hours(BaseModel):
    stall_id: str
    day_of_week: int
    open_time: str
    close_time: str
    
class Reviews(BaseModel):
    author_url: str
    author: str
    stall_id: str
    rating: float
    review_text: str
    relative_time: str
    

class User_History(BaseModel):
    visit_id: str
    user_id: str
    stall_id: str
    visit_timestamp: datetime
