"""BS-specific discrete designs (design round v10): prototypes.

Every design here returns an hrs.Design whose BSs may carry different stream sets (d.bsmask), the super-common stream
at every BS. Stream keys while building: 'c' (super-common), ('g', i) (group-common stream of group i), ('p', k)
(private stream of UE k). BS b carries the first S_max keys of its own list.
"""
import math
import numpy as np
import hrs as H_


def link_gains(net, p):
    """(K, B): ||h_{d,k,b}||^2, the direct-channel gain of BS b to UE k (noise-normalized)."""
    Hd, N = net['Hd'], p['N']
    return np.stack([np.sum(np.abs(Hd[:, b * N:(b + 1) * N]) ** 2, axis=1) for b in range(p['B'])], axis=1)


def assemble(lists, groups, core, priority, p, rule, one_layer=False):
    """lists[b]: BS b's keys in its order of preference; BS b carries the first S_max of them (group keys removed for
    the 1-layer counterpart, their slots going to the next keys of the list). priority: a global order of all keys
    (for stream clustering on the design). Returns the hrs.Design (bsmask None when every BS carries every stream)."""
    K, B, S = p['K'], p['B'], p['Smax']
    grp = [] if one_layer else [list(m) for m in groups]
    G = len(grp)
    keep = lambda x: not (one_layer and x != 'c' and x[0] == 'g')

    def gid(x):
        return 0 if x == 'c' else (1 + x[1] if x[0] == 'g' else 1 + G + x[1])
    sets = [[gid(x) for x in [y for y in lists[b] if keep(y)][:S]] for b in range(B)]
    served = sorted(set().union(*map(set, sets)))
    d = H_.Design(grp, served, K)
    d.core = list(core); d.rule = rule
    d.priority = [gid(x) for x in priority if keep(x)]
    mask = np.array([[j in sets[b] for j in d.served] for b in range(B)])
    if not mask.all():
        d.bsmask = mask; d.bs_sets = [sorted(s) for s in sets]
    return d


def _global_order(order, groups, energy, K):
    sizes = [len(m) for m in groups]
    non = sorted([k for k in range(K) if k not in order], key=lambda k: (-energy[k], k))
    return (['c'] + [('p', k) for k in order] + [('g', i) for i in sorted(range(len(groups)), key=lambda i: (-sizes[i], i))]
            + [('p', k) for k in non])


# --------------------------------------------------------------------------- D1: per-BS ranking within the HRS classes
def d1(net, p, one_layer=False):
    """SUS core users and nearest-core groups (as the joint design); BS b ranks: super-common; core private streams by
    its own gain to the core user; group-common streams by its gain to the weakest member; non-core private streams by
    its own gain."""
    K, B = p['K'], p['B']
    order, groups, energy, _ = H_.joint_structure(net['Hd'], p, 'sus')
    g = link_gains(net, p)
    non = [k for k in range(K) if k not in order]
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in sorted(order, key=lambda k: -g[k, b])]
        l += [('g', i) for i in sorted(range(len(groups)), key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(non, key=lambda k: -g[k, b])]
        lists.append(l)
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'd1', one_layer)


def d1_1(net, p):
    return d1(net, p, True)


# --------------------------------------------------------------------------- D3: joint cores, per-BS extras
def d3(net, p, one_layer=False):
    """Core private streams in the SUS order at every BS (joint transmission up to S_max); then BS b ranks the
    group-common streams by its gain to the weakest member and the non-core private streams by its own gain."""
    K, B = p['K'], p['B']
    order, groups, energy, _ = H_.joint_structure(net['Hd'], p, 'sus')
    g = link_gains(net, p)
    non = [k for k in range(K) if k not in order]
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in order]
        l += [('g', i) for i in sorted(range(len(groups)), key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(non, key=lambda k: -g[k, b])]
        lists.append(l)
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'd3', one_layer)


def d3_1(net, p):
    return d3(net, p, True)


