import math

def get_hawker_centre(Hawker_Centre) -> dict:
    return {
        "id": str(Hawker_Centre["_id"]),
        "centre_id": Hawker_Centre["centre_id"],
        "name": Hawker_Centre["name"],
        "address": Hawker_Centre["address"],
        "latitude": Hawker_Centre["latitude"],
        "longitude": Hawker_Centre["longitude"],
        "description": Hawker_Centre["description"],
        "status": Hawker_Centre["status"]
    }
    
def get_hawker_centre_list(Hawker_Centres) -> list:
    return [get_hawker_centre(hc) for hc in Hawker_Centres]

def get_cleaning_schedule(Cleaning_Schedule) -> dict:
    return {
        "id": str(Cleaning_Schedule["_id"]),
        "schedule_id": str(Cleaning_Schedule["schedule_id"]), #or we can use auto-generated _id
        "centre_id": Cleaning_Schedule["centre_id"],
        "cleaning_quarter": Cleaning_Schedule["cleaning_quarter"],
        "cleaning_startdate": Cleaning_Schedule["cleaning_startdate"],
        "cleaning_enddate": Cleaning_Schedule["cleaning_enddate"],
        "remarks": Cleaning_Schedule["remarks"]
    }
    
def get_cleaning_schedule_list(Cleaning_Schedules) -> list:
    return [get_cleaning_schedule(cs) for cs in Cleaning_Schedules]

def get_hawker_stall(Hawker_Stall) -> dict:
    return {
        "id": str(Hawker_Stall["_id"]),
        "stall_id": Hawker_Stall["stall_id"],
        "name": Hawker_Stall["name"],
        "centre_id": Hawker_Stall["centre_id"],
        "rating": Hawker_Stall["rating"],
        "business_status": Hawker_Stall["business_status"],
        "url": Hawker_Stall["url"]
    }
    
def get_hawker_stall_list(Hawker_Stalls) -> list:
    return [get_hawker_stall(hs) for hs in Hawker_Stalls]

def get_opening_hours(Opening_Hours) -> dict:
    return {
        "id": str(Opening_Hours["_id"]),
        "day_of_week": Opening_Hours["day_of_week"],
        "open_time": Opening_Hours["open_time"],
        "close_time": Opening_Hours["close_time"]
    }
    
def get_opening_hours_list(Opening_Hours) -> list:
    return [get_opening_hours(oh) for oh in Opening_Hours]

def get_reviews(Reviews) -> dict:
    return {
        "id": str(Reviews["_id"]),
        "author_url": Reviews["author_url"],
        "author": Reviews["author"],
        "stall_id": Reviews["stall_id"],
        "rating": str(Reviews["rating"]),
        "review_text": Reviews["review_text"],
        "relative_time": Reviews["relative_time"]
    }
    
def get_reviews_list(Reviews) -> list:
    return [get_reviews(r) for r in Reviews]

def get_user_history(User_History) -> dict:
    return {
        "id": str(User_History["_id"]),
        "visit_id": User_History["visit_id"],
        "user_id": User_History["user_id"],
        "stall_id": User_History["stall_id"],
        "visit_timestamp": User_History["visit_timestamp"]
    }
    
def get_user_history_list(User_History) -> list:
    return [get_user_history(uh) for uh in User_History]

def get_geographical_hc_data(Geographical_HC_Data) -> dict:
    return {
        "id": str(Geographical_HC_Data["_id"]),
        "centre_id": Geographical_HC_Data["centre_id"],
        "name": Geographical_HC_Data["name"],
        "latitude": Geographical_HC_Data["latitude"],
        "longitude": Geographical_HC_Data["longitude"],
        "avg_rating": Geographical_HC_Data["avg_rating"],
        "stalls": Geographical_HC_Data["stalls"],
        "top3_stalls": Geographical_HC_Data["top3_stalls"]
    }
    
def get_geographical_hc_data_list(Geographical_HC_Data) -> list:
    return [get_geographical_hc_data(g) for g in Geographical_HC_Data]

def get_hs_review_stats(HS_Review_Stats) -> dict:
    return {
        "id": str(HS_Review_Stats["_id"]),
        "stall_id": HS_Review_Stats["stall_id"],
        "stall_name": HS_Review_Stats["stall_name"],
        "no_of_reviews": HS_Review_Stats["no_of_reviews"],
        "no_of_authors": HS_Review_Stats["no_of_authors"],
        "avg_user_rating": HS_Review_Stats["avg_user_rating"],
        "rating_sd": HS_Review_Stats["rating_sd"],
        "avg_no_of_visits": HS_Review_Stats["avg_no_of_visits"],
        "top_10_words": HS_Review_Stats["top_10_words"]
    }
    
def get_hs_review_stats_list(HS_Review_Stats) -> list:    
    return [get_hs_review_stats(h) for h in HS_Review_Stats]