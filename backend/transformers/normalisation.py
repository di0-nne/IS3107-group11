import re
import pandas as pd

def normalise_stalls(stalls): ## raw stalls dataset
    stalls['name_norm'] = (
        stalls['name']
        .fillna('')
        .str.lower()
        .str.strip()
        .str.replace(r'[^a-z0-9 ]', '', regex=True)
    )

    stalls['address_norm'] = (
        stalls['address']
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

    stalls = stalls[~stalls['name_norm'].str.contains(pattern, na=False)].reset_index(drop=True)
    stalls = stalls.dropna(subset=['rating']).reset_index(drop=True)
    stalls['rating'] = stalls['rating'].astype(float)

    return stalls


def normalise_reviews(reviews):
    
    REF = pd.Timestamp('2025-04-27')
    
    def parse_rt(rt):
        if pd.isna(rt): 
            return REF
        num, unit, *_ = rt.split()
        n = 1 if num in ('a','an') else int(num)
        if 'year' in unit: return REF - pd.DateOffset(years=n)
        if 'month' in unit: return REF - pd.DateOffset(months=n)
        if 'day' in unit: return REF - pd.DateOffset(days=n)
        return REF

    reviews['ts'] = reviews['relative_time'].apply(parse_rt)

    return reviews
