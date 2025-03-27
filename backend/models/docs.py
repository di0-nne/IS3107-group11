from pydantic import BaseModel

# TODO: do the same for Hawker Stall and User
class Hawker_Centre(BaseModel):
    name: str
    address: str
    type: str
    owner: str
    latitude: str
    longitude: str
    description: str
    status: str

