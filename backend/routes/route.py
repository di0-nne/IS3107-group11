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