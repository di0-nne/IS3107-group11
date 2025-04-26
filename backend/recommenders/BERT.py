# import re
# import pandas as pd
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity
# from pymongo import MongoClient

# class BERTRecommender:
#     def __init__(self, mongo_uri, db_name, stall_collection, review_collection):
#         self.client = MongoClient(mongo_uri)
#         self.db = self.client[db_name]
#         self.stall_collection = stall_collection
#         self.review_collection = review_collection
#         self.model = SentenceTransformer('all-MiniLM-L6-v2')

#     def preprocess_stalls(self):
#         stalls = pd.DataFrame(list(self.db[self.stall_collection].find())).reset_index(drop=True)
        
#         stalls['name_norm'] = (
#             stalls['name']
#             .fillna('')
#             .str.lower()
#             .str.strip()
#             .str.replace(r'[^a-z0-9 ]', '', regex=True)
#         )
#         stalls['address_norm'] = (
#             stalls['address']
#             .fillna('')
#             .str.lower()
#             .str.strip()
#             .str.replace(r'[^a-z0-9 ]', '', regex=True)
#         )
        
#         exclude = [
#             "dbs", "atm", "posb", "axs", "polyclinic", "electronic",
#             "provision", "trading", "tailoring", "clothing", "wear",
#             "bicycle", "florist", "ware", "swim", "sports", "apparel",
#             "nhg", "flower", "ntuc", "gym", "kampung", "925", "silver",
#             "gold", "money", "department", "watch", "jewel", "hdb",
#             "nkf", "tuition", "library", "fitness", "fairprice",
#             "supermarket", "mart", "singtel", "hair", "shoe",
#             "furniture", "recycling", "phone", "fashion", "post",
#             "aquarium", "tcm"
#         ]
#         pattern = "|".join(map(re.escape, exclude))

#         stalls = stalls[~stalls['name_norm'].str.contains(pattern, na=False)].reset_index(drop=True)
#         stalls = stalls.dropna(subset=['rating']).reset_index(drop=True)
#         stalls['rating'] = stalls['rating'].astype(float)
        
#         return stalls

#     def preprocess_interactions(self, stalls):
#         interactions = pd.DataFrame(list(self.db[self.review_collection].find())).reset_index(drop=True)
#         interactions = interactions[interactions['rating'] >= 4].reset_index(drop=True)
#         interactions = interactions[interactions['stall_id'].isin(stalls['stall_id'])].reset_index(drop=True)

#         counts = interactions['author'].value_counts()
#         eligible = counts[counts >= 10].index.tolist()
#         interactions = interactions[interactions['author'].isin(eligible)].reset_index(drop=True)
        
#         return interactions, eligible

#     def prepare_data(self, interactions, stalls):
#         train_parts, test_data = [], {}
#         for author, grp in interactions.groupby('author'):
#             grp_shuf = grp.sample(frac=1, random_state=42).reset_index(drop=True)
#             half = len(grp_shuf) // 2
#             train_parts.append(grp_shuf.iloc[:half])
#             test_data[author] = grp_shuf.iloc[half:].reset_index(drop=True)
#         train_df = pd.concat(train_parts, ignore_index=True)

#         train_df['review_clean'] = (
#             train_df['review_text']
#             .fillna('')
#             .str.lower()
#             .str.replace(r'[^a-z0-9 ]', ' ', regex=True)
#             .str.strip()
#         )

#         stall_docs = (
#             interactions
#             .groupby('stall_id')['review_text']
#             .apply(lambda texts: ' '.join(texts))
#             .rename('all_reviews')
#             .reset_index()
#             .merge(stalls, on='stall_id', how='inner')
#         )
#         stall_docs['all_reviews'] = stall_docs['all_reviews'].fillna('').astype(str)
#         stall_docs['doc'] = (
#             stall_docs['name_norm'] + '. ' +
#             stall_docs['address_norm'] + '. ' +
#             stall_docs['all_reviews']
#         )
#         stall_docs['doc'] = stall_docs['doc'].astype(str)

#         return train_df, test_data, stall_docs

#     def run(self):
#         stalls = self.preprocess_stalls()
#         interactions, eligible = self.preprocess_interactions(stalls)
#         train_df, test_data, stall_docs = self.prepare_data(interactions, stalls)

#         stall_embs = self.model.encode(
#             stall_docs['doc'].tolist(),
#             convert_to_numpy=True
#         )
#         pid_to_idx = {pid: idx for idx, pid in enumerate(stall_docs['stall_id'])}
#         max_pool = len(stall_embs)

