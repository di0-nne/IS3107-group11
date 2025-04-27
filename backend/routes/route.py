from fastapi import APIRouter,Response, Depends, Body, HTTPException
from models.docs import *
from database import *
from models.schemas import *
from models.getters import *
from transformers.analytics_transformer import *
from bson import ObjectId

router = APIRouter()

@router.get("/hawkerCentres")
def hawkerCentres():
    return getHawkerCentres()

@router.get("/cleaningSchedule")
def cleaningSchedule():
    return getCleaningSchedules()

@router.get("/hawkerStalls")
def hawkerStalls():
    return getHawkerStalls()

@router.get("/hawkerStallByCentreId")
def hawkerStallsByCentreId(centreId: int):
    return getHawkerStallsByCentreId(centreId)

@router.get("/openingHours")
def openingHours():
    return getOpeningHours()

@router.get("/reviews")
def reviews(stallId: str):
    return getReviewsById(stallId)

@router.get("/geographicalData")
def geographicalData():
    return getGeographicalData()

@router.get("/reviewsDataForStall")
def reviewsData(stallId:str):
    return getHSReviewStats(stallId)