# DESIGN.md — per-BS ranking of the HRS streams (variant `DQ`, 1-layer counterpart `DQ_1`)

Design round v10 (BS-specific stream sets). Code: `code/bsdesign.py` (the design, ~120 lines), `code/algo.py` (one
switch for the AO start, off by default), `harness/variants.py` (`DQ`, `DQ_1`; the other entries are the methods of
§4). Results: `results/DQ__*.jsonl`, `results/DQ_1__*.jsonl`, `results/DQ@SC__T2__bench.jsonl`, reports
`results/DQ__report*.json`.

## 0. Summary

**The design.** (1) The core users are the users of the current SUS order that still pay for a zero-forcing beam:
the order is kept while the next user increases the ZF sum rate, and at least as long as the remaining users could
not get their QoS from one common stream. (2) Nearest-core groups, as in the current design. (3) Every BS ranks the
streams by its own direct channels: the super-common stream first, then the core private streams, the group-common
streams and the other private streams, each class by decreasing gain of the BS to the stream's (weakest) receiver.
Each BS carries the first S_max entries of its own list. A core user (or group, or other UE) is served by every BS
when every BS has room for it, and otherwise by the BSs that reach it best, which in a network of many BSs over a
large area means the BSs around it. No parameter, no test, no optimization; about 2 ms per drop.

**Results** (details in §3; Q = 50 where marked, otherwise the Q = 5 screen):

| Requirement | Result |
|---|---|
| R1, T2 (Q = 5, 144 runs) | DQ − DQ_1 = 0.00, −0.18 ± 0.33, **+0.71 ± 0.32, +2.04 ± 0.87, +1.31 ± 0.82, +2.49 ± 1.57** (R_th = 0 … 2.5) |
| R1, E3 (Q = 5, 144 runs) | 0.00, +0.01 ± 0.01, −0.00 ± 0.41, +0.47 ± 0.78, +0.89 ± 0.93, +1.27 ± 0.78 |
| R1, T2 (Q = 50, confirm, 108 runs) | +0.21 ± 0.40, −1.28 ± 0.80, +0.30 ± 0.95, +0.54 ± 1.10, +1.58 ± 1.92, **+2.13 ± 1.09** |
| R1, E3 (Q = 50, confirm, 108 runs) | +1.04 ± 0.58, +0.20 ± 0.25, +0.03 ± 0.32, +1.09 ± 0.83, **+3.67 ± 1.65**, +0.23 ± 0.94 |
| R1, composition-study setting (Q = 50, 30 runs) | +0.18 ± 2.24, −1.90 ± 1.43, +2.35 ± 2.16, +2.03 ± 3.50, **+20.69 ± 1.33, +50.93 ± 12.40** |
| R2 (Q = 50, bench) | DQ 76.3 / 86.1 / 86.1 (M = 100 / 300 / 500) vs sparse BF 63.1 / 75.1 / 81.0 (DQ − sparse BF = +9.8 ± 2.6 over the 15 runs) and stream clustering on DQ 44.5 / 57.2 / 62.5 (+28.1 ± 2.2); J 73.5 / 82.0 / 88.7 |
| R3 (Q = 50, bench) | super-common 14.1 %, group-common 10.1 % of the sum rate (15/15 runs meet the QoS) |
| R4 (Q = 50, smax) | rises with S_max and flattens: K = 8: 73.4 → 96.5 → 97.4 → 97.5 → 99.4 → 99.4 → 99.4; K = 12: 68.6 → 94.4 → 111.9 → 115.1 → 113.7 → 116.9 → 116.5; K = 16: 61.0 → 72.8 → 102.7 → 102.7 → 109.8 → 107.6 → 108.9 (S_max = 4 … 16); largest step down −2.2 ± 1.9 |
| BS-specific streams | in 97/144 (T2) and 114/144 (E3) screen runs and in 9/15 benchmark runs; private streams in both scenarios, group-common streams in T2 (setting e) |

**Verdict, requirement by requirement.**

* **R1 — met in the mean, not clearly at R_th = 1–1.5.** At Q = 50 the mean of DQ − DQ_1 is ≥ 0 at every R_th ≥ 1
  in both scenarios, but at R_th = 1–1.5 the margins are within one standard error; they are clear at R_th = 2 in E3,
  at 2.5 in T2, and from R_th = 2 on in the thesis's composition-study setting (+20.7, +50.9). At R_th = 0.5 in T2
  the mean is −1.28 ± 0.80 (a tie is allowed there). The reasons are structural (§3.1, §5): in 7 of the 12
  scenario-settings of the grid the core private streams fill the fronthaul, and DQ and DQ_1 are the same design;
  where they differ, the 1-layer counterpart spreads the private streams of the non-core users over the BSs and
  carries a moderate QoS load almost as well as the group-common streams; and single paired runs at Q = 50 differ by
  ±5–15 bit/s/Hz. CALIBRATION_SENTENCE
* **R2 — met.** +9.8 ± 2.6 over sparse beamforming over the 15 benchmark runs (+13.2 / +11.1 / +5.1 at M = 100 /
  300 / 500) and +28.1 ± 2.2 over stream clustering on DQ's streams; DQ is also 1.5 above the current framework J.
* **R3 — met.** Super-common 14.1 % and group-common 10.1 % of the sum rate at K = 16, R_th = 2.
* **R4 — met.** The rate rises with S_max and flattens; the steps along the plateau are within ±2.3 (stream sets
  nested in S_max).
* **Design requirement — met.** The BSs carry different private streams in most runs of both scenarios (core private
  streams at small S_max, non-core private streams at large S_max and at the benchmark) and different group-common
  streams in T2 e.
* **Method.** One deterministic design for every setting, no AO test, no tuned parameter, nothing tied to B = 2, 3 or
  to the BS positions; core users of their own for some BSs and shared ones for others, joint transmission when the
  fronthaul admits every core user at every BS (§1.9).

## 1. The design

### 1.1 Idea

The design keeps the two structural decisions of the current design that the benchmark figure relies on, SUS core
users and nearest-core groups, and changes two things.

* **How many core users.** The current design takes min(K, BN) core users, the largest number zero-forcing can
  separate. The new design keeps the SUS order only as long as the next user still pays for its ZF beam (the ZF sum
  rate increases), and at least as long as the users left without a private stream could not get their QoS from a
  single common stream.
* **Who carries what.** The BSs no longer carry one common stream set. Each BS ranks the streams of the hierarchy by
  its own direct channels, class by class in the role order of the hierarchy, and carries the first S_max entries of
  its own list.

### 1.2 Notation

B BSs with N antennas each, K UEs; h_{d,k} = [f_{1,k}, …, f_{B,k}] ∈ C^{1×BN} the stacked direct channel of UE k
(noise-normalized), with f_{b,k} ∈ C^{1×N} the part of BS b; g_{k,b} = ||f_{b,k}||² the direct-channel gain of BS b
to UE k; P_max the per-BS power; R_th the QoS threshold; S_max the per-BS fronthaul limit; M_{b,j} ∈ {0, 1} whether
BS b carries stream j (j = c the super-common stream, j = g the group-common stream of group g, j = k the private
stream of UE k).

### 1.3 Step 1 — core users

SUS order (the greedy projection step of the current design, eq. (core_selection) of the thesis), without change:

    u_{i+1} = argmax_{k ∉ C_i} || h_{d,k} (I_BN − P_{C_i}) ||²,   C_i = {u_1, …, u_i},   i = 0, …, min(K, BN) − 1.

ZF sum rate of a set C, with the total power B·P_max split equally over its |C| beams (H_C stacks the h_{d,k} of C):

    R_ZF(C) = Σ_{k∈C} log2( 1 + (B P_max / |C|) / [ (H_C H_C^H)^{-1} ]_{kk} ).

**Stopping rule.** n_ZF is the first i at which the next user does not increase the ZF sum rate,
R_ZF(C_{i+1}) ≤ R_ZF(C_i) (n_ZF = min(K, BN) if it increases throughout).

**QoS floor.** The super-common stream is decoded by every UE, and no stream reaches UE k with a larger SNR than if
every BS beamformed its full power coherently to k, so its rate is at most

    C_0 = min_k log2( 1 + P_max ( Σ_b ||f_{b,k}|| )² ).

A UE without a private stream needs R_th from the common streams. Whenever no group-common stream fits into the
fronthaul (always in the 1-layer counterpart), the super-common stream alone must carry R_th (K − n), which is
impossible if R_th (K − n) > C_0. The number of core users is therefore

    n = min{ i ≥ n_ZF : R_th (K − i) ≤ C_0 }  (at most min(K, BN)),     C = C_n = {u_1, …, u_n}.

### 1.4 Step 2 — groups (as in the current design)

Every non-core UE joins the core user with the most correlated direct channel,
a(k) = argmax_{a∈C} |h_{d,k} h_{d,a}^H|² / (||h_{d,k}||² ||h_{d,a}||²), and every core user with at least one
follower heads the group U_a = {a} ∪ {k ∉ C : a(k) = a}. Each group holds exactly one core user, so at most
min(n, K − n) ≤ ⌊K/2⌋ groups of size 2 … K − n + 1 ≤ K − 1 (n ≥ 2; with n = 1 the only group would contain every UE
and duplicate the super-common stream, so it is not formed).

### 1.5 Step 3 — the stream set of every BS

BS b orders the streams as

    L_b = ( c ;
            the core private streams k ∈ C  by decreasing g_{k,b} ;
            the group-common streams g      by decreasing min_{k∈U_g} g_{k,b} ;
            the other private streams k ∉ C by decreasing g_{k,b} )

and carries the first S_max of them: M_{b,j} = 1 if and only if j is among the first S_max entries of L_b. The served
streams are the union over the BSs; a stream is precoded jointly over the antennas of the BSs that carry it (the
evaluator constrains w_{j,b} = 0 where M_{b,j} = 0).

### 1.6 Algorithm

