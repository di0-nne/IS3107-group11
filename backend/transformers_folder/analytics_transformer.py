from database import *
from models.schemas import *
from models.getters import *
from collections import defaultdict, Counter
import math
import string

def calculate_standard_deviation(ratings, mean):
    """Helper function to calculate standard deviation."""
    if len(ratings) < 2:
        return 0
    variance = sum((x - mean) ** 2 for x in ratings) / len(ratings)
    return math.sqrt(variance)

def clean_text(text):
    """Helper function to clean and tokenize review text."""
    text = str(text).lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text.split()


def transform_hc_geographical_data():
    centres = list(hawker_centre_db.find({}, {
        '_id': 0,
        'centre_id': 1,
        'name': 1,
        'latitude': 1,
        'longitude': 1
    }))   # remove before submission
    
    stalls = list(hawker_stall_db.find({}, {
        '_id': 0,
        'centre_id': 1,
        'name': 1,
        'rating': 1
    }))   # remove before submission

    centre_ratings = defaultdict(list)
    stall_ratings = defaultdict(list)

    for stall in stalls:
        cid = stall['centre_id']
        if 'rating' != None and not math.isnan(stall['rating']):
            centre_ratings[cid].append(stall['rating'])
            stall_ratings[cid].append((stall['name'], stall['rating']))

    output = []
    for centre in centres:
        cid = centre['centre_id']
        ratings = centre_ratings.get(cid, [])
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0
        top3_stalls = sorted(stall_ratings[cid], key=lambda x: x[1], reverse=True)[0:3]

        output.append({
            'centre_id': cid,
            'name': centre['name'],
            'latitude': centre['latitude'],
            'longitude': centre['longitude'],
            'avg_rating': avg_rating,
            'stalls': len(ratings),
            'top3_stalls': 
                [
                    {"stall_name": name, "rating": rating}
                        for name, rating in top3_stalls
                ]
        })
        
    geographical_hc_db.delete_many({})
    geographical_hc_db.insert_many(output)


def transform_hs_review_stats():
    
    # to choose either one
    stalls = getHawkerStalls()  # remove before submission
    # stalls = getHawkerStallByIds(["ChIJVYpDvb8b2jERnf4SUGQIN4A","ChIJX9Gg9K8b2jEREH0a-0yVcGc", "ChIJEQSoKWAZ2jERbjFv-zHyLRo",
    #                             "ChIJRRxyTrUZ2jERWlYbp4FdxKk","ChIJkeXybmAZ2jER1wI3s3SBPRI", "ChIJ82mn4sIb2jERgXdSpagSZUg",
    #                             "ChIJM0fGcO4b2jERfL3KacFWHPU","ChIJgfhr2lcb2jERAHIZ1f8N-Xg", "ChIJRR6-XAob2jERDVQYlQfj4gA",
    #                             "ChIJ82mn4sIb2jER-iAy--xuMsI", "ChIJ82mn4sIb2jERivrtL3P0XBM", "ChIJCd8s9a8b2jERGoFGSjv4DMw"
    #                             ])
    #############
    
    stall_to_reviews = defaultdict(list)
    user_to_reviews = defaultdict(list)
    
    filler_words = set([
        "the", "is", "a", "of", "to", "and", "in", "for", "on", "with", "that", "this", 
        "it", "as", "was", "at", "by", "an", "be", "or", "have", "are", "but", "not", "which",
        "i", "you", "he", "she", "it", "we", "they", "them", "his", "her", "him", "hers", "their",
        "my", "your", "his", "her", "its", "our", "theirs", "that", "this", "these", "those",
        "...", "person", "has", "mr", "mrs", "miss", "mr.", "mrs.", "miss.", "mr", "mrs", "miss",
        "can", "could", "may", "might", "must", "will", "should", "shall", "do", "does", "did",
        "am", "is", "are", "was", "were", "been", "being", "have", "had", "has", "will", "shall",
        "place"
    ])
    
    for stall in stalls:
        hs_review_stats_db.delete_one({"stall_id": stall['stall_id']})
        
        stall_id = stall['stall_id']
        reviews_for_stall = getReviewsById(stall_id) 
        stall_to_reviews[stall_id] = reviews_for_stall
        
        unique_authors = set()
        for review in reviews_for_stall:
            user_to_reviews[review['author']].append(review)
            unique_authors.add(review['author'])
        
        no_of_reviews = len(reviews_for_stall)
        ratings = [float(review['rating']) for review in reviews_for_stall]
        avg_user_rating = sum(ratings) / no_of_reviews if ratings else 0
        review_texts = [review['review_text'] for review in reviews_for_stall]
        rating_sd = calculate_standard_deviation(ratings, avg_user_rating)
        print(no_of_reviews, len(unique_authors), avg_user_rating, rating_sd)
        avg_no_of_visits = no_of_reviews / len(unique_authors) if unique_authors else 0
    
        all_words = []
        for text in review_texts:
            words = clean_text(text)
            all_words.extend(words)
        
        word_counts = Counter(word for word in all_words if word not in filler_words)
        top_10_words = word_counts.most_common(10)
        
        stats = {
            'stall_id': stall_id,
            'stall_name': stall['name'],
            'no_of_reviews': no_of_reviews,
            'no_of_authors': len(unique_authors),
            'avg_user_rating': round(avg_user_rating, 2),
            'rating_sd': round(rating_sd, 2),
            'avg_no_of_visits': avg_no_of_visits,
            'top_10_words': top_10_words
        }
        
        hs_review_stats_db.insert_one(stats)
    