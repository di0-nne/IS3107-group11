from models.schemas import *
from database import *

def getHawkerCentres():
    return get_hawker_centre_list(hawker_centre_db.find())