```
Input: direct channels h_{d,k} (k = 1..K); B, N, S_max, P_max, R_th
1  u ← SUS order on the stacked direct channels (min(K, BN) UEs)                         [as the current design]
2  n ← 1;  while n < |u| and R_ZF(u_1..u_{n+1}) > R_ZF(u_1..u_n):  n ← n + 1          [ZF stopping rule]
3  C_0 ← min_k log2(1 + P_max (Σ_b ||f_{b,k}||)²);  while n < |u| and R_th (K − n) > C_0:  n ← n + 1   [QoS floor]
4  C ← {u_1, …, u_n}
5  for every k ∉ C:  a(k) ← the core user with the most correlated direct channel;  U_a ← {a} ∪ a^{-1}(a)
6  for b = 1 … B:
7      L_b ← [c] + sort(C by −g_{k,b}) + sort(groups by −min_{k∈U} g_{k,b}) + sort(K∖C by −g_{k,b})
8      BS b carries the first S_max entries of L_b                                     (M_{b,j})
Output: the groups, the served streams ∪_b L_b[1..S_max], M_{b,j}; the core users C start the AO
1-layer counterpart: line 7 without the group-common streams (their slots go to the next private streams of L_b)
```

In code: `bsdesign.design(net, p)` returns an `hrs.Design` (with `d.bsmask` and `d.bs_sets` when the BSs carry
different streams; `d.core = C`; `d.priority` = super-common, core privates in SUS order, group-common streams by
decreasing size, other privates by decreasing channel energy — every stream, so that stream clustering on the design
can use it); `bsdesign.design_1layer(net, p)` is the 1-layer counterpart.

### 1.7 The 1-layer counterpart (`DQ_1`)

The same three steps, the same core users and the same order of the private streams at every BS, without the
group-common streams: each BS carries the super-common stream and the first S_max − 1 private streams of its list.

### 1.8 What it does in the test grid

From the designs of the screen drops (901–904, R_th ∈ {0, 1, 2}); "cores carried by all BSs": share of the served
core private streams that every BS carries.

| scen | set | N | K | BN | S_max | core users | groups | group-commons served | streams (1-layer) | BS-specific | cores carried by all BSs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T2 | a | 3 | 8 | 6 | 12 | 4–5 | 2–3 | 2–3 | 11.8 (9.0) | 0/12 | 100% |
| T2 | b | 3 | 12 | 6 | 4 | 4–6 | 2–4 | 0 | 6.0 (6.0) | 12/12 | 22% |
| T2 | c | 3 | 16 | 6 | 6 | 6 | 3–5 | 0 | 7.0 (7.0) | 12/12 | 67% |
| T2 | d | 5 | 12 | 10 | 6 | 5–6 | 2–4 | 0 | 6.5 (6.5) | 6/12 | 83% |
| T2 | e | 5 | 16 | 10 | 10 | 7–8 | 3–5 | 2 | 10.8 (11.2) | 9/12 | 100% |
| T2 | f | 5 | 16 | 10 | 20 | 7–8 | 3–5 | 3–5 | 21.0 (17.0) | 9/12 | 100% |
| E3 | a | 3 | 8 | 9 | 12 | 6–8 | 0–1 | 0–1 | 9.8 (9.0) | 0/12 | 100% |
| E3 | b | 3 | 12 | 9 | 4 | 6–9 | 2–5 | 0 | 8.2 (8.2) | 12/12 | 4% |
| E3 | c | 3 | 16 | 9 | 6 | 8–9 | 4–6 | 0 | 9.2 (9.2) | 12/12 | 27% |
| E3 | d | 5 | 12 | 15 | 6 | 8–10 | 1–3 | 0 | 10.0 (10.0) | 12/12 | 9% |
| E3 | e | 5 | 16 | 15 | 10 | 10–11 | 3–5 | 0 | 11.5 (11.5) | 12/12 | 65% |
| E3 | f | 5 | 16 | 15 | 20 | 10–11 | 3–5 | 3–5 | 21.0 (17.0) | 9/12 | 100% |

The current design takes min(K, BN) core users: 6, 6, 6, 10, 10, 10 (T2) and 8, 9, 9, 12, 15, 15 (E3); in E3 a and d
every UE is a core user and there is no group at all, in E3 e and f one UE is left for one group. At the benchmark
setting (T2, K = 16, N = 3, S_max = 12, R_th = 2) the new rule keeps the current design's six core users in all five
drops (the ZF rule alone keeps six in four drops; the QoS floor adds the sixth in drop 802), and the groups are the
current design's.

### 1.9 Many BSs scattered over a large area

The design has no notion of B = 2 or 3 or of the BS positions. Its behaviour on networks that are not in the grid
(design only, the channel model of the package, UEs uniform over the area; `python3 tools/large_area.py`):

```
T2 layout, S_max = 12: B=2 K=16 N=3 S_max=12 R_th=2.0: |C|=6 groups=3 served streams=14 BS-specific=True
   BSs per core private: [0, 6] (count of cores carried by 1..B BSs; 0 not carried)
   distance rank of the carrying BSs (1 = nearest): [6, 6]
   BSs per served group-common: [2, 2, 2]
T2 layout, S_max = 4: B=2 K=16 N=3 S_max=4 R_th=2.0: |C|=6 groups=3 served streams=7 BS-specific=True
   BSs per core private: [6, 0] (count of cores carried by 1..B BSs; 0 not carried)
   distance rank of the carrying BSs (1 = nearest): [6, 0]
9 BSs on a 600 m grid, S_max = 4: B=9 K=36 N=3 S_max=4 R_th=1.0: |C|=19 groups=9 served streams=20 BS-specific=True
   BSs per core private: [13, 4, 2, 0, 0, 0, 0, 0, 0] (count of cores carried by 1..B BSs; 0 not carried)
   distance rank of the carrying BSs (1 = nearest): [18, 7, 2, 0, 0, 0, 0, 0, 0]
9 BSs on a 600 m grid, S_max = 7: B=9 K=36 N=3 S_max=7 R_th=1.0: |C|=19 groups=9 served streams=20 BS-specific=True
   BSs per core private: [1, 8, 5, 3, 2, 0, 0, 0, 0] (count of cores carried by 1..B BSs; 0 not carried)
   distance rank of the carrying BSs (1 = nearest): [19, 17, 9, 4, 2, 1, 0, 1, 1]
9 BSs on a 600 m grid, S_max = 13: B=9 K=36 N=3 S_max=13 R_th=1.0: |C|=19 groups=9 served streams=20 BS-specific=True
   BSs per core private: [0, 0, 2, 4, 5, 3, 1, 0, 4] (count of cores carried by 1..B BSs; 0 not carried)
   distance rank of the carrying BSs (1 = nearest): [19, 19, 18, 13, 16, 8, 5, 5, 5]
9 BSs on a 600 m grid, S_max = 28: B=9 K=36 N=3 S_max=28 R_th=1.0: |C|=19 groups=9 served streams=29 BS-specific=True
   BSs per core private: [0, 0, 0, 0, 0, 0, 0, 0, 19] (count of cores carried by 1..B BSs; 0 not carried)
   distance rank of the carrying BSs (1 = nearest): [19, 19, 19, 19, 19, 19, 19, 19, 19]
   BSs per served group-common: [5, 9, 9, 9, 8, 9, 8, 6, 9]
16 BSs on a 1 km grid, S_max = 7: B=16 K=64 N=3 S_max=7 R_th=1.0: |C|=45 groups=13 served streams=46 BS-specific=True
   BSs per core private: [8, 26, 8, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] (count of cores carried by 1..B BSs; 0 not carried)
   distance rank of the carrying BSs (1 = nearest): [44, 29, 13, 8, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
4 BSs within 40 m (dense), S_max = 13: B=4 K=12 N=3 S_max=13 R_th=1.0: |C|=8 groups=4 served streams=13 BS-specific=False
   BSs per core private: [0, 0, 0, 8] (count of cores carried by 1..B BSs; 0 not carried)
   distance rank of the carrying BSs (1 = nearest): [8, 8, 8, 8]
   BSs per served group-common: [4, 4, 4, 4]
```

With 9 BSs on a 600 m grid and S_max = 4, 13 of the 19 core users are carried by one BS, 4 by two and 2 by three, and
18 of the 27 carrying BSs are the nearest BS of the user (7 the second nearest). With S_max = 7 the core users are
carried by 1–5 BSs, mostly the nearest ones. Joint transmission appears by itself when the fronthaul admits every
core user at every BS (S_max = 28 on the 600 m grid; S_max = 13 with four BSs within 40 m of each other). This is the
behaviour asked for: core users of their own for some BSs, core users shared by several BSs, and all core users at
all BSs when the scenario allows it.

Robustness (`python3 tools/stress_bsdesign.py`): on 600 random networks (B = 1 … 16 BSs and K = 1 … 48 UEs at random
positions over areas of 50 m to 2 km, N = 1 … 8, S_max = 1 … 40, R_th = 0 … 4, some with co-located UEs) every design
and its 1-layer counterpart pass `discrete.check` (disjoint groups of admissible size, at most S_max streams per BS,
the super-common stream at every BS); 314 of them are BS-specific, 286 joint, 392 have groups.

### 1.10 AO start for BS-specific stream sets (switch, off by default)

The evaluator's core-user start (`algo.init_core`) computes the regularized ZF directions on all BN antennas and then
zeroes the blocks of the BSs that do not carry a stream. For BS-specific sets this truncation can leave a stream with
a poor direction. `algo.init_core_support` (`init='core_s'`, coefficient seed `seed='rule_s'`) computes every
direction on the antennas of the BSs that carry its stream: regularized ZF on the carrying antennas for the served core
private streams, the dominant eigenvector of the normalized channels of its decoders for a common stream, the matched
filter for any other private stream; powers as in `init_core`. With joint transmission (`d.bsmask` None) it is
`init_core` itself. The switch is off by default (`NP.NEW` keeps `init='core'`), so JH, J1 and every stored run stay
bit-identical (`harness/selftest.py` passes with identical traces after the change); `DQ`, `DQ_1` and every
BS-specific prototype of §4 set it in `harness/variants.py` (`SUPPORT_START`). The stream-clustering benchmark on
the design (`DQ@SC`) takes the options of `DQ` (`harness/grid.py`), so the same start applies to it. Measured effect
on the first BS-specific prototype (per-BS ranking with min(K, BN) core users, `D1` vs `D1s`, Q = 5, settings b, c,
f, R_th ∈ {0, 1, 2}, 2 drops): +0.0 ± 1.0 bit/s/Hz in T2 and +0.9 ± 0.6 in E3, i.e. small; it is kept because it is
the consistent start for streams that some BSs do not carry, not for its measured gain.

