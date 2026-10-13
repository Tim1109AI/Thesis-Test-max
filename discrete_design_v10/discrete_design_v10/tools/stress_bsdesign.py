"""Robustness of code/bsdesign.py on random networks (design only): random B (1-16), BS and UE positions over areas of
50 m to 2 km, K (1-48), N (1-8), S_max (1-40), R_th (0-4); every design and its 1-layer counterpart must pass
discrete.check (constraints of the problem and the super-common stream at every BS).  python3 tools/stress_bsdesign.py"""
import sys, os, math, numpy as np
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PKG, 'code'))
import hrs as H_, run as R, bsdesign as BD, discrete as DC


def direct(p, BS, UE):
    K, B, N = len(UE), len(BS), p['N']
    k0 = 2 * math.pi / p['lam']
    Hd = np.zeros((K, B * N), complex)
    for k in range(K):
        for b in range(B):
            v = UE[k] - BS[b]; d = np.linalg.norm(v)
            a = np.exp(1j * k0 * p['uBS'] @ (v / d))
            Hd[k, b * N:(b + 1) * N] = math.sqrt(p['PL0'] / p['noise']) * d ** (-p['alpha'] / 2) * np.exp(-1j * k0 * d) * a
    return Hd


rng = np.random.default_rng(2026)
n_ok, n_spec, n_jt, n_groups = 0, 0, 0, 0
for t in range(600):
    B, K, N = int(rng.integers(1, 17)), int(rng.integers(1, 49)), int(rng.integers(1, 9))
    S, Rth, side = int(rng.integers(1, 41)), float(rng.uniform(0, 4)), float(rng.choice([50, 100, 500, 2000]))
    BS = np.column_stack([rng.uniform(0, side, B), rng.uniform(0, side, B), np.full(B, 15.0)])
    UE = np.column_stack([rng.uniform(0, side, K), rng.uniform(0, side, K), np.full(K, 1.5)])
    if t % 50 == 0:                       # co-located UEs (identical channels)
        UE[1:] = UE[0]
    p = H_.params(K=K, N=N, M=100, Smax=S, Rth=Rth, bank=R.BANK, B=B)
    net = dict(BS=BS, UE=UE, Hd=direct(p, BS, UE))
    for f in (BD.design, BD.design_1layer):
        d = f(net, p)
        DC.check(d, p)
    n_ok += 1
    d = BD.design(net, p)
    n_spec += d.bsmask is not None; n_jt += d.bsmask is None; n_groups += d.G > 0
print(f'{n_ok} random networks: every design and 1-layer counterpart passes discrete.check; '
      f'BS-specific {n_spec}, joint {n_jt}, with groups {n_groups}')
