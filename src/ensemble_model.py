"""Model classes for the stacked ensemble (importable at unpickle time).

Members:
- LightGBM / XGBoost / CatBoost: Optuna-tuned gradient-boosted trees
- TabPFN-2.5: tabular foundation model (transformer, in-context learning) on GPU
- TorchMLP: seed-ensembled MLP on GPU (per "Better by Default", ensembled MLPs
  approach GBDT quality and add diversity to the blend)
Meta-learner: multinomial logistic regression over the members' probabilities
(blending), which also acts as a calibration layer.
"""
import numpy as np


class TorchMLP:
    """Seed-ensemble of small MLPs, sklearn-like interface."""

    def __init__(self, n_seeds=5, hidden=256, epochs=60, lr=1e-3, device=None):
        self.n_seeds, self.hidden, self.epochs, self.lr = n_seeds, hidden, epochs, lr
        self.device = device
        self.nets, self.mu, self.sd = [], None, None

    def _build(self, n_in, n_out, seed):
        import torch
        import torch.nn as nn
        torch.manual_seed(seed)
        return nn.Sequential(
            nn.Linear(n_in, self.hidden), nn.GELU(), nn.Dropout(0.25),
            nn.Linear(self.hidden, self.hidden), nn.GELU(), nn.Dropout(0.25),
            nn.Linear(self.hidden, n_out))

    def fit(self, X, y, X_val=None, y_val=None):
        import torch
        import torch.nn as nn
        dev = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        X = np.asarray(X, dtype=np.float32); y = np.asarray(y, dtype=np.int64)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-8
        Xt = torch.tensor((X - self.mu) / self.sd, device=dev)
        yt = torch.tensor(y, device=dev)
        has_val = X_val is not None
        if has_val:
            Xv = torch.tensor((np.asarray(X_val, dtype=np.float32) - self.mu) / self.sd, device=dev)
            yv = torch.tensor(np.asarray(y_val, dtype=np.int64), device=dev)
        n_out = int(y.max()) + 1
        self.nets = []
        for seed in range(self.n_seeds):
            net = self._build(X.shape[1], n_out, seed).to(dev)
            opt = torch.optim.AdamW(net.parameters(), lr=self.lr, weight_decay=1e-4)
            lossf = nn.CrossEntropyLoss()
            best, best_state, patience = 1e9, None, 0
            for ep in range(self.epochs):
                net.train()
                perm = torch.randperm(len(Xt), device=dev)
                for i in range(0, len(Xt), 1024):
                    idx = perm[i:i + 1024]
                    opt.zero_grad()
                    loss = lossf(net(Xt[idx]), yt[idx])
                    loss.backward(); opt.step()
                if has_val:
                    net.eval()
                    with torch.no_grad():
                        vl = lossf(net(Xv), yv).item()
                    if vl < best - 1e-4:
                        best, best_state, patience = vl, {k: v.clone() for k, v in net.state_dict().items()}, 0
                    else:
                        patience += 1
                        if patience >= 8:
                            break
            if best_state:
                net.load_state_dict(best_state)
            net.eval()
            self.nets.append(net.cpu())
        return self

    def predict_proba(self, X):
        import torch
        X = (np.asarray(X, dtype=np.float32) - self.mu) / self.sd
        Xt = torch.tensor(X)
        with torch.no_grad():
            ps = [torch.softmax(net(Xt), 1).numpy() for net in self.nets]
        return np.mean(ps, axis=0)


class StackEnsemble:
    """Blend of base classifiers; meta=None averages probabilities (preferred
    for few members), otherwise a logistic-regression meta-learner stacks them."""

    def __init__(self, members, meta=None):
        self.members = members          # dict name -> fitted model
        self.meta = meta                # None -> average; LR -> stacking

    def _probs(self, X):
        X = np.asarray(X, dtype=np.float32)
        return [m.predict_proba(X) for m in self.members.values()]

    def predict_proba(self, X):
        ps = self._probs(X)
        if self.meta is None:
            return np.mean(ps, axis=0)
        return self.meta.predict_proba(np.hstack(ps))

    def predict(self, X):
        return self.predict_proba(X).argmax(1)