### 1.11 Cost

* The design: SUS (as before), at most min(K, BN) ZF sum rates of size ≤ n, the gains and B sorts: 1.9 ms (T2) and
  2.2 ms (E3) per drop on average (`cpu_design`, max 5 ms).
* The runs: the BSs of DQ carry different streams in most runs, so DQ serves more distinct streams than the current
  design and the evaluations cost more: 161 (T2) and 182 (E3) CPU-s per run at Q = 50 on average, 550–600 CPU-s in
  setting f, where the BSs carry about 21 distinct streams (§3.7).

## 2. Why it works, and why it needs no tuning

* **Core users.** In the line-of-sight channels of the thesis (half-wavelength arrays, rank-one cascades), the
  stacked direct channels have a low effective rank: the SUS residuals fall steeply after a few users, and the last
  users SUS is forced to take when |C| = min(K, BN) are nearly aligned with earlier ones. Their ZF beams cost every
  other beam much of its gain. The sign of the ZF sum-rate increment says exactly when the next user stops paying for
  its beam (the stopping rule of greedy ZF user selection, Dimic & Sidiropoulos 2005, applied to the SUS order of the
  current design). With K ≫ BN (the benchmark: K = 16, BN = 6) SUS finds well separated users and the rule keeps BN of
  them, as the current design does; with K ≈ BN (E3 f: K = 16, BN = 15) it keeps 10–11.
* **Groups.** The users that are not core users are exactly those that ZF cannot separate from the core users. Each
  joins the core user it is most aligned with, and the group-common stream serves them along that direction. Because
  the number of core users now follows the channels, the hierarchy has group-common streams to offer wherever K
  exceeds the number of users worth a ZF beam, also where K ≤ BN (E3 a and d), where the current design has no group.
  Each group contains exactly one user with a private stream (its core user), so only one private stream pays the
  decoding requirement of a group-common stream. (Groups whose members all have private streams were tried and lose
  heavily at the benchmark, §4.)
* **QoS floor.** It removes a design that cannot meet the QoS even in principle whenever no group-common stream fits.
  It binds rarely: in 2 of the 288 screen runs (R_th = 2.5) and in one of the five benchmark drops, where the ZF rule
  alone keeps 5 core users (Q = 5: 49.1 instead of 69.1 bit/s/Hz at M = 100, §4).
* **Per-BS ranking.** The fronthaul limit is per BS, so the slots are each BS's own resource. The class order is the
  role order of the hierarchy (the order of the current design): the super-common stream reaches every UE; the core
  private streams carry the spatially multiplexed rate; the group-common streams carry the QoS of their non-core
  members at a lower decoding requirement than the super-common stream; the other private streams cannot be
  separated from the core streams. Within a class each BS takes the streams it delivers best.
* **When does a core user go to all BSs?** When every BS has room for all core users (S_max − 1 ≥ |C|): every BS's
  list then starts with the same core users and joint transmission follows. Otherwise each BS carries the core users
  it reaches best; a core user that several BSs reach well is carried by several of them; one that no BS ranks among
  its first S_max − 1 has no private stream (its group-common or the super-common stream carries its QoS). With many
  BSs over a large area, |C| grows with the area while S_max is per BS, and the gain falls with the distance, so
  every BS carries the core users, groups and other UEs around it — local association without any distance
  threshold (§1.9).
* **R1.** The 1-layer counterpart has the same core users and the same lists without group-common streams. Where every
  BS's first S_max entries are super-common and core private streams (S_max = N + 1 and 2N in the grid), both carry
  the same streams and tie exactly. Where a BS has room after its core private streams (S_max = 4N in both scenarios,
  and setting e in T2), the group-common streams take the slots that the 1-layer counterpart gives to the private
  streams of the non-core users — the users ZF cannot separate. A group-common stream carries the QoS of all its
  members at once; once the QoS load is high this is worth far more than the private streams it replaces (R_th ≥ 2,
  §3.1–3.2), at a moderate load the two are close (§5).
* **R4 (S_max).** The core users, the groups and every BS's list do not depend on S_max; a larger S_max only appends
  streams to the carried prefix of each list. The stream set of every BS is nested in S_max.
* **No empirical tuning.** Every quantity is a channel quantity (SUS residuals, correlations, gains, the ZF sum rate
  with the system's total power, the single-stream bound C_0 with the system's P_max) or a setting (B, N, K, S_max,
  R_th). There is no threshold, weight or constant: the stopping rule is the sign of a sum-rate difference, the floor
  an inequality between the QoS load and a capacity bound, the association a sort. Nothing refers to the test grid,
  to B = 2 or 3 or to the BS positions, and there is no test of alternatives by the AO.

## 3. Results

All numbers in bit/s/Hz; a run whose QoS shortfall exceeds 1e-2 counts as 0 (the harness rule). J, JH, J1: the
current framework, its design without the stream-set test, its 1-layer RSMA (reference). Every comparison is paired
on common runs; ± is the standard error of the paired mean.

### 3.1 R1 at Q = 50 (`--tier confirm`, both scenarios, `--by-setting`)

`python3 tools/report.py DQ --by-setting` (216 runs per variant, drops 901–903; JH and J1 at Q = 50: see §6):

```
===== scenario T2, Q = 50: 108 common runs (DQ: 108, DQ_1: 108)
-- T2, all settings
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0   18    117.65    117.44    +0.21± 0.40      18/18
    0.5   18    114.73    116.01    -1.28± 0.80      18/18
      1   18    109.96    109.66    +0.30± 0.95      18/18
    1.5   18    102.79    102.26    +0.54± 1.10      18/18
      2   18     94.05     92.47    +1.58± 1.92      18/18
    2.5   18     77.86     75.73    +2.13± 1.09      15/15
    all  108    102.84    102.26    +0.58± 0.47      105/105
-- T2, setting a
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    105.77    105.98    -0.21± 0.61      3/3
    0.5    3    102.38    103.81    -1.43± 2.21      3/3
      1    3    102.12    102.27    -0.15± 3.91      3/3
    1.5    3    100.98    104.20    -3.21± 2.73      3/3
      2    3    105.15    103.07    +2.08± 3.81      3/3
    2.5    3    107.02    106.79    +0.24± 3.78      3/3
    all   18    103.91    104.35    -0.45± 1.13      18/18
-- T2, setting b
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3     75.96     75.96    +0.00± 0.00      3/3
    0.5    3     74.74     74.74    +0.00± 0.00      3/3
      1    3     68.44     68.44    +0.00± 0.00      3/3
    1.5    3     64.59     64.59    +0.00± 0.00      3/3
      2    3     65.13     65.13    +0.00± 0.00      3/3
    2.5    3     54.29     54.29    +0.00± 0.00      3/3
    all   18     67.19     67.19    +0.00± 0.00      18/18
-- T2, setting c
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3     82.47     82.47    +0.00± 0.00      3/3
    0.5    3     88.96     88.96    +0.00± 0.00      3/3
      1    3     82.27     82.27    +0.00± 0.00      3/3
    1.5    3     74.82     74.82    +0.00± 0.00      3/3
      2    3     55.57     55.57    +0.00± 0.00      3/3
    2.5    3      0.00      0.00    +0.00± 0.00      0/0
    all   18     64.01     64.01    +0.00± 0.00      15/15
-- T2, setting d
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    122.61    122.61    +0.00± 0.00      3/3
    0.5    3    112.05    112.05    +0.00± 0.00      3/3
      1    3    110.72    110.72    +0.00± 0.00      3/3
    1.5    3    106.25    106.25    +0.00± 0.00      3/3
      2    3     95.56     95.56    +0.00± 0.00      3/3
    2.5    3     83.77     83.77    +0.00± 0.00      3/3
    all   18    105.16    105.16    +0.00± 0.00      18/18
-- T2, setting e
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    161.18    161.68    -0.50± 1.82      3/3
    0.5    3    156.15    160.29    -4.15± 3.99      3/3
      1    3    153.44    149.27    +4.16± 2.87      3/3
    1.5    3    137.06    131.81    +5.25± 3.97      3/3
      2    3    115.70    112.23    +3.46±10.98      3/3
    2.5    3    102.81     96.05    +6.76± 4.27      3/3
    all   18    137.72    135.22    +2.50± 2.09      18/18
-- T2, setting f
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    157.93    155.97    +1.96± 1.62      3/3
    0.5    3    154.10    156.20    -2.10± 2.17      3/3
      1    3    142.76    144.99    -2.23± 3.34      3/3
    1.5    3    133.06    131.89    +1.17± 4.50      3/3
      2    3    127.21    123.27    +3.94± 6.68      3/3
    2.5    3    119.30    113.51    +5.79± 1.42      3/3
    all   18    139.06    137.64    +1.42± 1.48      18/18
-- DQ: mean served streams 10.56, group-common served 1.44, private served 8.12; BS-specific in 73/108 runs; per run, carried by a subset of the BSs: group-common 0.24, private 1.67
-- CPU per run (s): DQ 160.9, DQ_1 68.1; DQ discrete design 0.002

===== scenario E3, Q = 50: 108 common runs (DQ: 108, DQ_1: 108)
-- E3, all settings
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0   18    141.88    140.84    +1.04± 0.58      18/18
    0.5   18    137.72    137.52    +0.20± 0.25      18/18
      1   18    135.01    134.98    +0.03± 0.32      18/18
    1.5   18    128.66    127.57    +1.09± 0.83      18/18
      2   18    122.31    118.64    +3.67± 1.65      18/18
    2.5   18    112.24    112.01    +0.23± 0.94      18/18
    all  108    129.64    128.60    +1.04± 0.38      108/108
-- E3, setting a
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    142.20    142.00    +0.20± 0.26      3/3
    0.5    3    140.67    141.55    -0.88± 0.65      3/3
      1    3    141.17    140.54    +0.62± 0.34      3/3
    1.5    3    139.87    140.17    -0.30± 1.91      3/3
      2    3    141.88    136.73    +5.15± 4.31      3/3
    2.5    3    139.37    140.23    -0.86± 1.31      3/3
    all   18    140.86    140.20    +0.66± 0.86      18/18
-- E3, setting b
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3     84.35     84.35    +0.00± 0.00      3/3
    0.5    3     81.23     81.23    +0.00± 0.00      3/3
      1    3     78.51     78.51    +0.00± 0.00      3/3
    1.5    3     80.12     80.12    +0.00± 0.00      3/3
      2    3     73.24     73.24    +0.00± 0.00      3/3
    2.5    3     68.25     68.25    +0.00± 0.00      3/3
    all   18     77.62     77.62    +0.00± 0.00      18/18
-- E3, setting c
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    106.98    106.98    +0.00± 0.00      3/3
    0.5    3    101.39    101.39    +0.00± 0.00      3/3
      1    3     96.65     96.65    +0.00± 0.00      3/3
    1.5    3     87.51     87.51    +0.00± 0.00      3/3
      2    3     77.39     77.39    +0.00± 0.00      3/3
    2.5    3     51.67     51.67    +0.00± 0.00      3/3
    all   18     86.93     86.93    +0.00± 0.00      18/18
-- E3, setting d
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    129.40    129.40    +0.00± 0.00      3/3
    0.5    3    129.68    129.68    +0.00± 0.00      3/3
      1    3    125.03    125.03    +0.00± 0.00      3/3
    1.5    3    120.36    120.36    +0.00± 0.00      3/3
      2    3    117.37    117.37    +0.00± 0.00      3/3
    2.5    3    119.49    119.49    +0.00± 0.00      3/3
    all   18    123.55    123.55    +0.00± 0.00      18/18
-- E3, setting e
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    182.13    182.13    +0.00± 0.00      3/3
    0.5    3    170.25    170.25    +0.00± 0.00      3/3
      1    3    175.87    175.87    +0.00± 0.00      3/3
    1.5    3    157.73    157.73    +0.00± 0.00      3/3
      2    3    141.03    141.03    +0.00± 0.00      3/3
    2.5    3    128.01    128.01    +0.00± 0.00      3/3
    all   18    159.17    159.17    +0.00± 0.00      18/18
-- E3, setting f
   R_th    n        DQ      DQ_1           DQ-DQ_1   QoS met DQ/DQ_1
      0    3    206.20    200.15    +6.05± 1.35      3/3
    0.5    3    203.11    201.04    +2.07± 0.57      3/3
      1    3    192.84    193.29    -0.45± 2.18      3/3
    1.5    3    186.38    179.57    +6.81± 3.44      3/3
      2    3    182.96    166.07   +16.89± 2.33      3/3
    2.5    3    166.67    164.44    +2.23± 6.41      3/3
    all   18    189.69    184.09    +5.60± 1.77      18/18
-- DQ: mean served streams 11.50, group-common served 0.78, private served 9.72; BS-specific in 84/108 runs; per run, carried by a subset of the BSs: group-common 0.00, private 4.39
-- CPU per run (s): DQ 181.7, DQ_1 133.0; DQ discrete design 0.002
```

