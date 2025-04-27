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
        
