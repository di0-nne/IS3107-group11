from fastapi import APIRouter,Response, Depends, Body, HTTPException
from models.docs import *
from database import *
from models.schemas import *
from models.getters import *
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

@router.get("/openingHours")
def openingHours():
    return getOpeningHours()

@router.get("/reviews")
def reviews():
    return getReviews()

# @router.get("/userHistory")
# def userHistory():
#     return getUserHistory()