#         fixed_pool_sizes = [50, 100, 200, 500, 1000, 2000]
#         pool_sizes = fixed_pool_sizes + [max_pool]
#         ks = [1, 2, 3, 5]

#         metrics_by_pool = {
#             ps: {k: {'hit': [], 'precision': [], 'recall': [], 'f1': []} for k in ks}
#             for ps in pool_sizes
#         }

#         for author in eligible:
#             hist = train_df[train_df['author'] == author]
#             if hist.empty:
#                 continue

#             emb = self.model.encode(hist['review_clean'].tolist(), convert_to_numpy=True)
#             profile = emb.mean(axis=0, keepdims=True)
#             sims = cosine_similarity(profile, stall_embs)[0]

#             test_pids = test_data[author]['stall_id'].tolist()
#             test_idxs = [pid_to_idx[p] for p in test_pids if p in pid_to_idx]
#             if not test_idxs:
#                 continue

#             seen_idxs = {pid_to_idx[p] for p in hist['stall_id'] if p in pid_to_idx}
#             all_idxs = set(range(max_pool))
#             neg_pool = list(all_idxs - seen_idxs - set(test_idxs))

#             for ps in pool_sizes:
#                 neg_needed = ps - len(test_idxs)
#                 if neg_needed > 0:
#                     neg_needed = min(neg_needed, len(neg_pool))
#                     sampled_neg = np.random.choice(neg_pool, size=neg_needed, replace=False).tolist()
#                     candidates = test_idxs + sampled_neg
#                 else:
#                     candidates = test_idxs.copy()

#                 ranked = sorted(candidates, key=lambda i: sims[i], reverse=True)

#                 for k in ks:
#                     rec_k = ranked[:k]
#                     tp = sum(1 for i in rec_k if i in test_idxs)
#                     prec = tp / k
#                     rec = tp / len(test_idxs)
#                     f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
#                     hit = tp > 0

#                     m = metrics_by_pool[ps][k]
#                     m['hit'].append(hit)
#                     m['precision'].append(prec)
#                     m['recall'].append(rec)
#                     m['f1'].append(f1)

#         hitrate_rows, metrics_rows = [], []
#         for ps, data in metrics_by_pool.items():
#             hr = {'pool_size': ps}
#             mr = {'pool_size': ps}
#             for k in ks:
#                 hr[f'HitRate@{k}'] = np.mean(data[k]['hit'])
#                 mr[f'Precision@{k}'] = np.mean(data[k]['precision'])
#                 mr[f'Recall@{k}'] = np.mean(data[k]['recall'])
#                 mr[f'F1@{k}'] = np.mean(data[k]['f1'])
#             hitrate_rows.append(hr)
#             metrics_rows.append(mr)

#         hitrate_df = pd.DataFrame(hitrate_rows)
#         metric_df = pd.DataFrame(metrics_rows)

#         return hitrate_df, metric_df

# if __name__ == "__main__":
#     recommender = BERTRecommender(
#         mongo_uri="mongodb+srv://db_user:db_user123@cluster0.4e885.mongodb.net/?",
#         db_name="IS3107-GROUP11",
#         stall_collection="hawker_stall",
#         review_collection="reviews"
#     )
    
#     hitrate_df, metric_df = recommender.run()

#     print("=== BERT HitRate@k ===")
#     print(hitrate_df)

#     print("\n=== BERT Precision@k, Recall@k, F1@k ===")
#     print(metric_df)
    
#     hitrate_df.to_csv("bert_hitrate_results.csv", index=False)
#     metric_df.to_csv("bert_metrics_results.csv", index=False)

#     print("\nResults saved as 'bert_hitrate_results.csv' and 'bert_metrics_results.csv'.")

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Tuple

