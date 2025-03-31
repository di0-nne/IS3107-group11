from models.schemas import *
from database import *

def getHawkerCentres():
    return get_hawker_centre_list(hawker_centre_db.find())

def getCleaningSchedules():
    return get_cleaning_schedule_list(cleaning_schedule_db.find())

def getHawkerStalls():
    return get_hawker_stall_list(hawker_stall_db.find())

def getOpeningHours():
    return get_opening_hours_list(opening_hours_db.find())

# TODO: find by date and location?

def getReviews():
    return get_reviews_list(reviews_db.find())

# TODO: get reviews by stall_id and centre_id?

def getUserHistory():
    return get_user_history_list(user_history_db.find())