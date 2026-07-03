#!/usr/bin/env python3
"""
TRELLIS — grid_sim: basket engine (reusable) สำหรับ Stage 0 sim
================================================================
อ้างอิง: Plan/TRELLIS-002_expectancy_sim_plan.md §3.2/§3.3

โครง engine (locked decisions §10):
  - flat lot (StartLot 0.01) — #2
  - one-at-a-time basket    — #7
  - fill convention §3.2: entry=limit (BUY@Ask/SELL@Bid), mark BUY→Bid/SELL→Ask,
    close=cross spread, hard-stop overshoot = slippage
  - cost §3.3: spread (จาก bid/ask), commission/side, stop slippage

หมายเหตุ: entry/TP/hard-stop ที่ใส่เป็น CALIBRATION param สำหรับ Layer 1
(ยังไม่ใช่ค่า §10.4/.5 ของวิน). engine ตัวนี้ใช้ซ้ำใน Layer 2/3 บน data จริง.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class GridConfig:
    spacing: float                       # ระยะระหว่าง grid level ($price)
    lot: float = 0.01                    # flat lot (#2)
    contract: float = 100.0              # oz/lot (XAU: 1 lot=100oz)
    max_levels: int = 20                 # เพดานไม้/basket
    tp_usd: float = 5.0                  # basket TP ($/cycle, $/R — #3)
    hardstop_usd: float = 50.0           # basket hard-stop ($/cycle)
    commission_per_lot_side: float = 7.0 # $ ต่อ 1.0 lot ต่อ side
    stop_slippage_usd: float = 0.20      # overshoot ตอน hard-stop ต่อ position (Doctrine #6)
    entry_lookback: int = 5              # หน้าต่าง fade
    entry_mode: str = "fade"             # 'fade'(MR) | 'random' | 'always_buy'


def _comm(lot, n, cfg):
    return cfg.commission_per_lot_side * lot * n


def run_grid(mid, spread, cfg, rng=None):
    """
    mid    : np.array ของ mid price
    spread : scalar หรือ np.array (price) — Bid=mid-spread/2, Ask=mid+spread/2
    คืน list ของ cycle dict: pnl, n_fills, closed_by, steps, max_adverse_usd
    """
    mid = np.asarray(mid, dtype=float)
    n = mid.size
    sp = np.full(n, float(spread)) if np.isscalar(spread) else np.asarray(spread, float)

    cycles = []
    open_basket = False
    direction = 0
    positions = []          # entry price ของแต่ละไม้
    next_level = 0.0
    commission = 0.0
    entry_step = 0
    max_adv = 0.0

    i = cfg.entry_lookback
    while i < n:
        half = sp[i] / 2.0
        bid = mid[i] - half
        ask = mid[i] + half

        if not open_basket:
            move = mid[i] - mid[i - cfg.entry_lookback]
            if cfg.entry_mode == "fade":
                if move < 0:
                    direction = 1      # ราคาลง → BUY (คาดเด้งกลับ) = mean-reversion
                elif move > 0:
                    direction = -1     # ราคาขึ้น → SELL
                else:
                    i += 1
                    continue
            elif cfg.entry_mode == "random":
                direction = 1 if rng.random() < 0.5 else -1
            else:
                direction = 1
            entry = ask if direction == 1 else bid    # limit entry §3.2
            positions = [entry]
            next_level = mid[i] - direction * cfg.spacing
            commission = _comm(cfg.lot, 1, cfg)
            entry_step = i
            max_adv = 0.0
            open_basket = True
            i += 1
            continue

        # --- basket เปิดอยู่: เติม grid ตามทิศ adverse (อาจหลายไม้ถ้า gap) ---
        while (len(positions) < cfg.max_levels and
               ((direction == 1 and mid[i] <= next_level) or
                (direction == -1 and mid[i] >= next_level))):
            entry = ask if direction == 1 else bid
            positions.append(entry)
            commission += _comm(cfg.lot, 1, cfg)
            next_level -= direction * cfg.spacing

        # --- mark floating PnL: BUY→Bid, SELL→Ask (§3.2) ---
        mark = bid if direction == 1 else ask
        gross = direction * np.sum(mark - np.asarray(positions)) * cfg.lot * cfg.contract
        float_pnl = gross - commission
        if -float_pnl > max_adv:
            max_adv = -float_pnl

        # --- exits ---
        if float_pnl >= cfg.tp_usd:
            close_comm = _comm(cfg.lot, len(positions), cfg)
            # TP = limit ปิดที่เป้า ไม่ปล่อยกำไรวิ่งถึง extreme (กัน overstate wins)
            pnl = cfg.tp_usd - close_comm
            cycles.append(dict(pnl=float(pnl), n_fills=len(positions), closed_by="TP",
                               steps=i - entry_step, max_adverse_usd=float(max_adv)))
            open_basket = False
        elif float_pnl <= -cfg.hardstop_usd:
            close_comm = _comm(cfg.lot, len(positions), cfg)
            slip = cfg.stop_slippage_usd * len(positions)   # overshoot ทะลุเพดาน (Doctrine #6)
            pnl = gross - commission - close_comm - slip
            cycles.append(dict(pnl=float(pnl), n_fills=len(positions), closed_by="STOP",
                               steps=i - entry_step, max_adverse_usd=float(max_adv)))
            open_basket = False
        i += 1

    return cycles


def run_grid_bars(O, H, L, C, cfg, spread, entry_mode="fade", lookback=15, rng=None,
                  intrabar="adverse_first"):
    """
    Bar-structured backtest บน M1 OHLC (real data) — แก้ตาม Engineer #1 (ไม่ใช้ M1 close ดิบ):
      - entry signal ตัดสินที่ 'close' ของแต่ละ bar (clean series — กัน microstructure ของ intra-bar)
      - fill/stop/TP ประมวล intra-bar ผ่าน O→adverse-extreme→favor-extreme→C
    ⚠️ INTRA-BAR BIAS (Engineer round-6): adverse-first conservative เฉพาะ STOP (4-6%) —
       แต่สำหรับ WIN (94%+) มันให้ grid fill ที่ extreme แล้ว recover ในแท่งเดียว (V-shape) = OPTIMISTIC
       → net OPTIMISTIC. ผลเป็น UPPER BOUND ของ expectancy ห้ามอ้างเป็นค่าจริง.
       ต้อง null-test (GBM-as-OHLC, layer2b) วัด artifact + ใช้ real-tick fill เพื่อค่าจริง.
    spread: scalar ($). swap = 0 (Exness swap-free — verify holding fee แยก).
    คืน list ของ cycle dict (เหมือน run_grid).
    """
    O = np.asarray(O, float); H = np.asarray(H, float)
    L = np.asarray(L, float); C = np.asarray(C, float)
    n = C.size
    half = spread / 2.0
    cycles = []
    open_basket = False
    direction = 0
    positions = []
    next_level = 0.0
    commission = 0.0
    entry_bar = 0
    max_adv = 0.0

    for i in range(n):
        if open_basket:
            adverse = L[i] if direction == 1 else H[i]    # BUY adverse=Low, SELL adverse=High
            favor = H[i] if direction == 1 else L[i]
            # adverse_first = OPTIMISTIC (fill ก้นเหวแล้ว recover) ; favor_first = PESSIMISTIC (bracket)
            seq = ((O[i], adverse, favor, C[i]) if intrabar == "adverse_first"
                   else (O[i], favor, adverse, C[i]))
            for px in seq:
                bid = px - half
                ask = px + half
                while (len(positions) < cfg.max_levels and
                       ((direction == 1 and px <= next_level) or
                        (direction == -1 and px >= next_level))):
                    positions.append(ask if direction == 1 else bid)
                    commission += _comm(cfg.lot, 1, cfg)
                    next_level -= direction * cfg.spacing
                mark = bid if direction == 1 else ask
                gross = direction * np.sum(mark - np.asarray(positions)) * cfg.lot * cfg.contract
                float_pnl = gross - commission
                if -float_pnl > max_adv:
                    max_adv = -float_pnl
                if float_pnl <= -cfg.hardstop_usd:
                    close_comm = _comm(cfg.lot, len(positions), cfg)
                    slip = cfg.stop_slippage_usd * len(positions)
                    cycles.append(dict(pnl=float(gross - commission - close_comm - slip),
                                       n_fills=len(positions), closed_by="STOP",
                                       bars=i - entry_bar, max_adverse_usd=float(max_adv)))
                    open_basket = False
                    break
                if float_pnl >= cfg.tp_usd:
                    close_comm = _comm(cfg.lot, len(positions), cfg)
                    # TP = limit ปิดที่เป้า ไม่ปล่อยวิ่งถึง favor-extreme (กัน overstate wins)
                    cycles.append(dict(pnl=float(cfg.tp_usd - close_comm),
                                       n_fills=len(positions), closed_by="TP",
                                       bars=i - entry_bar, max_adverse_usd=float(max_adv)))
                    open_basket = False
                    break
        if not open_basket:
            if i < lookback:
                continue
            if entry_mode == "fade":
                move = C[i] - C[i - lookback]
                direction = 1 if move < 0 else (-1 if move > 0 else 0)
                if direction == 0:
                    continue
            elif entry_mode == "random":
                direction = 1 if rng.random() < 0.5 else -1
            else:
                direction = 1
            c = C[i]
            entry = (c + half) if direction == 1 else (c - half)   # limit fill ที่ close
            positions = [entry]
            next_level = c - direction * cfg.spacing
            commission = _comm(cfg.lot, 1, cfg)
            entry_bar = i
            max_adv = 0.0
            open_basket = True
    return cycles


def summarize(cycles):
    """คืน metric สรุปจาก list ของ cycle (numbers เป็นของ script)."""
    if not cycles:
        return dict(n_cycles=0, expectancy=0.0, total=0.0, win_rate=0.0,
                    stop_rate=0.0, avg_fills=0.0, avg_win=0.0, avg_loss=0.0)
    pnls = np.array([c["pnl"] for c in cycles])
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]
    stops = sum(1 for c in cycles if c["closed_by"] == "STOP")
    return dict(
        n_cycles=len(cycles),
        expectancy=float(pnls.mean()),
        total=float(pnls.sum()),
        win_rate=float((pnls > 0).mean()),
        stop_rate=float(stops / len(cycles)),
        avg_fills=float(np.mean([c["n_fills"] for c in cycles])),
        avg_win=float(wins.mean()) if wins.size else 0.0,
        avg_loss=float(losses.mean()) if losses.size else 0.0,
    )
