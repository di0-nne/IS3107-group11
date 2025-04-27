from pydantic import BaseModel
from datetime import datetime

# TODO: do the same for Hawker Stall and User
class Hawker_Centre(BaseModel):
    centre_id: float
    name: str
    address: str
    latitude: str
    longitude: str
    zipcode: str
    description: str
    status: str

class Cleaning_Schedule(BaseModel):
    schedule_id: str
    centre_id: float
    cleaning_quarter: str
    cleaning_startdate: datetime
    cleaning_enddate: datetime
    remarks: str

class Hawker_Stall(BaseModel):
    stall_id: str
    name: str
    centre_id: str
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
    
class Geographical_HC_data(BaseModel):
    centre_id: float
    name: str
    latitude: str
    longitude: str
    avg_rating: float
    stalls: float
    top3_stalls: object
    

class HC_Review_Stats(BaseModel):
    stall_id: str
    stall_name: str
    no_of_reviews: float
    no_of_authors: float
    avg_user_rating: float
    rating_sd: float
    avg_no_of_visits: float
    top_10_words: object