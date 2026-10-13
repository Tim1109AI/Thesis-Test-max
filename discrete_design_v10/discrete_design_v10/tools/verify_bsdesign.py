"""Checks that code/bsdesign.py gives the same designs as the prototype bsd.dq / bsd.dq_1 (with which the Q = 5 screen
and the Q = 5 benchmark check of DQ were run) on every configuration of the screen, confirm, bench and smax tiers.
python3 tools/verify_bsdesign.py"""
import sys, os, numpy as np
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PKG, 'code')); sys.path.insert(0, os.path.join(PKG, 'harness'))
import scenarios as SC, bsd, bsdesign as BD, grid as G, discrete as DC

def same(a, b):
    ok = (a.groups == b.groups and list(a.served) == list(b.served) and list(a.core) == list(b.core)
          and list(a.priority) == list(b.priority))
    ma, mb = getattr(a, 'bsmask', None), getattr(b, 'bsmask', None)
    ok = ok and ((ma is None and mb is None) or (ma is not None and mb is not None and np.array_equal(ma, mb)))
    ok = ok and getattr(a, 'bs_sets', None) == getattr(b, 'bs_sets', None)
    return ok

cfgs = []
for sc in ('T2', 'E3'):
    for st in G.SETTINGS:
        for dr in range(901, 905):
            for R in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5):
                cfgs.append(dict(G.SETTINGS[st], setting=st, Rth=R, drop=dr, scenario=sc))
cfgs += [dict(c) for c in G.BENCH] + [dict(c) for c in G.SMAX]
n = 0
for c in cfgs:
    c.update(Dmax=10.0, L=3, Pmax=1.0)
    p, net = SC.network(c)
    for f_old, f_new in ((bsd.dq, BD.design), (bsd.dq_1, BD.design_1layer)):
        a, b = f_old(net, p), f_new(net, p)
        DC.check(b, p)
        assert same(a, b), (c, f_old.__name__)
        n += 1
print('identical designs:', n)
