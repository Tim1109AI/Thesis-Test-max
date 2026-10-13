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


# --------------------------------------------------------------------------- greedy-ZF core users
def zf_structure(net, p):
    """Core users by greedy ZF user selection (hrs.zf_greedy: add the UE that most increases the ZF sum rate with the
    total power split equally, stop when no UE increases it); every other UE joins the core user with the most
    correlated direct channel (as hrs.joint_structure)."""
    Hd, K = net['Hd'], p['K']
    order = H_.zf_greedy(Hd, p['B'] * p['Pmax'])
    energy = np.sum(np.abs(Hd) ** 2, axis=1)
    Hn = Hd / np.sqrt(energy)[:, None]; corr = np.abs(Hn @ Hn.conj().T) ** 2
    follow = {c: [] for c in order}
    for k in range(K):
        if k in order: continue
        follow[order[int(np.argmax(corr[k, order]))]].append(k)
    groups = [[c] + follow[c] for c in order if follow[c]]
    return order, groups, energy


def _lists_rank(order, groups, g, p, core_key):
    K, B = p['K'], p['B']
    non = [k for k in range(K) if k not in order]
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in sorted(order, key=lambda k: core_key(k, b))]
        l += [('g', i) for i in sorted(range(len(groups)), key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(non, key=lambda k: -g[k, b])]
        lists.append(l)
    return lists


def d1z(net, p, one_layer=False):
    """Greedy-ZF core users; BS b ranks core privates, group-commons and other privates by its own gain (as d1)."""
    order, groups, energy = zf_structure(net, p)
    g = link_gains(net, p)
    lists = _lists_rank(order, groups, g, p, lambda k, b: -g[k, b])
    return assemble(lists, groups, order, _global_order(order, groups, energy, p['K']), p, 'd1z', one_layer)


def d1z_1(net, p):
    return d1z(net, p, True)


def d3z(net, p, one_layer=False):
    """Greedy-ZF core users in their selection order at every BS (joint up to S_max), then per-BS extras (as d3)."""
    order, groups, energy = zf_structure(net, p)
    g = link_gains(net, p)
    pos = {k: i for i, k in enumerate(order)}
    lists = _lists_rank(order, groups, g, p, lambda k, b: pos[k])
    return assemble(lists, groups, order, _global_order(order, groups, energy, p['K']), p, 'd3z', one_layer)


def d3z_1(net, p):
    return d3z(net, p, True)


# --------------------------------------------------------------------------- QoS-feasibility promotion of group-common streams
def c0_bound(net, p):
    """Upper bound of the rate of the super-common stream: it must be decoded by every UE, and no stream can reach UE k
    with a larger SNR than P_max (sum_b ||h_{d,k,b}||)^2 (every BS at full power, coherently)."""
    Hd, N, B = net['Hd'], p['N'], p['B']
    amp = sum(np.linalg.norm(Hd[:, b * N:(b + 1) * N], axis=1) for b in range(B))
    return float(np.min(np.log2(1.0 + p['Pmax'] * amp ** 2)))


def promote(lists, groups, p, g, C0):
    """While the UEs that have neither a private nor a group-common stream need more QoS rate than the super-common can
    carry (R_th |A| > C0), the group-common stream of the group with the most such UEs moves, at the BS that reaches its
    weakest member best, ahead of the last private stream that BS carries. Returns the lists (modified in place)."""
    S, Rth, K, B = p['Smax'], p['Rth'], p['K'], p['B']
    while Rth > 0:
        sets = [l[:S] for l in lists]
        served = set().union(*map(set, sets))
        covered = {x[1] for x in served if x != 'c' and x[0] == 'p'}
        for x in served:
            if x != 'c' and x[0] == 'g': covered |= set(groups[x[1]])
        A = set(range(K)) - covered
        if Rth * len(A) <= C0: break
        cand = [i for i in range(len(groups)) if ('g', i) not in served and set(groups[i]) & A]
        moved = False
        for i in sorted(cand, key=lambda i: (-len(set(groups[i]) & A), i)):
            for b in sorted(range(B), key=lambda b: (-min(g[k, b] for k in groups[i]), b)):
                priv = [j for j, x in enumerate(sets[b]) if x != 'c' and x[0] == 'p']
                if not priv: continue
                lists[b].remove(('g', i)); lists[b].insert(priv[-1], ('g', i)); moved = True
                break
            if moved: break
        if not moved: break
    return lists


# --------------------------------------------------------------------------- DR: DoF-relevant association (+ promotion)
def dr(net, p, one_layer=False, qos=True):
    """SUS core users (|C| = min(K, BN)), each associated with its ceil(|C|/N) strongest BSs (the fewest BSs whose
    antennas can separate the |C| core users); BS b lists: super-common, its associated cores (SUS order), group-common
    streams (its gain to the weakest member), the other private streams (its gain). With qos: QoS-feasibility promotion."""
    K, B, N = p['K'], p['B'], p['N']
    order, groups, energy, _ = H_.joint_structure(net['Hd'], p, 'sus')
    g = link_gains(net, p)
    m = min(B, -(-len(order) // N))
    assoc = {k: set(sorted(range(B), key=lambda b: (-g[k, b], b))[:m]) for k in order}
    non = [k for k in range(K) if k not in order]
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in order if b in assoc[k]]
        l += [('g', i) for i in sorted(range(len(groups)), key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(non + [k for k in order if b not in assoc[k]], key=lambda k: -g[k, b])]
        lists.append(l)
    if qos and not one_layer and groups:
        promote(lists, groups, p, g, c0_bound(net, p))
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'dr', one_layer)


def dr_1(net, p):
    return dr(net, p, True)


def d1p(net, p, one_layer=False):
    """d1 (SUS cores, per-BS ranking by own gain) with the QoS-feasibility promotion."""
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
    if not one_layer and groups:
        promote(lists, groups, p, g, c0_bound(net, p))
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'd1p', one_layer)


# --------------------------------------------------------------------------- experiment: the joint design with greedy-ZF cores
def jz(net, p):
    return H_.joint_design(net, p, 'private_first', 'zf')


def jz_1(net, p):
    import composition as CM
    return CM.nogroup_design(jz(net, p), p)


def d2n(net, p, one_layer=False):
    """d2 without the private streams of non-core UEs (BS b: super-common, own cores, other cores, group-commons)."""
    K, B, N = p['K'], p['B'], p['N']
    d = d2(net, p, one_layer)
    G = 0 if one_layer else len(d.groups)
    core = set(d.core)
    keep = [j for j in d.served if j <= G or (j - 1 - G) in core]
    if d.bsmask is None:
        sets = [list(keep)] * B
    else:
        sets = [[j for j in d.bs_sets[b] if j in keep] for b in range(B)]
    dn = H_.Design([list(m) for m in d.groups], sorted(set().union(*map(set, sets))), K)
    dn.core = d.core; dn.priority = d.priority; dn.rule = 'd2n'
    mask = np.array([[j in sets[b] for j in dn.served] for b in range(B)])
    if not mask.all():
        dn.bsmask = mask; dn.bs_sets = [sorted(s) for s in sets]
    return dn


def d2n_1(net, p):
    return d2n(net, p, True)


# --------------------------------------------------------------------------- H1: groups around the BSs' own beam heads
def local_heads(net, p):
    """Union of the BSs' own SUS selections (N UEs per BS on its own N antennas), round-robin by rank."""
    Hd, B, N = net['Hd'], p['B'], p['N']
    own = [H_.sus(Hd[:, b * N:(b + 1) * N], N) for b in range(B)]
    heads = []
    for r in range(N):
        for b in range(B):
            if r < len(own[b]) and own[b][r] not in heads: heads.append(own[b][r])
    return heads, own


def head_groups(net, p, heads):
    """Every UE that is not a head joins the head with the most correlated (stacked) direct channel; a head with at
    least one follower forms a group with them."""
    Hd, K = net['Hd'], p['K']
    energy = np.sum(np.abs(Hd) ** 2, axis=1)
    Hn = Hd / np.sqrt(energy)[:, None]; corr = np.abs(Hn @ Hn.conj().T) ** 2
    follow = {h: [] for h in heads}
    for k in range(K):
        if k in heads: continue
        follow[heads[int(np.argmax(corr[k, heads]))]].append(k)
    return [[h] + follow[h] for h in heads if follow[h]]


def dh(net, p, one_layer=False):
    """Network SUS core users (|C| = min(K, BN)); groups around the BSs' own SUS heads (head_groups); BS b ranks core
    private streams by its own gain, group-common streams by its gain to the weakest member, other private streams by
    its own gain (as d1). Its 1-layer counterpart is d1_1."""
    K, B = p['K'], p['B']
    order, _, energy, _ = H_.joint_structure(net['Hd'], p, 'sus')
    heads, _ = local_heads(net, p)
    groups = head_groups(net, p, heads)
    g = link_gains(net, p)
    lists = _lists_rank(order, groups, g, p, lambda k, b: -g[k, b])
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'dh', one_layer)