**Reading.** At Q = 50 the mean of DQ − DQ_1 is positive at every R_th from 1 to 2.5 in both scenarios (T2: +0.30,
+0.54, +1.58, +2.13; E3: +0.03, +1.09, +3.67, +0.23), ties at R_th = 0 (+0.21, +1.04) and is −1.28 ± 0.80 (T2) and
+0.20 ± 0.25 (E3) at R_th = 0.5. Only E3 at R_th = 2 (+3.67 ± 1.65) and T2 at 2.5 (+2.13 ± 1.09) are about two
standard errors from zero; **at R_th = 1–1.5 the margins are within one standard error, i.e. R1 is met in the
mean but not with statistical clarity at Q = 50.** Where the two variants differ (T2 a, e, f and E3 a, f; every run of
T2 b–d and E3 b–e is identical), single paired differences range from −11 to +17 bit/s/Hz, so three drops cannot
resolve a margin of 1–3 bit/s/Hz diluted over six settings. By setting: E3 f +5.60 ± 1.77 and T2 e +2.50 ± 2.09
(positive at R_th ≥ 1), T2 f +1.42 ± 1.48 (+5.8 ± 1.4 at R_th = 2.5), T2 a −0.45 ± 1.13 and E3 a +0.66 ± 0.86 (where
every UE already has a private stream and the group-common streams are extra streams in free slots).

### 3.2 R1 in the composition-study setting (Q = 50, `tools/rsweep.py`)

The grid has room for group-common streams after the core private streams only at S_max = 4N (and in T2 e). The
thesis's own composition study (FINDINGS.md §3: K = 16, N = 3, M = 500, S_max = 12, where J − J1 = −0.2, −0.3, +3.2,
+10.1, +21.5, +68.2 at R_th = 0 … 2.5 over 48 drops) is such a setting. DQ and DQ_1 on it, the five benchmark drops,
every R_th, Q = 50 (`python3 tools/rsweep.py DQ`, `DQ_1`; runs through `harness/grid.py`'s `run()`, records in
`results/DQ*__T2__rsweep.jsonl`):

```
===== R1 in the composition-study setting (T2, K = 16, N = 3, M = 500, S_max = 12, drops 801-805, Q = 50): 30 common runs
 R_th   n        DQ      DQ_1           DQ-DQ_1                                  per drop   QoS met
    0   5    125.19    125.01    +0.18± 2.24                   -6.2 -1.0 +2.1 -1.3 +7.4   5/5
  0.5   5    123.16    125.06    -1.90± 1.43                   -3.5 -0.6 -1.5 +2.3 -6.2   5/5
    1   5    116.89    114.54    +2.35± 2.16                   +9.5 +1.4 -4.0 +3.1 +1.6   5/5
  1.5   5     97.21     95.17    +2.03± 3.50                   +8.9 +8.4 -5.4 -7.4 +5.7   5/5
    2   5     86.08     65.40   +20.69± 1.33              +21.4 +24.8 +16.7 +21.1 +19.4   5/5
  2.5   5     75.86     24.93   +50.93±12.40              +30.9 +85.9 +33.3 +28.4 +76.1   5/3
  all  30    104.06     91.69   +12.38± 4.04                                              30/28
```

