from database import *
from models.schemas import *
from models.getters import *
from collections import defaultdict
import math

def geographical_data():
    centres = list(hawker_centre_db.find({}, {
        '_id': 0,
        'centre_id': 1,
        'name': 1,
        'latitude': 1,
        'longitude': 1
    }))

    # Step 2: Get all stalls and group them by centre_id
    stalls = list(hawker_stall_db.find({}, {
        '_id': 0,
        'centre_id': 1,
        'name': 1,
        'rating': 1
    }))

    centre_ratings = defaultdict(list)

    for stall in stalls:
        cid = stall['centre_id']
        if 'rating' is not None and not math.isnan(stall['rating']):
            centre_ratings[cid].append(stall['rating'])

    output = []
    for centre in centres:
        cid = centre['centre_id']
        ratings = centre_ratings.get(cid, [])
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

        output.append({
            'centre_id': cid,
            'name': centre['name'],
            'latitude': centre['latitude'],
            'longitude': centre['longitude'],
            'avg_rating': avg_rating,
            'stalls': len(ratings)
        })
        
    return output
