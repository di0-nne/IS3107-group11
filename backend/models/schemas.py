# TODO: do the same for Hawker Stall and User
def get_hawker_centre(Hawker_Centre) -> dict:
    return {
        "id": str(Hawker_Centre["_id"]),
        "name": Hawker_Centre["name"],
        "address": Hawker_Centre["address"],
        "type": Hawker_Centre["type"],
        "owner": Hawker_Centre["owner"],
        "latitude": Hawker_Centre["latitude"],
        "longitude": Hawker_Centre["longitude"],
        "description": Hawker_Centre["description"],
        "status": Hawker_Centre["status"]
    }
    
def get_hawker_centre_list(Hawker_Centres) -> list:
    return [get_hawker_centre(hc) for hc in Hawker_Centres]