#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dir_features.py — TRELLIS-010 · shared as-of feature builder (single source · CLAUDE rule 3)
compute_features() anchored ที่ bar `a` (inclusive) · **ทุก index ≤ a** = no within-bar lookahead
ใช้ทั้ง direction_at_real_exit (anchor=j=decision bar) · (v1 migration = Issue แยก)

⚠ R = risk unit ที่ส่งเข้ามา (direction_at_real_exit ใช้ ash−asl · **ไม่ใช่ Rmap**) — Engineer P1-b
⚠ tdir = decision direction ที่ส่งเข้ามา (v4: breakout dir d) — Engineer note
"""
import numpy as np

FEATS = ["tdir", "ret5", "ret15", "ret60", "ret240", "posrange", "dist_pdh", "dist_pdl",
         "vol30", "slope60", "trigpress", "ntrig30", "clv", "clv5", "upwick", "dnwick",
         "body", "tdir_x_ret15", "pos_x_slope"]


def session_derived(oo, hh, ll, cc):
    """as-of session arrays (แต่ละ element as-of bar ตัวเอง) — precompute ครั้งเดียว/วัน"""
    rng = np.maximum(hh - ll, 1e-9)
    clv = ((cc - ll) - (hh - cc)) / rng
    upw = (hh - np.maximum(oo, cc)) / rng
    dnw = (np.minimum(oo, cc) - ll) / rng
    body = np.abs(cc - oo) / rng
    cmin = np.minimum.accumulate(ll)
    cmax = np.maximum.accumulate(hh)
    return clv, upw, dnw, body, cmin, cmax


def compute_features(hh, ll, cc, lt, st, clv, upw, dnw, body, cmin, cmax,
                     a, pdh, pdl, R, tdir):
    """19 as-of features anchored ที่ bar a (inclusive) · index สูงสุด = a (assert ได้)
    R = risk unit (ash−asl) · tdir = decision dir · pdh/pdl = prior-day (complete)"""
    dr = cmax[a] - cmin[a]
    pos = (cc[a] - cmin[a]) / dr if dr > 0 else 0.5
    ret15 = (cc[a] - cc[a - 15]) / R
    slope60 = (cc[a] - cc[a - 60:a + 1].mean()) / R
    return [
        tdir,
        (cc[a] - cc[a - 5]) / R, ret15, (cc[a] - cc[a - 60]) / R, (cc[a] - cc[a - 240]) / R,
        pos,
        (cc[a] - pdh) / R if pdh else 0.0, (cc[a] - pdl) / R if pdl else 0.0,
        (hh[a - 30:a + 1].max() - ll[a - 30:a + 1].min()) / R,
        slope60,
        int(lt[a - 30:a].sum()) - int(st[a - 30:a].sum()),
        int(lt[a - 30:a].sum()) + int(st[a - 30:a].sum()),
        clv[a], clv[a - 5:a + 1].mean(), upw[a], dnw[a], body[a],
        tdir * ret15, pos * slope60,
    ]
