from models.schemas import *
from database import *

def getHawkerCentres():
    return get_hawker_centre_list(hawker_centre_db.find())

def getCleaningSchedules():
    return get_cleaning_schedule_list(cleaning_schedule_db.find())

def getHawkerStalls():
    return get_hawker_stall_list(hawker_stall_db.find())

def getHawkerStallsByCentreId(centreId: str):
    return get_hawker_stall_list(hawker_stall_db.find({"centre_id": {"$eq": centreId}}))

def getHawkerStallByIds(stallIds: list):
    return get_hawker_stall_list(hawker_stall_db.find({"stall_id": {"$in": stallIds}}))

def getOpeningHours():
    return get_opening_hours_list(opening_hours_db.find())

# TODO: find by date and location?

def getReviewsById(stallId: str):
    return get_reviews_list(reviews_db.find({"stall_id": {"$eq": stallId}}))

# TODO: get reviews by stall_id and centre_id?

def getUserHistory():
    return get_user_history_list(user_history_db.find())

def getGeographicalData():
    return get_geographical_hc_data_list(geographical_hc_db.find())

def getHSReviewStats(stallId):
    return get_hs_review_stats_list(hs_review_stats_db.find({"stall_id": {"$eq": stallId}}))