"""Behaviour of the design (code/bsdesign.py) on networks that are not in the grid: many BSs scattered over a large area
(design only, no AO; the direct channels of hrs.make_network for arbitrary BS / UE positions).  python3 tools/large_area.py"""
import sys, os, numpy as np
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PKG, 'code'))
import hrs as H_, run as R, bsdesign as BD, discrete as DC

import math
def direct(p, BS, UE):
    """The direct channels of hrs.make_network for arbitrary BS / UE positions."""
    K, B, N = len(UE), len(BS), p['N']
    k0 = 2 * math.pi / p['lam']
    Hd = np.zeros((K, B * N), complex)
    for k in range(K):
        for b in range(B):
            v = UE[k] - BS[b]; d = np.linalg.norm(v)
            a = np.exp(1j * k0 * p['uBS'] @ (v / d))
            Hd[k, b * N:(b + 1) * N] = math.sqrt(p['PL0'] / p['noise']) * d ** (-p['alpha'] / 2) * np.exp(-1j * k0 * d) * a
    return Hd

def demo(name, BS, K, N, Smax, Rth, side, seed):
    rng = np.random.default_rng(seed)
    B = len(BS)
    UE = np.column_stack([rng.uniform(0, side, K), rng.uniform(0, side, K), np.full(K, 1.5)])
    p = H_.params(K=K, N=N, M=100, Smax=Smax, Rth=Rth, bank=R.BANK, B=B)
    net = dict(BS=np.array(BS, float), UE=UE, Hd=direct(p, np.array(BS, float), UE))
    d = BD.design(net, p); DC.check(d, p)
    G = d.G
    mask = d.bsmask if d.bsmask is not None else np.ones((B, d.nS), bool)
    dist = np.linalg.norm(UE[:, None, :2] - np.array(BS)[None, :, :2], axis=2)
    core = d.core
    nb = [int(mask[:, d.col[1 + G + k]].sum()) if (1 + G + k) in d.col else 0 for k in core]
    # rank (1 = nearest) of the carrying BSs of each core user
    ranks = []
    for k in core:
        if (1 + G + k) not in d.col: continue
        order = np.argsort(dist[k]); carriers = np.where(mask[:, d.col[1 + G + k]])[0]
        ranks += [int(np.where(order == b)[0][0]) + 1 for b in carriers]
    gc = [int(mask[:, d.col[1 + g]].sum()) for g in range(G) if (1 + g) in d.col]
    print(f'{name}: B={B} K={K} N={N} S_max={Smax} R_th={Rth}: |C|={len(core)} groups={G} served streams={d.nS} '
          f'BS-specific={d.bsmask is not None}')
    print(f'   BSs per core private: {np.bincount(nb, minlength=B + 1)[1:].tolist()} (count of cores carried by 1..B BSs; '
          f'{nb.count(0)} not carried)')
    if ranks: print(f'   distance rank of the carrying BSs (1 = nearest): {np.bincount(ranks, minlength=B + 1)[1:].tolist()}')
    if gc: print(f'   BSs per served group-common: {gc}')

bank_side = 100
demo('T2 layout, S_max = 12', [[25, 50, 15], [75, 50, 15]], 16, 3, 12, 2.0, 100, 1)
demo('T2 layout, S_max = 4', [[25, 50, 15], [75, 50, 15]], 16, 3, 4, 2.0, 100, 1)
g = [[x, y, 15] for x in (100, 300, 500) for y in (100, 300, 500)]
for S in (4, 7, 13, 28):
    demo(f'9 BSs on a 600 m grid, S_max = {S}', g, 36, 3, S, 1.0, 600, 2)
g16 = [[x, y, 15] for x in (125, 375, 625, 875) for y in (125, 375, 625, 875)]
demo('16 BSs on a 1 km grid, S_max = 7', g16, 64, 3, 7, 1.0, 1000, 3)
demo('4 BSs within 40 m (dense), S_max = 13', [[40, 40, 15], [60, 40, 15], [40, 60, 15], [60, 60, 15]], 12, 3, 13, 1.0, 100, 4)
