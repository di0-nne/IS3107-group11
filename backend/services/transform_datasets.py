import pandas as pd 
import sys
import os
import re

def transform_hawkers(hawkers_full):
    hawkers_full["zipcode"] = hawkers_full["address"].astype(str).str[-6:]
    hawkers_full.sort_values(by=['latitude'], inplace=True)
    return hawkers_full

def transform_stalls(stalls_full): ## raw stalls dataset
    stalls_full['name_norm'] = (
        stalls_full['name']
        .fillna('')
        .str.lower()
        .str.strip()
        .str.replace(r'[^a-z0-9 ]', '', regex=True)
    )
    stalls_full['address_norm'] = (
        stalls_full['address']
        .fillna('')
        .str.lower()
        .str.strip()
        .str.replace(r'[^a-z0-9 ]', '', regex=True)
    )

    exclude = [ ## exclude these stopwords
        "dbs", "atm", "posb", "axs", "polyclinic", "electronic",
        "provision", "trading", "tailoring", "clothing", "wear",
        "bicycle", "florist", "ware", "swim", "sports", "apparel",
        "nhg", "flower", "ntuc", "gym", "kampung", "925", "silver",
        "gold", "money", "department", "watch", "jewel", "hdb",
        "nkf", "tuition", "library", "fitness", "fairprice",
        "supermarket", "mart", "singtel", "hair", "shoe",
        "furniture", "recycling", "phone", "fashion", "post",
        "aquarium", "tcm"
    ]

    pattern = "|".join(map(re.escape, exclude))

    mask_name = ~stalls_full['name_norm'].str.contains(pattern, na=False)
    keep_mask = mask_name
    stalls_to_include = stalls_full[keep_mask].reset_index(drop=True)
    stalls_to_exclude = stalls_full[~keep_mask].reset_index(drop=True)
    stalls_included = stalls_included.drop(columns=['address_norm', 'name_norm'])
    return stalls_to_include


def transform_reviews(reviews_full): ## surface level reviews transformation since more transformation will be done in downstream apps
    def clean_text(text):
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002700-\U000027BF"  # Dingbats
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U00002600-\U000026FF"  # Misc symbols
            "\U00002B50"             
            "\U000024C2-\U0001F251"  # Enclosed characters
            "]+", flags=re.UNICODE)
        new_text = emoji_pattern.sub(r'', text)
        result = new_text.replace('\n', ' ').replace('\r', ' ')
        return result

    reviews_full = reviews_full.dropna(subset=['rating'])
    reviews_full['cleaned_text'] = reviews_full['review_text'].astype(str).apply(clean_text)
    reviews_full = reviews_full.drop(columns=['review_text'], errors='ignore')
    reviews_full = reviews_full.rename(columns={'cleaned_text': 'review_text'})
    return reviews_full