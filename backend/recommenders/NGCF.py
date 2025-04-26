import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset, DataLoader
from typing import Tuple


class NGCFRecommender:

    def __init__(
        self,
        embedding_dim: int = 64,
        layers: list = [64, 64],
        lr: float = 1e-3,
        epochs: int = 40,
        device: str = None
    ):
        self.embedding_dim = embedding_dim
        self.layers = layers
        self.lr = lr
        self.epochs = epochs
        self.device = torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))

    class _NGCFModel(nn.Module):
        def __init__(self, n_users: int, n_items: int, emb_dim: int, layers: list):
            super().__init__()
            self.total = n_users + n_items
            self.embedding = nn.Embedding(self.total, emb_dim)
            self.linears = nn.ModuleList()
            in_dim = emb_dim
            for out_dim in layers:
                self.linears.append(nn.Linear(in_dim, out_dim))
                in_dim = out_dim
            self.act = nn.LeakyReLU()

        def propagate(self, edge_index: torch.LongTensor):
            src, dst = edge_index
            emb = self.embedding.weight
            deg = torch.bincount(dst, minlength=self.total).float().unsqueeze(1)
            norm = deg.pow(-0.5)
            norm[torch.isinf(norm)] = 0.0
            msgs = emb[src] * norm[src]
            agg = torch.zeros_like(emb).index_add_(0, dst, msgs)
            return agg * norm

        def forward(self, edge_index: torch.LongTensor) -> torch.Tensor:
            all_emb = self.embedding.weight
            embs = [all_emb]
            for layer in self.linears:
                agg = self.propagate(edge_index)
                side = layer(agg)
                all_emb = self.act(side + layer(all_emb))
                embs.append(all_emb)
            return torch.stack(embs, dim=0).mean(dim=0)

    def run(
        self,
        stalls: pd.DataFrame,
        interactions: pd.DataFrame,
        min_rating: int = 4,
        min_interactions: int = 10
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        
        # rename and filter
        interactions = interactions.rename(columns={'place_id': 'stall_id'})
        interactions = interactions[interactions['rating'] >= min_rating]
        interactions = interactions[interactions['stall_id'].isin(stalls['stall_id'])]

        # eligible users
        counts = interactions['author'].value_counts()
        eligible = counts[counts >= min_interactions].index.tolist()
        interactions = interactions[interactions['author'].isin(eligible)]

        # temporal split
        train_parts, test_sets = [], {}
        for user, grp in interactions.groupby('author'):
            grp = grp.sort_values('ts').reset_index(drop=True)
            half = len(grp) // 2
            train_parts.append(grp.iloc[:half])
            test_sets[user] = set(grp.iloc[half:]['stall_id'])
        train_df = pd.concat(train_parts, ignore_index=True)

        # label encode
        uenc = LabelEncoder().fit(train_df['author'])
        ienc = LabelEncoder().fit(interactions['stall_id'])
        train_df['uid'] = uenc.transform(train_df['author'])
        train_df['iid'] = ienc.transform(train_df['stall_id'])
        n_users = len(uenc.classes_)
        n_items = len(ienc.classes_)

        # build bipartite graph edges
        u_idx = train_df['uid'].values
        i_idx = train_df['iid'].values + n_users
        edges = np.vstack([np.concatenate([u_idx, i_idx]),
                           np.concatenate([i_idx, u_idx])])
        edge_index = torch.LongTensor(edges)

        # instantiate model and optimizer
        model = self._NGCFModel(n_users, n_items, self.embedding_dim, self.layers).to(self.device)
        optimizer = optim.Adam(model.parameters(), lr=self.lr)

        # BPR loss
        def bpr_loss(pos, neg):
            return -torch.log(torch.sigmoid(pos - neg) + 1e-8).mean()

        # training loop
        model.train()
        pairs = list(zip(train_df['uid'], train_df['iid']))
        for _ in range(self.epochs):
            np.random.shuffle(pairs)
            for u, pos_i in pairs:
                neg_i = np.random.randint(n_items)
                while (u, neg_i) in pairs:
                    neg_i = np.random.randint(n_items)
                optimizer.zero_grad()
                emb = model(edge_index.to(self.device))
                u_emb = emb[u].unsqueeze(0)
                pos_emb = emb[n_users + pos_i].unsqueeze(0)
                neg_emb = emb[n_users + neg_i].unsqueeze(0)
                loss = bpr_loss((u_emb * pos_emb).sum(1), (u_emb * neg_emb).sum(1))
                loss.backward()
                optimizer.step()

        # extract final embeddings
        model.eval()
        with torch.no_grad():
            all_embs = model(edge_index.to(self.device)).cpu().numpy()
        user_embs = all_embs[:n_users]
        item_embs = all_embs[n_users:]

        # evaluation
        pool_sizes = [50, 100, 200, 500, 1000, 2000, n_items]
        ks = [1, 2, 3, 5]
        metrics = {ps: {k: {'hit': [], 'precision': [], 'recall': [], 'f1': []}
                        for k in ks} for ps in pool_sizes}

        for user in eligible:
            uid = uenc.transform([user])[0]
            test_i = [ienc.transform([pid])[0]
                      for pid in test_sets[user] if pid in ienc.classes_]
            if not test_i:
                continue
            seen = set(train_df[train_df['uid'] == uid]['iid'])
            neg_pool = list(set(range(n_items)) - seen - set(test_i))

            for ps in pool_sizes:
                # sampling guard
                neg_needed = min(max(0, ps - len(test_i)), len(neg_pool))
                sampled_neg = (np.random.choice(neg_pool, neg_needed, replace=False).tolist()
                               if neg_needed > 0 else [])
                candidates = test_i + sampled_neg

                scores = item_embs[candidates].dot(user_embs[uid])
                ranked = np.array(candidates)[np.argsort(scores)[::-1]]

                for k in ks:
                    rec_k = ranked[:k]
                    tp = sum(i in test_i for i in rec_k)
                    prec = tp / k
                    rec = tp / len(test_i)
                    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
                    hit = tp > 0
                    m = metrics[ps][k]
                    m['hit'].append(hit)
                    m['precision'].append(prec)
                    m['recall'].append(rec)
                    m['f1'].append(f1)

        # aggregate to DataFrames
        hr_rows, mr_rows = [], []
        for ps, data in metrics.items():
            hr = {'pool_size': ps}
            mr = {'pool_size': ps}
            for k in ks:
                hr[f'HitRate@{k}'] = np.mean(data[k]['hit'])
                mr[f'Precision@{k}'] = np.mean(data[k]['precision'])
                mr[f'Recall@{k}'] = np.mean(data[k]['recall'])
                mr[f'F1@{k}'] = np.mean(data[k]['f1'])
            hr_rows.append(hr)
            mr_rows.append(mr)

        hitrate_df = pd.DataFrame(hr_rows)
        metric_df = pd.DataFrame(mr_rows)
        return hitrate_df, metric_df


if __name__ == "__main__":

    from pymongo import MongoClient
    import re
    client = MongoClient("mongodb+srv://db_user:db_user123@cluster0.4e885.mongodb.net/?")
    db = client["IS3107-GROUP11"]

    stalls = pd.DataFrame(list(db.hawker_stall.find())).reset_index(drop=True)
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

    mask_name = ~stalls['name_norm'].str.contains(pattern, na=False)
    keep_mask = mask_name
    stalls = stalls[keep_mask].reset_index(drop=True)
    stalls = stalls.dropna(subset=['rating']).reset_index(drop=True)
    stalls['rating'] = stalls['rating'].astype(float)
    interactions = pd.DataFrame(list(db.reviews.find())).reset_index(drop=True)

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

    interactions['ts'] = interactions['relative_time'].apply(parse_rt)

    # Create and run
    recommender = NGCFRecommender()
    hitrate_df, metric_df = recommender.run(stalls, interactions)

    print("HitRate Table:")
    print(hitrate_df)

    print("\nMetrics Table:")
    print(metric_df)

    hitrate_df.to_csv("ngcf_hitrate_results.csv", index=False)
    metric_df.to_csv("ngcf_metrics_results.csv", index=False)

    print("\nResults saved as 'ngcf_hitrate_results.csv' and 'ngcf_metrics_results.csv'.")