# --------------------------------------------------------------------------- D2: local SUS per BS
def d2(net, p, one_layer=False):
    """BS b selects N core users by SUS on its own channels; network cores = union; groups: nearest core (stacked
    channel correlation); BS b ranks: super-common, its own cores (SUS order), the other cores by its gain, group-common
    streams by its gain to the weakest member, non-core private streams by its gain."""
    K, B, N = p['K'], p['B'], p['N']
    Hd = net['Hd']
    g = link_gains(net, p)
    own = [H_.sus(Hd[:, b * N:(b + 1) * N], N) for b in range(B)]
    core = []
    for r in range(N):
        for b in range(B):
            if r < len(own[b]) and own[b][r] not in core: core.append(own[b][r])
    energy = np.sum(np.abs(Hd) ** 2, axis=1)
    Hn = Hd / np.sqrt(energy)[:, None]; corr = np.abs(Hn @ Hn.conj().T) ** 2
    follow = {c: [] for c in core}
    for k in range(K):
        if k in core: continue
        follow[core[int(np.argmax(corr[k, core]))]].append(k)
    groups = [[c] + follow[c] for c in core if follow[c]]
    non = [k for k in range(K) if k not in core]
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in own[b]]
        l += [('p', k) for k in sorted([k for k in core if k not in own[b]], key=lambda k: -g[k, b])]
        l += [('g', i) for i in sorted(range(len(groups)), key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(non, key=lambda k: -g[k, b])]
        lists.append(l)
    return assemble(lists, groups, core, _global_order(core, groups, energy, K), p, 'd2', one_layer)


def d2_1(net, p):
    return d2(net, p, True)


# --------------------------------------------------------------------------- D4 / D5: home BS first
def _home_struct(net, p):
    K, B = p['K'], p['B']
    order, groups, energy, _ = H_.joint_structure(net['Hd'], p, 'sus')
    g = link_gains(net, p)
    home = np.argmax(g, axis=1)                     # strongest BS of every UE
    ghome = [home[m[0]] for m in groups]            # a group's home: the home of its core user (head)
    non = [k for k in range(K) if k not in order]
    return order, groups, energy, g, home, ghome, non


def d4(net, p, one_layer=False):
    """BS b: super-common; its home cores (SUS order); the group-common streams of its home groups (decreasing size);
    the other cores (its gain); the other group-common streams (its gain to the weakest member); non-core privates
    (its gain)."""
    K, B = p['K'], p['B']
    order, groups, energy, g, home, ghome, non = _home_struct(net, p)
    G = len(groups)
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in order if home[k] == b]
        l += [('g', i) for i in sorted([i for i in range(G) if ghome[i] == b], key=lambda i: -len(groups[i]))]
        l += [('p', k) for k in sorted([k for k in order if home[k] != b], key=lambda k: -g[k, b])]
        l += [('g', i) for i in sorted([i for i in range(G) if ghome[i] != b], key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(non, key=lambda k: -g[k, b])]
        lists.append(l)
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'd4', one_layer)


def d4_1(net, p):
    return d4(net, p, True)


def d5(net, p, one_layer=False):
    """BS b covers its home UEs first: super-common; home cores (SUS order); home groups' common streams (decreasing
    size); home non-core privates (its gain); then the other cores, groups and non-core privates (its gain)."""
    K, B = p['K'], p['B']
    order, groups, energy, g, home, ghome, non = _home_struct(net, p)
    G = len(groups)
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in order if home[k] == b]
        l += [('g', i) for i in sorted([i for i in range(G) if ghome[i] == b], key=lambda i: -len(groups[i]))]
        l += [('p', k) for k in sorted([k for k in non if home[k] == b], key=lambda k: -g[k, b])]
        l += [('p', k) for k in sorted([k for k in order if home[k] != b], key=lambda k: -g[k, b])]
        l += [('g', i) for i in sorted([i for i in range(G) if ghome[i] != b], key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted([k for k in non if home[k] != b], key=lambda k: -g[k, b])]
        lists.append(l)
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'd5', one_layer)


def d5_1(net, p):
    return d5(net, p, True)


# --------------------------------------------------------------------------- experiment: joint design with g group-common
# streams in place of the last g core private streams (how much is a group-common worth at small S_max?)
def _jt_swap(net, p, g):
    K, S = p['K'], p['Smax']
    order, groups, energy, _ = H_.joint_structure(net['Hd'], p, 'sus')
    sizes = [len(m) for m in groups]
    grank = sorted(range(len(groups)), key=lambda i: (-sizes[i], i))[:g]
    ncore = max(0, min(len(order), S - 1) - len(grank))
    keys = ['c'] + [('p', k) for k in order[:ncore]] + [('g', i) for i in grank]
    lists = [keys for _ in range(p['B'])]
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, f'jt_swap{g}')


def jt_swap1(net, p):
    return _jt_swap(net, p, 1)


def jt_swap2(net, p):
    return _jt_swap(net, p, 2)


# --------------------------------------------------------------------------- DM: DoF-matched association
def dm_supports(order, g, p):
    """The largest number n of core private streams (SUS order) that the fronthaul admits when each is carried by its
    ceil(n/N) strongest BSs that still have a private-stream slot (S_max - 1 per BS). Returns (n, {core: BSs})."""
    B, N, S = p['B'], p['N'], p['Smax']
    for n in range(min(len(order), B * (S - 1)), 0, -1):
        m = min(B, -(-n // N))
        load = [0] * B; supp = {}
        for k in order[:n]:
            bs = [b for b in sorted(range(B), key=lambda b: -g[k, b]) if load[b] < S - 1][:m]
            if len(bs) < m: break
            for b in bs: load[b] += 1
            supp[k] = bs
        else:
            return n, supp
    return 0, {}


def dm(net, p, one_layer=False):
    """BS b: super-common; the core private streams it carries in the DoF-matched association (SUS order); group-common
    streams (its gain to the weakest member); the other private streams (its gain); the array-gain extensions of the
    served core streams (its gain)."""
    K, B = p['K'], p['B']
    order, groups, energy, _ = H_.joint_structure(net['Hd'], p, 'sus')
    g = link_gains(net, p)
    n, supp = dm_supports(order, g, p)
    served = order[:n]
    others = [k for k in range(K) if k not in served]
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in served if b in supp[k]]
        l += [('g', i) for i in sorted(range(len(groups)), key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(others, key=lambda k: -g[k, b])]
        l += [('p', k) for k in sorted([k for k in served if b not in supp[k]], key=lambda k: -g[k, b])]
        lists.append(l)
    d = assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'dm', one_layer)
    d.n_core_streams = n
    return d


def dm_1(net, p):
    return dm(net, p, True)
