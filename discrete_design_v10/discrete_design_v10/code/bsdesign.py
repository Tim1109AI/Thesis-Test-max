"""Discrete design with BS-specific stream sets (design round v10): per-BS ranking of the HRS streams.

One central design, computed from the direct channels before the deployment search:

1. Core users. The UEs in the SUS order on the stacked direct channels (the greedy projection step of the current
   design) are kept while the next UE increases the zero-forcing sum rate with the total power B P_max split equally,
   and at least until the super-common stream could carry the QoS of the remaining UEs (R_th (K - n) <= C0, C0 the
   largest rate any stream can reach at the weakest UE); never more than min(K, BN).
2. Groups. Every other UE joins the core user with the most correlated direct channel; a core user with at least one
   follower heads a group (as the current design).
3. Stream sets. Every BS ranks the streams by its own direct channels: the super-common stream; the private streams of
   the core users (decreasing gain of the BS to the UE); the group-common streams (decreasing gain to the weakest
   member); the private streams of the other UEs (decreasing gain). BS b carries the first S_max streams of its list.

The 1-layer counterpart (design_1layer) uses the same lists without the group-common streams. Nothing depends on B = 2
or 3 or on the BS positions; the only inputs are the channels and the settings (B, N, K, S_max, P_max, R_th).
"""
import math
import numpy as np
import hrs as H_


def link_gains(Hd, B, N):
    """(K, B): ||h_{k,b}||^2, the direct-channel gain of BS b to UE k (noise-normalized)."""
    return np.stack([np.sum(np.abs(Hd[:, b * N:(b + 1) * N]) ** 2, axis=1) for b in range(B)], axis=1)


def zf_sum_rate(Hd, C, P):
    """Sum rate of zero-forcing to the UEs C on the stacked direct channels, the total power P split equally."""
    Hs = Hd[C]
    try:
        g = 1.0 / np.maximum(np.real(np.diag(np.linalg.inv(Hs @ Hs.conj().T))), 1e-300)
    except np.linalg.LinAlgError:          # linearly dependent channels: ZF cannot separate the UEs of C
        return -np.inf
    return float(np.sum(np.log2(1.0 + P / len(C) * g)))


def common_rate_bound(Hd, B, N, Pmax):
    """C0 = min_k log2(1 + P_max (sum_b ||h_{k,b}||)^2): no stream reaches UE k with a larger SNR than every BS
    beamforming its full power coherently to k, and the super-common stream must be decoded by every UE."""
    amp = sum(np.linalg.norm(Hd[:, b * N:(b + 1) * N], axis=1) for b in range(B))
    return float(np.min(np.log2(1.0 + Pmax * amp ** 2)))


def core_users(Hd, p):
    """Step 1: the SUS order, kept while the ZF sum rate increases, at least up to the QoS floor, at most min(K, BN)."""
    K, B, N = p['K'], p['B'], p['N']
    order = H_.sus(Hd, p['BN'])
    P = B * p['Pmax']
    n, best = 1, zf_sum_rate(Hd, order[:1], P)
    while n < len(order):
        r = zf_sum_rate(Hd, order[:n + 1], P)
        if r <= best:
            break
        n, best = n + 1, r
    C0 = common_rate_bound(Hd, B, N, p['Pmax'])
    while n < len(order) and p['Rth'] * (K - n) > C0:
        n += 1
    return order[:n]


def nearest_core_groups(Hd, core, K):
    """Step 2: every other UE joins the core user with the most correlated direct channel."""
    energy = np.sum(np.abs(Hd) ** 2, axis=1)
    Hn = Hd / np.sqrt(energy)[:, None]
    corr = np.abs(Hn @ Hn.conj().T) ** 2
    follow = {c: [] for c in core}
    for k in range(K):
        if k not in core:
            follow[core[int(np.argmax(corr[k, core]))]].append(k)
    # a group of every UE (one core user only) would duplicate the super-common stream: not formed
    return [[c] + follow[c] for c in core if follow[c] and len(follow[c]) < K - 1], energy


def bs_lists(core, groups, gain, K, B):
    """Step 3: BS b's ranking of the streams ('c' super-common, ('g', i) group i, ('p', k) private of UE k)."""
    others = [k for k in range(K) if k not in core]
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in sorted(core, key=lambda k: -gain[k, b])]
        l += [('g', i) for i in sorted(range(len(groups)), key=lambda i: -min(gain[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(others, key=lambda k: -gain[k, b])]
        lists.append(l)
    return lists


def assemble(lists, groups, core, energy, p, rule, one_layer):
    """hrs.Design of the lists: BS b carries the first S_max streams of its list (group-common streams removed in the
    1-layer counterpart); d.priority: a global order of every stream (super-common, core privates in SUS order,
    group-common streams by decreasing size, other privates by decreasing energy) for stream clustering."""
    K, B, S = p['K'], p['B'], p['Smax']
    grp = [] if one_layer else [list(m) for m in groups]
    G = len(grp)
    keep = lambda x: x == 'c' or not (one_layer and x[0] == 'g')
    gid = lambda x: 0 if x == 'c' else (1 + x[1] if x[0] == 'g' else 1 + G + x[1])
    sets = [[gid(x) for x in [y for y in lists[b] if keep(y)][:S]] for b in range(B)]
    served = sorted(set().union(*map(set, sets)))
    d = H_.Design(grp, served, K)
    d.core = list(core)
    d.rule = rule
    others = sorted([k for k in range(K) if k not in core], key=lambda k: (-energy[k], k))
    glob = (['c'] + [('p', k) for k in core]
            + [('g', i) for i in sorted(range(len(groups)), key=lambda i: (-len(groups[i]), i))]
            + [('p', k) for k in others])
    d.priority = [gid(x) for x in glob if keep(x)]
    mask = np.array([[j in sets[b] for j in d.served] for b in range(B)])
    if not mask.all():
        d.bsmask = mask
        d.bs_sets = [sorted(s) for s in sets]
    return d


def design(net, p, one_layer=False):
    """The discrete design (hrs.Design with d.bsmask / d.bs_sets when the BSs carry different streams)."""
    Hd, K, B, N = net['Hd'], p['K'], p['B'], p['N']
    core = core_users(Hd, p)
    groups, energy = nearest_core_groups(Hd, core, K)
    lists = bs_lists(core, groups, link_gains(Hd, B, N), K, B)
    return assemble(lists, groups, core, energy, p, 'bs_rank', one_layer)


def design_1layer(net, p):
    """Its 1-layer RSMA counterpart: the same lists without group-common streams."""
    return design(net, p, True)
