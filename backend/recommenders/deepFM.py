import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from torch.utils.data import Dataset, DataLoader
from typing import Tuple

class DeepFMRecommender:

    def __init__(
        self,
        embedding_dim: int = 10,
        hidden_dims: list = [64, 32],
        lr: float = 1e-3,
        weight_decay: float = 1e-5,
        epochs: int = 1000,
        batch_size: int = 1024,
        device: str = None
    ):
        self.embedding_dim = embedding_dim
        self.hidden_dims = hidden_dims
        self.lr = lr
        self.weight_decay = weight_decay
        self.epochs = epochs
        self.batch_size = batch_size
        self.device = torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))

    class _DeepFMModel(nn.Module):
        def __init__(self, n_users, n_items, n_side, k, hidden_dims):
            super().__init__()
            self.user_emb = nn.Embedding(n_users, k)
            self.item_emb = nn.Embedding(n_items, k)
            self.user_lin = nn.Embedding(n_users, 1)
            self.item_lin = nn.Embedding(n_items, 1)
            self.side_lin = nn.Linear(n_side, 1)
            layers = []
            input_dim = 2 * k + n_side
            for h in hidden_dims:
                layers += [nn.Linear(input_dim, h), nn.ReLU(), nn.Dropout(0.2)]
                input_dim = h
            layers.append(nn.Linear(input_dim, 1))
            self.mlp = nn.Sequential(*layers)

        def forward(self, u, i, side):
            u_vec = self.user_emb(u)
            i_vec = self.item_emb(i)
            fm_term = ((u_vec + i_vec)**2 - u_vec**2 - i_vec**2).sum(1, keepdim=True)
            linear_term = self.user_lin(u) + self.item_lin(i) + self.side_lin(side)
            x = torch.cat([u_vec, i_vec, side], dim=1)
            return linear_term + fm_term + self.mlp(x)

    def run(
        self,
        stalls: pd.DataFrame,
        interactions: pd.DataFrame,
        min_rating: int = 4,
        min_interactions: int = 10
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        
        # prepare identifiers
        interactions = interactions.rename(columns={'place_id': 'stall_id'})

        # filter by rating
        interactions = interactions[interactions['rating'] >= min_rating].reset_index(drop=True)
        interactions = interactions[interactions['stall_id'].isin(stalls['stall_id'])].reset_index(drop=True)

        # require sufficient interactions per user
        counts = interactions['author'].value_counts()
        eligible = counts[counts >= min_interactions].index.tolist()
        interactions = interactions[interactions['author'].isin(eligible)].reset_index(drop=True)

        # temporal split per user
        train_parts, test_data = [], {}
        for user, grp in interactions.groupby('author'):
            grp = grp.sort_values('ts').reset_index(drop=True)
            half = len(grp) // 2
            train_parts.append(grp.iloc[:half])
            test_data[user] = grp.iloc[half:].reset_index(drop=True)
        train_df = pd.concat(train_parts, ignore_index=True)

        # label encoding
        uenc = LabelEncoder().fit(train_df['author'])
        ienc = LabelEncoder().fit(interactions['stall_id'])
        train_df['uid'] = uenc.transform(train_df['author'])
        train_df['iid'] = ienc.transform(train_df['stall_id'])
        n_users = len(uenc.classes_)
        n_items = len(ienc.classes_)

        # side features
        stalls = stalls.fillna({'business_status': 'unknown'})
        ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        cat = ohe.fit_transform(stalls[['business_status']])
        tfidf = TfidfVectorizer(max_features=100)
        text = stalls['name_norm'].fillna('') + ' ' + stalls['address_norm'].fillna('')
        txt_feats = tfidf.fit_transform(text).toarray()
        side_matrix = np.hstack([cat, txt_feats])

        item_side = np.zeros((n_items, side_matrix.shape[1]))
        for idx, pid in enumerate(ienc.classes_):
            loc = stalls.index[stalls['stall_id'] == pid]
            if len(loc):
                item_side[idx] = side_matrix[loc[0]]

        # build training pairs
        def gen_pairs(df):
            pos = df[['uid','iid']].values.tolist()
            neg = []
            for u, i in pos:
                choices = np.setdiff1d(np.arange(n_items), df[df['uid']==u]['iid'].unique())
                neg_i = np.random.choice(choices, 1)[0]
                neg.append([u, neg_i])
            return list(zip(pos, neg))

        pairs = gen_pairs(train_df)
        class BPRDataset(Dataset):
            def __init__(self, pairs): self.pairs = pairs
            def __len__(self): return len(self.pairs)
            def __getitem__(self, idx):
                (u, pos), (_, neg) = self.pairs[idx]
                return u, pos, neg

        loader = DataLoader(BPRDataset(pairs), batch_size=self.batch_size, shuffle=True)

        # initialise model
        model = self._DeepFMModel(n_users, n_items, item_side.shape[1],
                                  self.embedding_dim, self.hidden_dims).to(self.device)
        optimizer = optim.Adam(model.parameters(), lr=self.lr, weight_decay=self.weight_decay)

        # BPR loss
        def bpr_loss(pos, neg): return -torch.log(torch.sigmoid(pos - neg)).mean()

        # train
        for _ in range(self.epochs):
            model.train()
            for u_b, p_b, n_b in loader:
                u_b, p_b, n_b = map(lambda x: x.to(self.device), (u_b, p_b, n_b))
                side_p = torch.tensor(item_side[p_b.cpu().numpy()],
                                      dtype=torch.float32, device=self.device)
                side_n = torch.tensor(item_side[n_b.cpu().numpy()],
                                      dtype=torch.float32, device=self.device)
                optimizer.zero_grad()
                pos_s = model(u_b, p_b, side_p).squeeze()
                neg_s = model(u_b, n_b, side_n).squeeze()
                loss = bpr_loss(pos_s, neg_s)
                loss.backward()
                optimizer.step()

        # evaluation
        side_tensor = torch.tensor(item_side, dtype=torch.float32, device=self.device)
        all_items = np.arange(n_items)
        ks = [1,2,3,5]
        pools = [50,100,200,500,1000,2000,n_items]
        metrics = {ps: {k: {'hit':[], 'precision':[], 'recall':[], 'f1':[]} for k in ks} for ps in pools}

        for user in eligible:
            uid = uenc.transform([user])[0]
            seen = set(train_df[train_df['uid']==uid]['iid'])
            test_i = [int(ienc.transform([pid])[0]) for pid in test_data[user]['stall_id'] if pid in ienc.classes_]
            if not test_i: continue

            reps = torch.full((n_items,), uid, dtype=torch.long, device=self.device)
            with torch.no_grad():
                scores = model(reps, torch.tensor(all_items, device=self.device), side_tensor).squeeze().cpu().numpy()
            scores[list(seen)] = -np.inf

            for ps in pools:
                neg_pool = list(set(all_items) - seen - set(test_i))
                neg_needed = min(max(0, ps - len(test_i)), len(neg_pool))
                sampled_neg = (
                    np.random.choice(neg_pool, size=neg_needed, replace=False).tolist()
                    if neg_needed > 0 else []
                )
                candidates = test_i + sampled_neg

                ranked = sorted(candidates, key=lambda i: scores[i], reverse=True)

                for k in ks:
                    rec_k = ranked[:k]
                    tp = sum(i in test_i for i in rec_k)
                    prec = tp/k
                    rec_ = tp/len(test_i)
                    f1 = 2*prec*rec_/(prec+rec_) if prec+rec_>0 else 0.0
                    hit = tp>0
                    m = metrics[ps][k]
                    m['hit'].append(hit)
                    m['precision'].append(prec)
                    m['recall'].append(rec_)
                    m['f1'].append(f1)

        # aggregate
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
