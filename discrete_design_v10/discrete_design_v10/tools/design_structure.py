"""The structure of the design (code/bsdesign.py) in the test grid (drops 901-904, R_th 0, 1, 2): DESIGN.md section 1.8.
python3 tools/design_structure.py"""
import sys, os, numpy as np
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PKG, 'code')); sys.path.insert(0, os.path.join(PKG, 'harness'))
import scenarios as SC, hrs as H_, bsdesign as BD, grid as G
print('| scen | set | N | K | BN | S_max | core users | groups | group-commons served | streams (1-layer) | BS-specific | cores carried by all BSs |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|')
for sc in ('T2', 'E3'):
    for st in G.SETTINGS:
        nc, ng, ngs, ns, ns1, bsx, jt = [], [], [], [], [], [], []
        for dr in range(901, 905):
            for R in (0.0, 1.0, 2.0):
                cfg = dict(G.SETTINGS[st], setting=st, Rth=R, drop=dr, scenario=sc, Dmax=10.0, L=3, Pmax=1.0)
                p, net = SC.network(cfg)
                d = BD.design(net, p); d1 = BD.design_1layer(net, p)
                nc.append(len(d.core)); ng.append(d.G); ngs.append(sum(1 for j in d.served if 1 <= j <= d.G))
                ns.append(d.nS); ns1.append(d1.nS); bsx.append(d.bsmask is not None)
                m = d.bsmask if d.bsmask is not None else np.ones((p['B'], d.nS), bool)
                cs = [k for k in d.core if (1 + d.G + k) in d.col]
                jt.append(np.mean([m[:, d.col[1 + d.G + k]].all() for k in cs]) if cs else 0)
        s = G.SETTINGS[st]
        f = lambda v: f'{min(v)}–{max(v)}' if min(v) != max(v) else f'{min(v)}'
        print(f"| {sc} | {st} | {s['N']} | {s['K']} | {p['BN']} | {s['Smax']} | {f(nc)} | {f(ng)} | {f(ngs)} | {np.mean(ns):.1f} ({np.mean(ns1):.1f}) | {sum(bsx)}/{len(bsx)} | {100*np.mean(jt):.0f}% |")