class BERTRecommender:

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def run(
        self,
        stalls: pd.DataFrame,
        interactions: pd.DataFrame,
        min_rating: int = 4,
        min_interactions: int = 10
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        
        # filter interactions by rating and available stalls
        interactions = interactions[interactions['rating'] >= min_rating].reset_index(drop=True)
        interactions = interactions[interactions['stall_id'].isin(stalls['stall_id'])].reset_index(drop=True)

        # keep only authors with enough interactions
        counts = interactions['author'].value_counts()
        eligible = counts[counts >= min_interactions].index.tolist()
        interactions = interactions[interactions['author'].isin(eligible)].reset_index(drop=True)

        # split each author's interactions into train/test
        train_parts, test_data = [], {}
        for author, grp in interactions.groupby('author'):
            grp_shuf = grp.sample(frac=1, random_state=42).reset_index(drop=True)
            half = len(grp_shuf) // 2
            train_parts.append(grp_shuf.iloc[:half])
            test_data[author] = grp_shuf.iloc[half:].reset_index(drop=True)
        train_df = pd.concat(train_parts, ignore_index=True)

        # clean review text for embedding
        train_df['review_clean'] = (
            train_df['review_text']
            .fillna('')
            .str.lower()
            .str.replace(r'[^a-z0-9 ]', ' ', regex=True)
            .str.strip()
        )

        # build one document per stall
        stall_docs = (
            interactions
            .groupby('stall_id')['review_text']
            .apply(lambda texts: ' '.join(texts))
            .rename('all_reviews')
            .reset_index()
            .merge(stalls, on='stall_id', how='inner')
        )
        stall_docs['all_reviews'] = stall_docs['all_reviews'].fillna('').astype(str)
        stall_docs['doc'] = (
            stall_docs['name_norm'].fillna('') + '. ' +
            stall_docs['address_norm'].fillna('') + '. ' +
            stall_docs['all_reviews']
        )

        # encode stall documents once
        stall_embs = self.model.encode(
            stall_docs['doc'].tolist(),
            convert_to_numpy=True
        )
        pid_to_idx = {pid: idx for idx, pid in enumerate(stall_docs['stall_id'])}
        max_pool = len(stall_embs)

        # define evaluation settings
        fixed_pool_sizes = [50, 100, 200, 500, 1000, 2000]
        pool_sizes = fixed_pool_sizes + [max_pool]
        ks = [1, 2, 3, 5]

        # prepare storage for metrics
        metrics_by_pool = {
            ps: {k: {'hit': [], 'precision': [], 'recall': [], 'f1': []} for k in ks}
            for ps in pool_sizes
        }

        # evaluate per user
        for author in eligible:
            hist = train_df[train_df['author'] == author]
            if hist.empty:
                continue

            emb = self.model.encode(hist['review_clean'].tolist(), convert_to_numpy=True)
            profile = emb.mean(axis=0, keepdims=True)
            sims = cosine_similarity(profile, stall_embs)[0]

            test_pids = test_data[author]['stall_id'].tolist()
            test_idxs = [pid_to_idx[p] for p in test_pids if p in pid_to_idx]
            if not test_idxs:
                continue

            seen_idxs = {pid_to_idx[p] for p in hist['stall_id'] if p in pid_to_idx}
            neg_pool = list(set(range(max_pool)) - seen_idxs - set(test_idxs))

            for ps in pool_sizes:
                neg_needed = ps - len(test_idxs)
                if neg_needed > 0:
                    neg_needed = min(neg_needed, len(neg_pool))
                    sampled_neg = np.random.choice(neg_pool, size=neg_needed, replace=False).tolist()
                    candidates = test_idxs + sampled_neg
                else:
                    candidates = test_idxs.copy()

                ranked = sorted(candidates, key=lambda i: sims[i], reverse=True)

                for k in ks:
                    rec_k = ranked[:k]
                    tp = sum(i in test_idxs for i in rec_k)
                    prec = tp / k
                    rec = tp / len(test_idxs)
                    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
                    hit = tp > 0

                    m = metrics_by_pool[ps][k]
                    m['hit'].append(hit)
                    m['precision'].append(prec)
                    m['recall'].append(rec)
                    m['f1'].append(f1)

        # aggregate results
        hitrate_rows, metrics_rows = [], []
        for ps, data in metrics_by_pool.items():
            hr = {'pool_size': ps}
            mr = {'pool_size': ps}
            for k in ks:
                hr[f'HitRate@{k}'] = np.mean(data[k]['hit'])
                mr[f'Precision@{k}'] = np.mean(data[k]['precision'])
                mr[f'Recall@{k}'] = np.mean(data[k]['recall'])
                mr[f'F1@{k}'] = np.mean(data[k]['f1'])
            hitrate_rows.append(hr)
            metrics_rows.append(mr)

        hitrate_df = pd.DataFrame(hitrate_rows)
        metric_df = pd.DataFrame(metrics_rows)

        return hitrate_df, metric_df
