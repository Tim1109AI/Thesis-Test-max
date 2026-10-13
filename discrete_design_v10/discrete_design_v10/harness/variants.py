"""Discrete-design variants for the harness: name -> entry.

Entry keys:
  design      'module:function' in code/ ; the function design(net, p) -> hrs.Design (see code/discrete.py)
  one_layer   the name of the variant that is this design's 1-layer RSMA counterpart (requirement R1 of BRIEF.md)
  opt         (optional) dict of options passed to discrete.run (keys of newprop.NEW); leave it out unless your design
              needs a changed evaluation, and then explain why in DESIGN.md
Use a new name instead of editing a variant that already has results.
KEY@SC (no entry needed; harness/grid.py and tools/report.py) is the stream-clustering benchmark (code/benchmarks.py)
on the streams of KEY's design.

The baselines (the current thesis):
  JH   current design (joint transmission, HRS order)           discrete.current
  J1   its 1-layer RSMA (group-common streams removed)          discrete.current_1layer
  J    the thesis framework = JH or J1 by the stream-set test at the initial design of the search; derived by
       tools/report.py from the runs of JH and J1 (not run separately)
"""

VARIANTS = {
    'JH': dict(design='discrete:current', one_layer='J1'),
    'J1': dict(design='discrete:current_1layer'),
}

# ---- design round v10, BS-specific prototypes (bsd.py); suffix 's': support-aware AO start (algo.init_core_support)
SUPPORT_START = dict(init='core_s', seed='rule_s')
VARIANTS.update({
    'D1': dict(design='bsd:d1', one_layer='D1_1'), 'D1_1': dict(design='bsd:d1_1'),
    'D1s': dict(design='bsd:d1', one_layer='D1s_1', opt=SUPPORT_START), 'D1s_1': dict(design='bsd:d1_1', opt=SUPPORT_START),
    'D2s': dict(design='bsd:d2', one_layer='D2s_1', opt=SUPPORT_START), 'D2s_1': dict(design='bsd:d2_1', opt=SUPPORT_START),
    'D3s': dict(design='bsd:d3', one_layer='D3s_1', opt=SUPPORT_START), 'D3s_1': dict(design='bsd:d3_1', opt=SUPPORT_START),
})
VARIANTS.update({
    'D4s': dict(design='bsd:d4', one_layer='D4s_1', opt=SUPPORT_START), 'D4s_1': dict(design='bsd:d4_1', opt=SUPPORT_START),
    'D5s': dict(design='bsd:d5', one_layer='D5s_1', opt=SUPPORT_START), 'D5s_1': dict(design='bsd:d5_1', opt=SUPPORT_START),
})
VARIANTS.update({'JTg1': dict(design='bsd:jt_swap1'), 'JTg2': dict(design='bsd:jt_swap2')})
VARIANTS.update({'DMs': dict(design='bsd:dm', one_layer='DMs_1', opt=SUPPORT_START), 'DMs_1': dict(design='bsd:dm_1', opt=SUPPORT_START)})
VARIANTS.update({
    'D1z': dict(design='bsd:d1z', one_layer='D1z_1', opt=SUPPORT_START), 'D1z_1': dict(design='bsd:d1z_1', opt=SUPPORT_START),
    'D3z': dict(design='bsd:d3z', one_layer='D3z_1', opt=SUPPORT_START), 'D3z_1': dict(design='bsd:d3z_1', opt=SUPPORT_START),
})
VARIANTS.update({
    'DRs': dict(design='bsd:dr', one_layer='DRs_1', opt=SUPPORT_START), 'DRs_1': dict(design='bsd:dr_1', opt=SUPPORT_START),
    'D1p': dict(design='bsd:d1p', one_layer='D1s_1', opt=SUPPORT_START),
})
VARIANTS.update({'JZ': dict(design='bsd:jz', one_layer='JZ_1'), 'JZ_1': dict(design='bsd:jz_1')})
VARIANTS.update({'D2n': dict(design='bsd:d2n', one_layer='D2n_1', opt=SUPPORT_START), 'D2n_1': dict(design='bsd:d2n_1', opt=SUPPORT_START)})
# groups around the BSs' own SUS heads (1-layer counterparts: the same private lists without groups)
VARIANTS.update({'DH': dict(design='bsd:dh', one_layer='D1s_1', opt=SUPPORT_START),
                 'DRH': dict(design='bsd:drh', one_layer='DRs_1', opt=SUPPORT_START)})
# SUS core users stopped by the ZF sum rate, nearest-core groups, per-BS own-gain ranking
VARIANTS.update({'DZ': dict(design='bsd:dz', one_layer='DZ_1', opt=SUPPORT_START), 'DZ_1': dict(design='bsd:dz_1', opt=SUPPORT_START)})
# DZ with the QoS floor on the number of core users
VARIANTS.update({'DQ': dict(design='bsd:dq', one_layer='DQ_1', opt=SUPPORT_START), 'DQ_1': dict(design='bsd:dq_1', opt=SUPPORT_START)})
