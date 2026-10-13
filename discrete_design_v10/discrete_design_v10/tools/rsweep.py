"""R1 in the setting of the thesis composition study (FINDINGS.md section 3): T2, K = 16, N = 3, M = 500, S_max = 12, the
benchmark drops 801-805, R_th in {0, 0.5, ..., 2.5}, Q = 50. The runs use harness/grid.py's run() (same framework,
same record format) and go to results/<VARIANT>__T2__rsweep.jsonl (resumable).

    python3 tools/rsweep.py VARIANT [--workers 4]        # run
    python3 tools/rsweep.py X --report X1 [--json]       # X - X1 per R_th (paired over the drops)
"""
import os, sys, json, time, argparse
import multiprocessing as mp
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'harness')); sys.path.insert(0, os.path.join(ROOT, 'code'))
import grid as G

RTH = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
DROPS = [801, 802, 803, 804, 805]
CFGS = [dict(N=3, K=16, M=500, Smax=12, setting='rsweep_M500', Rth=r, drop=dr, scenario='T2', Dmax=10.0, L=3, Pmax=1.0)
        for dr in DROPS for r in RTH]


def fname(v):
    return os.path.join(ROOT, 'results', f'{v}__T2__rsweep.jsonl')


def load(v):
    out = {}
    if os.path.exists(fname(v)):
        for l in open(fname(v)):
            r = json.loads(l); c = r['cfg']; out[(c['drop'], float(c['Rth']))] = r
    return out


def report(X, X1, write_json):
    a, b = load(X), load(X1)
    keys = sorted(set(a) & set(b))
    print(f'===== R1 in the composition-study setting (T2, K = 16, N = 3, M = 500, S_max = 12, drops 801-805, Q = 50): '
          f'{len(keys)} common runs')
    print(f"{'R_th':>5} {'n':>3} {X:>9} {X1:>9} {X + '-' + X1:>17}  {'per drop':>40}   QoS met")
    out = dict(variant=X, one_layer=X1, rows=[])
    for R in RTH + ['all']:
        ks = [k for k in keys if R == 'all' or k[1] == R]
        if not ks: continue
        ra = lambda r: float(r['rate']) if r['qos_met'] else 0.0
        d = np.array([ra(a[k]) - ra(b[k]) for k in ks])
        se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else float('nan')
        per = ' '.join(f'{x:+.1f}' for x in d) if R != 'all' else ''
        print(f"{R if R == 'all' else f'{R:g}':>5} {len(ks):>3} {np.mean([ra(a[k]) for k in ks]):9.2f} {np.mean([ra(b[k]) for k in ks]):9.2f}"
              f" {d.mean():+8.2f}±{se:5.2f}   {per:>40}   {sum(a[k]['qos_met'] for k in ks)}/{sum(b[k]['qos_met'] for k in ks)}")
        out['rows'].append(dict(Rth=R, n=len(ks), mean=float(d.mean()), se=float(se)))
    if write_json:
        fn = os.path.join(ROOT, 'results', f'{X}__report_rsweep.json')
        json.dump(out, open(fn, 'w'), indent=1); print('written', fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('variant'); ap.add_argument('--workers', type=int, default=os.cpu_count())
    ap.add_argument('--report', default=None); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if a.report:
        report(a.variant, a.report, a.json); return
    done = set(load(a.variant))
    tag = f'{a.variant}__T2__rsweep'
    jobs = [(a.variant, c, 50, tag) for c in CFGS if (c['drop'], c['Rth']) not in done]
    print(f'{tag}: {len(jobs)} runs to do ({len(done)} done) -> {fname(a.variant)}', flush=True)
    t0 = time.time()
    with mp.get_context('spawn').Pool(a.workers, maxtasksperchild=10) as pool, open(fname(a.variant), 'a') as fh:
        for i, r in enumerate(pool.imap_unordered(G.run, jobs)):
            fh.write(json.dumps(r) + '\n'); fh.flush()
            c = r['cfg']
            print(f"  [{i + 1}/{len(jobs)}] drop {c['drop']} R_th {c['Rth']:g}: rate {r['rate']:.2f}"
                  f"{'' if r['qos_met'] else ' (QoS missed)'}, {r['nS']} streams{' BS-specific' if r['bs_specific'] else ''}"
                  f"  ({r['cpu']:.0f} CPU-s, {time.time() - t0:.0f} s elapsed)", flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
