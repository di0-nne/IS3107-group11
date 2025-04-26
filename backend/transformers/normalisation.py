import re

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