In this setting every BS carries the super-common stream, the six core private streams (the current design's), the
group-common streams and at most one other private stream, while the 1-layer counterpart gives those slots to the
private streams of the non-core users, different ones at the two BSs (up to 15 distinct private streams). From
R_th = 2 on the hierarchy wins by a wide margin (+20.7 ± 1.3 and +50.9 ± 12.4; the 1-layer counterpart misses the
QoS in two of the five drops at R_th = 2.5). At R_th = 0 the two tie (+0.2 ± 2.2); at R_th = 0.5–1.5 the mean
difference is within the run-to-run noise of Q = 50 (single paired differences from −7.4 to +9.5). Two reasons: the
noise, and the 1-layer counterpart itself: because each BS carries its own non-core private streams, DQ_1 serves up
to 15 UEs with private streams (J1 serves 11, all jointly), which carries a moderate QoS load nearly as well as the
group-common streams. For comparison, the current design over 48 drops (search T): J − J1 = +3.2 ± 0.6 at R_th = 1
and +10.1 ± 0.9 at 1.5.

### 3.3 R1 at Q = 5 (`--tier screen`, 288 runs per variant)

```
===== scenario T2, Q = 5: 144 common runs (DQ: 144, DQ_1: 144, JH: 144, J1: 144)
-- T2, all settings
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0   24    101.81    101.81    104.77    104.76    104.41    -0.00± 0.00       -2.95± 2.86      24/24/24/24/24
    0.5   24     99.42     99.60    102.52    102.51    102.16    -0.18± 0.33       -3.10± 2.71      24/24/24/24/24
      1   24     94.03     93.31     95.64     95.63     95.34    +0.71± 0.32       -1.61± 1.93      24/24/24/24/24
    1.5   24     84.09     82.05     87.23     87.23     86.94    +2.04± 0.87       -3.15± 1.05      24/24/24/24/24
      2   24     70.48     69.17     70.13     70.40     69.41    +1.31± 0.82       +0.35± 2.32      21/21/20/20/20
    2.5   24     60.68     58.19     55.88     55.88     54.42    +2.49± 1.57       +4.80± 3.24      19/19/16/16/16
    all  144     85.08     84.02     86.03     86.07     85.45    +1.06± 0.34       -0.94± 1.01      136/136/132/132/132
-- DQ: mean served streams 10.51, group-common served 1.46, private served 8.05; BS-specific in 97/144 runs; per run, carried by a subset of the BSs: group-common 0.26, private 1.50
-- J: stream-set test made in 48/144 runs, 1-layer kept in 16
-- CPU per run (s): DQ 16.3, DQ_1 7.1, J 8.0, JH 6.3, J1 4.5; DQ discrete design 0.002
===== scenario E3, Q = 5: 144 common runs (DQ: 144, DQ_1: 144, JH: 144, J1: 144)
-- E3, all settings
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0   24    126.43    126.43    128.91    128.82    128.91    -0.00± 0.00       -2.47± 2.90      24/24/24/24/24
    0.5   24    124.65    124.64    122.90    122.83    122.90    +0.01± 0.01       +1.75± 2.41      24/24/24/24/24
      1   24    121.55    121.55    113.25    113.24    113.25    -0.00± 0.41       +8.30± 2.08      24/24/24/24/24
    1.5   24    114.97    114.50    101.61    101.60    101.71    +0.47± 0.78      +13.37± 2.19      24/24/24/24/24
      2   24    109.02    108.13     83.68     83.68     83.66    +0.89± 0.93      +25.34± 4.30      24/24/20/20/20
    2.5   24     97.35     96.08     70.64     70.64     70.63    +1.27± 0.78      +26.71± 5.02      22/22/16/16/16
    all  144    115.66    115.22    103.50    103.47    103.51    +0.44± 0.25      +12.17± 1.63      142/142/132/132/132
-- DQ: mean served streams 11.62, group-common served 0.83, private served 9.79; BS-specific in 114/144 runs; per run, carried by a subset of the BSs: group-common 0.00, private 4.62
-- J: stream-set test made in 24/144 runs, 1-layer kept in 13
-- CPU per run (s): DQ 20.9, DQ_1 14.5, J 14.2, JH 9.1, J1 10.8; DQ discrete design 0.002
```

The per-setting tables of the screen are in Appendix A (`python3 tools/report.py DQ --budget 5 --by-setting`).
At Q = 5 the differences come only from the settings with room after the core private streams (T2 a, e, f; E3 a, f);
every run of T2 b, c, d and E3 b, c, d, e is an exact tie (the two variants carry the same streams). The tie in E3 at
R_th = 1 comes from one drop of E3 f (drop 904: −8.4 at R_th = 1, −11.7 at 1.5, where the 1-layer run at Q = 5 found an
unusually good deployment: its rate at R_th = 1.5 exceeds its rate at R_th = 0); the three other E3 f drops give +2.6,
+3.0 and +2.2 at R_th = 1.

### 3.4 R2 and R3 (`--tier bench`, Q = 50; `DQ@SC --tier bench`)

```
===== benchmark setting (T2, K = 16, N = 3, S_max = 12, R_th = 2, Q = 50): 15 common runs (DQ: 15, sparse_bf: 15, DQ@SC: 15, J: 15, J@SC: 15)
sparse_bf, J (the current framework) and J@SC (stream clustering on its streams): stored runs of Fig. 5.10
-- by M
      M    n        DQ sparse_bf     DQ@SC         J      J@SC      DQ-sparse_bf          DQ-DQ@SC   QoS met DQ/sparse_bf/DQ@SC/J/J@SC
    100    5     76.31     63.08     44.47     73.51     44.18   +13.23± 3.47      +31.84± 3.32      5/5/5/5/5
    300    5     86.14     75.09     57.23     81.95     54.38   +11.05± 4.02      +28.91± 3.61      5/5/5/5/5
    500    5     86.08     81.03     62.45     88.72     64.51    +5.05± 5.73      +23.63± 4.13      5/5/5/5/5
    all   15     82.84     73.07     54.72     81.39     54.36    +9.78± 2.58      +28.13± 2.18      15/15/15/15/15
-- DQ: mean served streams 12.60, group-common served 4.40, private served 7.20; BS-specific in 9/15 runs; per run, carried by a subset of the BSs: group-common 0.00, private 1.20
-- DQ: shares of the sum rate over its 15 runs meeting the QoS: super-common 14.1%, group-common 10.1%, private 75.9%
```

Per drop (M = 100 / 300 / 500), DQ: 78.3 81.3 68.5 72.5 81.0 / 89.0 88.1 77.5 82.0 94.1 / 82.5 90.6 78.9 87.6 90.8
(drops 801–805). In drops 803 and 804 the two BSs carry the same streams and DQ's runs equal J's exactly; in drops
801, 802 and 805 the BSs carry different non-core private streams. Means: DQ 76.3 / 86.1 / 86.1, J 73.5 / 82.0 / 88.7,
sparse beamforming 63.1 / 75.1 / 81.0 (DQ − sparse BF = +13.2 / +11.1 / +5.1; at M = 500 the paired margin is
+5.1 ± 5.7 because sparse beamforming reaches 97.4 in drop 801), stream clustering on DQ's streams 44.5 / 57.2 / 62.5
(19 streams on average; on J's streams 44.2 / 54.4 / 64.5). DQ is 1.5 above J over the 15 runs (82.8 vs 81.4): above
at M = 100 and 300, below at M = 500.

### 3.5 R4 (`--tier smax`, Q = 50)

```
===== sum rate versus S_max (T2, N = 3, M = 300, Q = 50): 126 runs of DQ
-- K = 8: mean sum rate over the drops (QoS met / runs)
  R_th          S=4          S=6          S=8         S=10         S=12         S=14         S=16
     0   77.83  2/2   101.66  2/2   100.67  2/2   101.96  2/2   101.55  2/2   101.55  2/2   101.55  2/2 
     1   77.07  2/2    97.24  2/2    98.75  2/2    96.02  2/2    96.12  2/2    96.12  2/2    96.12  2/2 
     2   65.22  2/2    90.46  2/2    92.66  2/2    94.36  2/2   100.52  2/2   100.52  2/2   100.52  2/2 
   all   73.38  6/6    96.45  6/6    97.36  6/6    97.45  6/6    99.40  6/6    99.40  6/6    99.40  6/6 
   change to the next S_max (paired over R_th and drops): 4->6 +23.08±1.00, 6->8 +0.91±0.85, 8->10 +0.09±2.20, 10->12 +1.95±4.48, 12->14 +0.00±0.00, 14->16 +0.00±0.00
-- K = 12: mean sum rate over the drops (QoS met / runs)
  R_th          S=4          S=6          S=8         S=10         S=12         S=14         S=16
     0   76.07  2/2   104.33  2/2   122.90  2/2   122.35  2/2   122.46  2/2   121.53  2/2   121.46  2/2 
     1   66.74  2/2    96.88  2/2   116.07  2/2   118.51  2/2   116.68  2/2   117.50  2/2   117.39  2/2 
     2   62.83  2/2    82.11  2/2    96.83  2/2   104.32  2/2   102.03  2/2   111.68  2/2   110.73  2/2 
   all   68.55  6/6    94.44  6/6   111.93  6/6   115.06  6/6   113.72  6/6   116.90  6/6   116.53  6/6 
   change to the next S_max (paired over R_th and drops): 4->6 +25.89±4.38, 6->8 +17.49±5.65, 8->10 +3.13±1.87, 10->12 -1.34±0.58, 12->14 +3.18±2.37, 14->16 -0.37±0.64
-- K = 16: mean sum rate over the drops (QoS met / runs)
  R_th          S=4          S=6          S=8         S=10         S=12         S=14         S=16
     0   73.34  2/2    82.43  2/2   123.32  2/2   122.97  2/2   121.61  2/2   122.01  2/2   122.60  2/2 
     1   66.66  2/2    80.67  2/2   112.45  2/2   109.53  2/2   115.07  2/2   114.67  2/2   115.95  2/2 
     2   43.12  2/2    55.44  2/2    72.46  2/2    75.65  2/2    92.66  2/2    86.02  2/2    88.05  2/2 
   all   61.04  6/6    72.84  6/6   102.74  6/6   102.72  6/6   109.78  6/6   107.56  6/6   108.87  6/6 
   change to the next S_max (paired over R_th and drops): 4->6 +11.81±3.26, 6->8 +29.90±4.62, 8->10 -0.03±1.25, 10->12 +7.06±4.25, 12->14 -2.22±1.87, 14->16 +1.30±1.20
```

The sum rate rises with S_max and flattens out once every BS carries the core private streams and the group-common
streams (from S_max = 6 for K = 8, 10 for K = 12 and 12 for K = 16). The steps along the plateau are within ±2.3 bit/s/Hz:
the largest decreases are −1.34 ± 0.58 (K = 12, S_max 10 → 12) and −2.22 ± 1.87 (K = 16, 12 → 14). The stream
set of every BS is nested in S_max (§2), so a larger S_max only adds streams (on the plateau: private streams of
non-core users); the small decreases are differences of the search and the AO with the added streams, not of the
design. (For reference, the thesis figure, Fig. 5.5, has the current design at
S_max = 4 / 6 / 12 only.)

### 3.6 Where the BSs carry different streams

From the report lines "BS-specific in …": in the Q = 5 screen, DQ's BSs carry different streams in 97 of 144 runs in
T2 and 114 of 144 in E3; per run, on average 1.50 (T2) and 4.62 (E3) private streams and 0.26 (T2) group-common
streams are carried by a subset of the BSs. Different private streams: T2 b, c, d, e, f, E3 b–f (core private streams
in the settings with S_max = N + 1 and 2N, non-core private streams in e and f); different group-common streams: T2 e
(each BS carries the group-common stream whose weakest member it reaches best, one slot each); in the benchmark
setting: 9 of 15 runs (non-core private streams). In the Q = 50 confirm runs: BS-specific in 73 of 108 runs (T2)
and 84 of 108 (E3); per run 1.67 (T2) and 4.39 (E3) private streams and 0.24 (T2) group-common streams are carried by
a subset of the BSs.

### 3.7 Cost

* **The discrete design:** 1.5–2.6 ms per drop (`cpu_design`; SUS, at most min(K, BN) ZF sum rates, B sorts).
* **The runs (search R, Q = 50, and the refinement)**, CPU-s per run in the confirm tier (mean over drops and R_th) and
  the mean number of distinct served streams:

| scen | setting | DQ (CPU-s) | DQ_1 (CPU-s) | DQ streams | DQ_1 streams |
|---|---|---|---|---|---|
| T2 | a | 43 | 22 | 11.7 | 9.0 |
| T2 | b | 32 | 32 | 6.3 | 6.3 |
| T2 | c | 51 | 50 | 7.0 | 7.0 |
| T2 | d | 37 | 37 | 6.7 | 6.7 |
| T2 | e | 201 | 133 | 10.7 | 11.3 |
| T2 | f | 601 | 136 | 21.0 | 17.0 |
| T2 | all | 161 | 68 | 10.6 | 9.5 |
| E3 | a | 53 | 40 | 9.7 | 9.0 |
| E3 | b | 69 | 67 | 8.0 | 8.0 |
| E3 | c | 117 | 113 | 9.0 | 9.0 |
| E3 | d | 127 | 123 | 10.0 | 10.0 |
| E3 | e | 177 | 171 | 11.7 | 11.7 |
| E3 | f | 547 | 286 | 20.7 | 17.0 |
| E3 | all | 182 | 133 | 11.5 | 10.8 |

  Where the BSs carry the same streams or the HRS adds nothing, DQ costs what DQ_1 costs. In setting f the BSs carry
  the core private streams, 3–5 group-common streams and different non-core private streams (about 21 distinct
  streams, BS-specific), and a run costs 550–600 CPU-s, about twice the current design's (about 300 CPU-s, FINDINGS.md
  §7) and about 4 (T2) and 2 (E3) times its own 1-layer counterpart's. Over the grid: 161 (T2) and 182 (E3) CPU-s per run, against about
  110 for the current design (README: 6.8 CPU-h for 216 runs).
* **Benchmark setting** (15 runs): DQ 129 CPU-s per run (J 102, sparse beamforming 85); stream clustering on DQ's
  streams 383 (on J's 328). S_max tier: 69 CPU-s per run. Q = 5 screen: 16.3 (T2) and 20.9 (E3) CPU-s per run (JH 6.3
  and 9.1).
* **This round in total:** about 25 CPU-hours for the runs of DQ, DQ_1 and DQ@SC, plus the screens of the other
  methods (§4).

## 4. Other methods tried

Same harness and grid; Q = 5; "R1": the variant minus its own 1-layer counterpart at R_th = 0, 0.5, 1, 1.5, 2, 2.5
(paired, common runs); "vs JH": the variant minus JH; bench: Q = 5, drops 801–802, M ∈ {100, 300, 500} (JH 68.8,
DQ 69.9). Full: all 288 runs of the screen; subsets: the settings and R_th listed. Every BS-specific variant uses the
same AO start switch (§1.10).

| Variant | Idea | R1 T2 | R1 E3 | vs JH | Bench Q5 | Why not |
|---|---|---|---|---|---|---|
| D1s (full) | per-BS ranking as DQ, with the current core users (min(K, BN)) | +0.35 +0.35 +0.28 +0.28 +0.99 +1.45 | −0.08 −0.07 −0.01 −0.11 +0.01 +0.01 | T2 −13.9 … +5.9, E3 −14.1 … +24.1 | 69.9 | E3 ties at every R_th: every UE is a core user in E3 a, d; one group of two in e, f |
| D2s (full) | every BS selects its own N core users by SUS on its own antennas (union; shared when selected by several); own cores, other cores, groups, others | +0.01 +0.04 +0.31 +1.05 +0.63 +1.64 | +0.00 +0.03 +0.31 +1.11 +2.25 +0.83 | T2 −8.5 … +5.2, E3 −8.2 … +25.1 | 61.1 | R2: Q = 50, M = 100, 5 drops: 65.4 vs sparse BF 63.1 (J 73.5); the BSs' own selections overlap (4 core users in drops 801, 803) or differ from the network's best (802, 805) |
| DRs (full) | each core user on its ⌈|C|/N⌉ strongest BSs (ZF degrees of freedom), per-BS extras, QoS-feasibility promotion of group-common streams | +0.35 +0.35 +0.28 +0.28 +0.99 +4.17 | −0.08 −0.07 −0.01 −0.11 +3.09 +6.26 | T2 0 … +2.7, E3 0 … +6.2 | — | E3 ties at R_th ≤ 1.5; ⌈|C|/N⌉ = B for min(K, BN) core users, i.e. joint transmission in any network |
| D3s (b, c, f; R_th 0, 1, 2) | core users in SUS order at every BS (joint), per-BS extras | +1.12 · +1.12 · +1.09 · | −0.33 · −0.02 · +0.04 · | 0 | — | the current design at small S_max; joint transmission in any network |
| D4s (b, c, f; 0, 1, 2) | home BS first: home cores, home groups, other cores, other groups, others | −2.99 · −1.12 · +4.81 · | −0.24 · −1.00 · +1.95 · | T2 −15.3 … +14.1 | 69.9 | R1 negative at R_th = 0 and 1 |
| D5s (b, c, f; 0, 1, 2) | coverage first: home cores, home groups, home others, then the others | +1.12 · +0.29 · +8.80 · | −0.52 · −0.63 · +1.42 · | T2 −17.4 … +14.6 | 27.7 | R1 negative in E3; QoS failures at the benchmark |
| DMs (b–e; 0, 1, 2) | n core private streams, each on its ⌈n/N⌉ strongest BSs, n the largest the fronthaul admits | +2.85 · +1.71 · +0.54 · | +6.32 · +3.46 · −1.76 · | T2 −9.9 … +1.2, E3 −12.1 … +22.9 | — | zero-margin ZF: −44 (E3 e) and −28 (T2 d) vs JH at R_th = 0 |
| D3z (a, e, f; 0, 1, 2, 2.5) | greedy ZF user selection (order and count), joint core users, per-BS extras | +0.00 · +0.76 · −0.05 +5.63 | +0.00 · +1.29 · +2.04 +1.39 | T2 +6.2 … +1.0, E3 +6.0 … −2.1 | 60.9 | R2: too few core users at the benchmark (4–5) and a different choice; JZ (the joint design with greedy-ZF core users): 61.5 |
| DH (a, f; full R_th) | network core users, groups around the BSs' own SUS selections (groups whose members all have private streams) | +1.63 +1.62 +1.63 +0.02 +0.65 +2.98 | +1.05 +1.19 +1.86 +3.22 +8.41 +1.67 | T2 +0.2 … +2.2, E3 +1.5 … +1.7 | 47.3 (one QoS failure) | R2: every member of such a group decodes the group-common stream before its private stream |
| DZ (bench only) | DQ without the QoS floor | — | — | — | 62.1 | drop 802: 5 core users, 49.1 / 63.0 / 63.8 instead of 69.1 / 81.9 / 71.9 |
| JTg1, JTg2 (b–e, single drops) | the current design with the last 1 or 2 core private streams replaced by the largest group-common streams | — | — | R_th 0: −23 (T2 b), −16 (T2 d), −14 (E3 b), −21 (E3 c); R_th 1.5–2: +2 … +9 | — | a group-common stream is worth a core private stream only at high QoS load |
| D2n (bench only) | D2s without the private streams of non-core UEs | — | — | — | 35.8 (QoS failures) | — |

("·": R_th not run in that subset.) A screen of D1s with the QoS-feasibility promotion of DRs (D1p) was started and
stopped when DQ was found; it has no results.

What these runs established:

* Any design that serves the core private streams before the group-common streams ties its 1-layer counterpart
  wherever the core private streams fill the fronthaul (S_max = N + 1 and 2N in the grid). R1 can only come from the
  settings with room after them.
* With the current min(K, BN) core users there is no such room for groups in E3 (every UE is a core user in E3 a and
  d; one group of two in e and f), so every design built on them ties its 1-layer counterpart in E3 (D1s, DRs, D3s,
  JH). The number of core users had to follow the channels; D2s (the BSs' own selections) and D3z (greedy ZF) do, but
  both choose fewer or different core users at the benchmark and lose there. The SUS order with the ZF stopping rule
  keeps the current core users at the benchmark and fewer where K ≈ BN.
* Groups must keep one private-served member each (DH).
* At small S_max, BS-specific core private streams lose to joint transmission at low R_th in T2 (interference-limited,
  as §4.1 of the thesis states) and win at high R_th, much more so in E3 (D1s: −14 at R_th = 0, +24 at 2.5 in E3).

## 5. Weak points

* **R1 is not clear at R_th = 1–1.5 (the main weak point).** Three causes. (i) The design ties its 1-layer
  counterpart exactly wherever the core private streams fill the fronthaul: T2 b, c, d and E3 b, c, d, e (7 of the 12
  scenario-settings); all of R1 comes from T2 a, e, f and E3 a, f. (ii) There, the 1-layer counterpart is a strong
  competitor at a moderate QoS load: each BS gives the slots to the private streams of the non-core users it reaches
  best, different ones at different BSs, so DQ_1 serves more UEs with private streams than a joint 1-layer design
  (composition-study setting: up to 15 instead of 11), and these carry R_th = 1–1.5 almost as well as the
  group-common streams; from R_th = 2 on they do not (+20.7 and +50.9 there). (iii) At Q = 50 single paired runs differ
  by −11 … +17 bit/s/Hz, and three drops cannot resolve a margin of 1–3 diluted over six settings. A design that would
  also gain in the small-S_max settings has to give group-common streams slots that the core private streams hold;
  every such rule I tried either loses at R_th = 0 (D4s, JTg1/JTg2) or needs a rate model of the AO outcome (§4).
  Dropping the private streams of the non-core users from the design would widen the gap by taking them from the
  1-layer counterpart too (not run), but they carry 5–9 bit/s/Hz in settings a and f at Q = 50, so I did not weaken
  the design to strengthen the comparison.
* **R_th = 0.5 in T2.** −1.28 ± 0.80 at Q = 50 (−0.18 ± 0.33 at Q = 5; −1.90 ± 1.43 in the composition-study
  setting): at a low QoS load the group-common streams are worth a little less than the private streams of the
  non-core users whose slots they take.
* **Low R_th at tight fronthaul in T2.** With S_max = N + 1 or 2N, the BSs carry different core private streams, which
  are interference-limited when every BS reaches every UE: at Q = 5, DQ − J = −12.4 (T2 b), −20.0 (T2 c), −7.1 (T2 d)
  at R_th = 0, and −10.9 (E3 e) at R_th = 0. From R_th ≈ 1.5 on, the same association is far better than joint
  transmission (E3 b–d: +17 … +48 at R_th 1.5–2.5), because more UEs have private streams. This is the trade-off
  the thesis states in §4.1 for BS-specific associations; the design accepts it because the request is a design in
  which each BS has its own stream set.
* **Fewer core users can cost where every UE could have a beam.** In T2 a (K = 8, BN = 6) the ZF rule keeps 4–5 core
  users: the AO starts with fewer ZF beams and DQ is 4.6 below J at Q = 5 (all eight private streams are still
  carried).
* **Group-common streams on one BS.** When one slot is left per BS (T2 e), each BS carries the group-common stream
  whose weakest member it reaches best, so each group-common stream is carried by one BS only (5 antennas). At Q = 5
  this lost at R_th = 2.5 (−2.4 ± 4.7); at Q = 50 T2 e is one of the settings with gains (+2.5 ± 2.1 over R_th,
  +6.8 ± 4.3 at R_th = 2.5).
* **Large fronthaul in a large network.** The class order comes first: when S_max − 1 ≥ |C|, every BS carries every
  core private stream, also the far ones, before any group-common stream. With S_max per BS and |C| growing with
  the area this does not happen in a large network (9 BSs on 600 m: only at S_max = 28, §1.9), but a mid-size network
  with a large fronthaul would use slots for far core users.
* **The QoS floor is only a necessary condition** (C_0 is an upper bound on the super-common rate). It does not
  guarantee feasibility; in the Q = 5 screen DQ misses the QoS in 8 of 144 T2 runs (T2 b at 2.5, T2 c at 2–2.5) and 2 of
  144 E3 runs (E3 c at 2.5), J in 12 of 144 in each scenario.
* **Cost.** The BSs carry more distinct streams, so the AO costs more per evaluation (§3.7).
* **The AO start switch.** BS-specific stream sets use a start computed on the carrying antennas (§1.10). It is a
  change of the evaluator's start, off by default, applied to every run of DQ, DQ_1 and DQ@SC; its measured effect is
  small.

## 6. Choices made without asking

* **Kept from the current design:** the SUS order (the user allowed keeping it), nearest-core groups, the class order
  of the streams, the per-run framework (search R, Q = 50, refinement) and the AO as it is (one start switch, §1.10).
* **The ZF stopping rule uses equal power** B·P_max/|C| per beam on the direct channels (the standard form of greedy ZF
  user selection); the DS-STARs are not known before the search.
* **The floor uses C_0**, the coherent single-stream bound, because it needs no optimization; it is an upper bound,
  so the floor is conservative.
* **Per-BS ranking by the direct-channel gain** (the weakest member's gain for a group-common stream): the simplest
  local quantity; no association threshold.
* **Ties** in a BS's sort (equal gains, which do not occur with continuous positions) keep the SUS order for core users
  and groups and the UE index for the other UEs (stable sorts), so the design is deterministic.
* **Variant names.** `DQ`, `DQ_1` are the prototype names under which the screen ran; after the screen the design was
  moved to `code/bsdesign.py` and the entries now point there. `tools/verify_bsdesign.py` checks that both give the
  same designs on all 858 configurations of the screen, confirm, bench and smax tiers (they do), so the earlier runs
  (screen, Q = 5 bench check, Q = 50 bench of DQ and DQ@SC, which started before the switch) are runs of the same
  design. In configurations outside the tiers, `bsdesign.py` adds two guards that the prototype lacks (no group of
  all K UEs when only one core user is kept; linearly dependent channels end the ZF rule).
* **JH and J1 were not run at Q = 50.** The README makes them optional; the confirm and smax tiers of DQ took the
  compute (DQ's runs of setting f cost 650–900 CPU-s each at Q = 50). The reference to J is the Q = 5 screen (JH, J1
  on all 288 runs) and the stored benchmark runs (Q = 50).
* **The 1-layer counterpart** is a variant of its own (`DQ_1`, `one_layer` of `DQ`): the same lists without
  group-common streams.

## 7. Files

* `DESIGN.md` — this file.
* `code/bsdesign.py` — the design and its 1-layer counterpart (`design`, `design_1layer`).
* `code/algo.py` — `init_core_support` and the seed `rule_s` (the AO start switch, off by default).
* `code/bsd.py` — every prototype of §4 (D1s … DQ), kept for reproducibility.
* `harness/variants.py` — `DQ`, `DQ_1` (the design) and the entries of the prototypes.
* `tools/verify_bsdesign.py`, `tools/design_structure.py`, `tools/large_area.py`, `tools/stress_bsdesign.py` — the
  checks and tables of §1.8, §1.9 and §6; `tools/rsweep.py` — the runs and the report of §3.2 (`results/*__T2__rsweep.jsonl`,
  `results/DQ__report_rsweep.json`).
* `results/*.jsonl` — every run (harness format, unedited): the design (`DQ`, `DQ_1`, `DQ@SC`), the references
  (`JH`, `J1`), and the prototypes; `results/*report*.json` — the reports of `tools/report.py --json` (`DQ__report.json`:
  confirm, `DQ__report_Q5.json`: screen, `DQ__report_bench.json`, `DQ__report_smax.json`, `DQ__report_rsweep.json`;
  `D1s`, `D2s`, `DRs`: the screens of §4).
* `design_return_cloud_max.diff` — unified diff (`diff -ruN`) against the package as delivered.
* `logs/` — the logs of the background jobs.

## Appendix A. R1 at Q = 5 by setting (`python3 tools/report.py DQ --budget 5 --by-setting`)

```
===== scenario T2, Q = 5: 144 common runs (DQ: 144, DQ_1: 144, JH: 144, J1: 144)
-- T2, all settings
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0   24    101.81    101.81    104.77    104.76    104.41    -0.00± 0.00       -2.95± 2.86      24/24/24/24/24
    0.5   24     99.42     99.60    102.52    102.51    102.16    -0.18± 0.33       -3.10± 2.71      24/24/24/24/24
      1   24     94.03     93.31     95.64     95.63     95.34    +0.71± 0.32       -1.61± 1.93      24/24/24/24/24
    1.5   24     84.09     82.05     87.23     87.23     86.94    +2.04± 0.87       -3.15± 1.05      24/24/24/24/24
      2   24     70.48     69.17     70.13     70.40     69.41    +1.31± 0.82       +0.35± 2.32      21/21/20/20/20
    2.5   24     60.68     58.19     55.88     55.88     54.42    +2.49± 1.57       +4.80± 3.24      19/19/16/16/16
    all  144     85.08     84.02     86.03     86.07     85.45    +1.06± 0.34       -0.94± 1.01      136/136/132/132/132
-- T2, setting a
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4     90.98     90.98     93.82     93.82     93.81    -0.00± 0.00       -2.83± 3.33      4/4/4/4/4
    0.5    4     90.50     90.40     93.82     93.82     93.81    +0.09± 0.09       -3.32± 3.54      4/4/4/4/4
      1    4     88.44     87.91     93.82     93.82     93.81    +0.53± 0.48       -5.38± 3.55      4/4/4/4/4
    1.5    4     85.62     84.32     93.82     93.82     93.81    +1.29± 0.50       -8.20± 3.43      4/4/4/4/4
      2    4     89.71     87.63     93.81     93.81     93.81    +2.08± 0.54       -4.10± 2.28      4/4/4/4/4
    2.5    4     90.05     88.57     93.56     93.56     93.56    +1.48± 0.42       -3.51± 3.56      4/4/4/4/4
    all   24     89.22     88.30     93.77     93.77     93.77    +0.91± 0.21       -4.56± 1.25      24/24/24/24/24
-- T2, setting b
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4     61.08     61.08     73.49     73.49     73.49    +0.00± 0.00      -12.41± 0.55      4/4/4/4/4
    0.5    4     60.29     60.29     67.64     67.64     67.64    +0.00± 0.00       -7.35± 1.01      4/4/4/4/4
      1    4     57.55     57.55     59.67     59.67     59.67    +0.00± 0.00       -2.12± 1.08      4/4/4/4/4
    1.5    4     50.47     50.47     50.97     50.97     50.97    +0.00± 0.00       -0.50± 1.07      4/4/4/4/4
      2    4     47.74     47.74     42.45     42.45     42.45    +0.00± 0.00       +5.29± 1.44      4/4/4/4/4
    2.5    4     31.70     31.70      0.00      0.00      0.00    +0.00± 0.00      +31.70±10.67      3/3/0/0/0
    all   24     51.47     51.47     49.04     49.04     49.04    +0.00± 0.00       +2.44± 3.37      23/23/20/20/20
-- T2, setting c
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4     76.67     76.67     96.70     96.70     96.70    +0.00± 0.00      -20.03± 3.05      4/4/4/4/4
    0.5    4     72.15     72.15     93.91     93.91     93.91    +0.00± 0.00      -21.76± 4.22      4/4/4/4/4
      1    4     65.22     65.22     79.27     79.27     79.27    +0.00± 0.00      -14.05± 1.22      4/4/4/4/4
    1.5    4     53.04     53.04     58.57     58.57     58.57    +0.00± 0.00       -5.52± 1.60      4/4/4/4/4
      2    4     10.28     10.28      0.00      0.00      0.00    +0.00± 0.00      +10.28±10.28      1/1/0/0/0
    2.5    4      0.00      0.00      0.00      0.00      0.00    +0.00± 0.00       +0.00± 0.00      0/0/0/0/0
    all   24     46.23     46.23     54.74     54.74     54.74    +0.00± 0.00       -8.51± 2.93      17/17/16/16/16
-- T2, setting d
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4    106.29    106.29    113.38    113.38    113.38    +0.00± 0.00       -7.09± 4.15      4/4/4/4/4
    0.5    4    103.62    103.62    109.01    109.01    109.01    +0.00± 0.00       -5.38± 3.27      4/4/4/4/4
      1    4     96.06     96.06     99.85     99.85     99.85    +0.00± 0.00       -3.79± 2.86      4/4/4/4/4
    1.5    4     87.23     87.23     88.14     88.14     88.14    +0.00± 0.00       -0.91± 2.34      4/4/4/4/4
      2    4     77.94     77.94     74.76     74.76     74.76    +0.00± 0.00       +3.18± 4.07      4/4/4/4/4
    2.5    4     65.92     65.92     60.94     60.94     60.94    +0.00± 0.00       +4.98± 3.82      4/4/4/4/4
    all   24     89.51     89.51     91.01     91.01     91.01    +0.00± 0.00       -1.50± 1.56      24/24/24/24/24
-- T2, setting e
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4    138.98    138.98    133.91    133.91    133.91    -0.00± 0.00       +5.07± 2.03      4/4/4/4/4
    0.5    4    136.68    136.46    133.43    133.43    133.43    +0.22± 0.22       +3.25± 3.22      4/4/4/4/4
      1    4    130.43    128.78    124.60    124.60    124.60    +1.66± 1.64       +5.84± 1.81      4/4/4/4/4
    1.5    4    114.09    111.24    116.82    116.82    116.82    +2.85± 2.89       -2.73± 2.10      4/4/4/4/4
      2    4     94.92     92.42    101.53    101.53    101.53    +2.49± 3.95       -6.61± 3.39      4/4/4/4/4
    2.5    4     74.00     76.39     80.51     80.51     80.51    -2.39± 4.65       -6.51± 3.75      4/4/4/4/4
    all   24    114.85    114.04    115.13    115.13    115.13    +0.81± 1.09       -0.28± 1.49      24/24/24/24/24
-- T2, setting f
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4    136.86    136.86    117.30    117.27    115.16    -0.00± 0.00      +19.56± 3.14      4/4/4/4/4
    0.5    4    133.29    134.71    117.30    117.27    115.16    -1.41± 2.07      +15.99± 5.10      4/4/4/4/4
      1    4    126.46    124.36    116.61    116.58    114.85    +2.10± 0.46       +9.85± 4.97      4/4/4/4/4
    1.5    4    114.08    105.99    115.09    115.08    113.33    +8.09± 3.07       -1.01± 3.02      4/4/4/4/4
      2    4    102.28     99.01    108.19    109.85    103.91    +3.26± 3.35       -5.92± 5.26      4/4/4/4/4
    2.5    4    102.41     86.55    100.26    100.26     91.50   +15.86± 4.11       +2.15± 3.27      4/4/4/4/4
    all   24    119.23    114.58    112.46    112.72    108.99    +4.65± 1.55       +6.77± 2.45      24/24/24/24/24
-- DQ: mean served streams 10.51, group-common served 1.46, private served 8.05; BS-specific in 97/144 runs; per run, carried by a subset of the BSs: group-common 0.26, private 1.50
-- J: stream-set test made in 48/144 runs, 1-layer kept in 16
-- CPU per run (s): DQ 16.3, DQ_1 7.1, J 8.0, JH 6.3, J1 4.5; DQ discrete design 0.002

===== scenario E3, Q = 5: 144 common runs (DQ: 144, DQ_1: 144, JH: 144, J1: 144)
-- E3, all settings
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0   24    126.43    126.43    128.91    128.82    128.91    -0.00± 0.00       -2.47± 2.90      24/24/24/24/24
    0.5   24    124.65    124.64    122.90    122.83    122.90    +0.01± 0.01       +1.75± 2.41      24/24/24/24/24
      1   24    121.55    121.55    113.25    113.24    113.25    -0.00± 0.41       +8.30± 2.08      24/24/24/24/24
    1.5   24    114.97    114.50    101.61    101.60    101.71    +0.47± 0.78      +13.37± 2.19      24/24/24/24/24
      2   24    109.02    108.13     83.68     83.68     83.66    +0.89± 0.93      +25.34± 4.30      24/24/20/20/20
    2.5   24     97.35     96.08     70.64     70.64     70.63    +1.27± 0.78      +26.71± 5.02      22/22/16/16/16
    all  144    115.66    115.22    103.50    103.47    103.51    +0.44± 0.25      +12.17± 1.63      142/142/132/132/132
-- E3, setting a
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4    126.72    126.72    125.65    125.65    125.65    -0.00± 0.00       +1.07± 0.51      4/4/4/4/4
    0.5    4    126.70    126.66    125.56    125.56    125.56    +0.04± 0.05       +1.15± 0.54      4/4/4/4/4
      1    4    126.66    126.52    125.42    125.42    125.42    +0.14± 0.13       +1.24± 0.59      4/4/4/4/4
    1.5    4    126.38    126.16    125.25    125.25    125.25    +0.22± 0.22       +1.13± 0.66      4/4/4/4/4
      2    4    125.84    125.50    125.04    125.04    125.04    +0.34± 0.34       +0.81± 1.02      4/4/4/4/4
    2.5    4    125.36    124.86    125.14    125.14    125.14    +0.50± 0.50       +0.22± 2.89      4/4/4/4/4
    all   24    126.28    126.07    125.34    125.34    125.34    +0.21± 0.10       +0.93± 0.49      24/24/24/24/24
-- E3, setting b
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4     71.24     71.24     72.05     72.05     72.05    +0.00± 0.00       -0.81± 3.18      4/4/4/4/4
    0.5    4     69.48     69.48     64.42     64.42     64.42    +0.00± 0.00       +5.05± 2.81      4/4/4/4/4
      1    4     69.53     69.53     55.60     55.60     55.60    +0.00± 0.00      +13.94± 4.03      4/4/4/4/4
    1.5    4     63.58     63.58     46.85     46.85     46.85    +0.00± 0.00      +16.74± 3.48      4/4/4/4/4
      2    4     62.37     62.37     38.17     38.17     38.17    +0.00± 0.00      +24.20± 1.47      4/4/4/4/4
    2.5    4     58.42     58.42      0.00      0.00      0.00    +0.00± 0.00      +58.42± 1.49      4/4/0/0/0
    all   24     65.77     65.77     46.18     46.18     46.18    +0.00± 0.00      +19.59± 4.13      24/24/20/20/20
-- E3, setting c
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4     93.09     93.09    113.87    113.87    113.87    +0.00± 0.00      -20.78± 6.98      4/4/4/4/4
    0.5    4     89.38     89.38     97.36     97.36     97.36    +0.00± 0.00       -7.98± 6.36      4/4/4/4/4
      1    4     86.61     86.61     76.29     76.29     76.29    +0.00± 0.00      +10.32± 2.93      4/4/4/4/4
    1.5    4     73.42     73.42     54.52     54.52     54.52    +0.00± 0.00      +18.89± 3.46      4/4/4/4/4
      2    4     61.04     61.04      0.00      0.00      0.00    +0.00± 0.00      +61.04± 2.33      4/4/0/0/0
    2.5    4     22.36     22.36      0.00      0.00      0.00    +0.00± 0.00      +22.36±12.96      2/2/0/0/0
    all   24     70.98     70.98     57.01     57.01     57.01    +0.00± 0.00      +13.98± 5.94      22/22/16/16/16
-- E3, setting d
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4    115.51    115.51    115.43    115.43    115.43    +0.00± 0.00       +0.08± 3.96      4/4/4/4/4
    0.5    4    115.11    115.11    109.73    109.73    109.73    +0.00± 0.00       +5.38± 4.25      4/4/4/4/4
      1    4    112.13    112.13     99.18     99.18     99.18    +0.00± 0.00      +12.95± 3.74      4/4/4/4/4
    1.5    4    110.03    110.03     86.12     86.12     86.12    +0.00± 0.00      +23.91± 4.24      4/4/4/4/4
      2    4    108.55    108.55     72.35     72.35     72.35    +0.00± 0.00      +36.20± 4.75      4/4/4/4/4
    2.5    4    106.64    106.64     58.64     58.64     58.64    +0.00± 0.00      +48.00± 4.94      4/4/4/4/4
    all   24    111.33    111.33     90.24     90.24     90.24    +0.00± 0.00      +21.09± 3.86      24/24/24/24/24
-- E3, setting e
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4    168.51    168.51    179.41    179.41    179.41    +0.00± 0.00      -10.90± 1.92      4/4/4/4/4
    0.5    4    164.89    164.89    173.48    173.48    173.48    +0.00± 0.00       -8.59± 3.61      4/4/4/4/4
      1    4    156.38    156.38    157.45    157.45    157.45    +0.00± 0.00       -1.07± 5.76      4/4/4/4/4
    1.5    4    144.87    144.87    135.06    135.06    135.06    +0.00± 0.00       +9.81± 4.98      4/4/4/4/4
      2    4    131.18    131.18    110.21    110.21    110.21    +0.00± 0.00      +20.97± 5.29      4/4/4/4/4
    2.5    4    112.99    112.99     84.76     84.76     84.76    +0.00± 0.00      +28.23± 5.70      4/4/4/4/4
    all   24    146.47    146.47    140.06    140.06    140.06    +0.00± 0.00       +6.41± 3.50      24/24/24/24/24
-- E3, setting f
   R_th    n        DQ      DQ_1         J        JH        J1           DQ-DQ_1              DQ-J   QoS met DQ/DQ_1/J/JH/J1
      0    4    183.53    183.53    167.03    166.53    167.04    -0.00± 0.00      +16.50± 6.71      4/4/4/4/4
    0.5    4    182.34    182.31    166.86    166.43    166.87    +0.02± 0.01      +15.48± 7.09      4/4/4/4/4
      1    4    177.98    178.14    165.53    165.51    165.54    -0.17± 2.76      +12.44± 7.52      4/4/4/4/4
    1.5    4    171.56    168.96    161.85    161.82    162.46    +2.60± 5.10       +9.72± 6.56      4/4/4/4/4
      2    4    165.13    160.15    156.28    156.28    156.22    +4.98± 5.77       +8.84± 5.42      4/4/4/4/4
    2.5    4    158.33    151.21    155.32    155.32    155.25    +7.12± 3.75       +3.01± 3.36      4/4/4/4/4
    all   24    173.14    170.72    162.15    161.98    162.23    +2.43± 1.45      +11.00± 2.45      24/24/24/24/24
-- DQ: mean served streams 11.62, group-common served 0.83, private served 9.79; BS-specific in 114/144 runs; per run, carried by a subset of the BSs: group-common 0.00, private 4.62
-- J: stream-set test made in 24/144 runs, 1-layer kept in 13
-- CPU per run (s): DQ 20.9, DQ_1 14.5, J 14.2, JH 9.1, J1 10.8; DQ discrete design 0.002
```