def drh(net, p, one_layer=False):
    """dr with the head groups (head_groups) and the QoS-feasibility promotion. Its 1-layer counterpart is dr_1."""
    K, B, N = p['K'], p['B'], p['N']
    order, _, energy, _ = H_.joint_structure(net['Hd'], p, 'sus')
    heads, _ = local_heads(net, p)
    groups = head_groups(net, p, heads)
    g = link_gains(net, p)
    m = min(B, -(-len(order) // N))
    assoc = {k: set(sorted(range(B), key=lambda b: (-g[k, b], b))[:m]) for k in order}
    non = [k for k in range(K) if k not in order]
    lists = []
    for b in range(B):
        l = ['c'] + [('p', k) for k in order if b in assoc[k]]
        l += [('g', i) for i in sorted(range(len(groups)), key=lambda i: -min(g[k, b] for k in groups[i]))]
        l += [('p', k) for k in sorted(non + [k for k in order if b not in assoc[k]], key=lambda k: -g[k, b])]
        lists.append(l)
    if not one_layer and groups:
        promote(lists, groups, p, g, c0_bound(net, p))
    return assemble(lists, groups, order, _global_order(order, groups, energy, K), p, 'drh', one_layer)


# --------------------------------------------------------------------------- DZ: SUS cores stopped by the ZF sum rate
def zf_sum_rate(Hd, C, P):
    """Sum rate of zero-forcing to the UEs C with the total power P split equally (direct channels)."""
    Hs = Hd[C]
    g = 1.0 / np.maximum(np.real(np.diag(np.linalg.inv(Hs @ Hs.conj().T))), 1e-300)
    return float(np.sum(np.log2(1.0 + P / len(C) * g)))


def sus_zf_cores(net, p):
    """Core users: the SUS order on the stacked direct channels (as the current design), kept while the next UE
    increases the ZF sum rate (total power B P_max split equally); at most min(K, BN)."""
    Hd = net['Hd']
    order = H_.sus(Hd, p['BN'])
    P = p['B'] * p['Pmax']
    n, best = 1, zf_sum_rate(Hd, order[:1], P)
    while n < len(order):
        r = zf_sum_rate(Hd, order[:n + 1], P)
        if r <= best: break
        n, best = n + 1, r
    return order[:n]


def nearest_core_groups(Hd, core, K):
    """Every non-core UE joins the core user with the most correlated direct channel (as the current design)."""
    energy = np.sum(np.abs(Hd) ** 2, axis=1)
    Hn = Hd / np.sqrt(energy)[:, None]; corr = np.abs(Hn @ Hn.conj().T) ** 2
    follow = {c: [] for c in core}
    for k in range(K):
        if k in core: continue
        follow[core[int(np.argmax(corr[k, core]))]].append(k)
    return [[c] + follow[c] for c in core if follow[c]], energy


def dz(net, p, one_layer=False):
    """SUS cores stopped by the ZF sum rate (sus_zf_cores); nearest-core groups; BS b ranks core private streams by its
    own gain, group-common streams by its gain to the weakest member, other private streams by its own gain."""
    K = p['K']
    core = sus_zf_cores(net, p)
    groups, energy = nearest_core_groups(net['Hd'], core, K)
    g = link_gains(net, p)
    lists = _lists_rank(core, groups, g, p, lambda k, b: -g[k, b])
    return assemble(lists, groups, core, _global_order(core, groups, energy, K), p, 'dz', one_layer)


def dz_1(net, p):
    return dz(net, p, True)


# --------------------------------------------------------------------------- DQ: DZ with the QoS floor on the core count
def core_users(net, p):
    """Core users: the SUS order on the stacked direct channels, kept while the next UE increases the ZF sum rate
    (total power B P_max split equally), and at least until the super-common stream could carry the QoS of the
    remaining UEs, R_th (K - n) <= C0 (c0_bound); at most min(K, BN)."""
    Hd, K = net['Hd'], p['K']
    order = H_.sus(Hd, p['BN'])
    P = p['B'] * p['Pmax']
    n, best = 1, zf_sum_rate(Hd, order[:1], P)
    while n < len(order):
        r = zf_sum_rate(Hd, order[:n + 1], P)
        if r <= best: break
        n, best = n + 1, r
    C0 = c0_bound(net, p)
    while n < len(order) and p['Rth'] * (K - n) > C0:
        n += 1
    return order[:n]


def dq(net, p, one_layer=False):
    """core_users; nearest-core groups; BS b ranks core private streams by its own gain, group-common streams by its
    gain to the weakest member, other private streams by its own gain."""
    K = p['K']
    core = core_users(net, p)
    groups, energy = nearest_core_groups(net['Hd'], core, K)
    g = link_gains(net, p)
    lists = _lists_rank(core, groups, g, p, lambda k, b: -g[k, b])
    return assemble(lists, groups, core, _global_order(core, groups, energy, K), p, 'dq', one_layer)


def dq_1(net, p):
    return dq(net, p, True)
