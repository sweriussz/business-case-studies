#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модель прибыльности корпоративного отеля (8 номеров, Бишкек)
=============================================================
Воспроизводит расчёты бизнес-кейса «Hotel Profitability & Corporate Segment
Strategy» (Эржан Амир):

  1. Юнит-экономика — на проданную ночь и на номер (раздел 2 кейса)
  2. Стресс-тесты — шоки выручки, аренды, электричества, персонала (раздел 5);
     там же карта «цена × загрузка» и безубыточность (разделы 3–4)
  3. Мост прибыли — рычаги, сценарии, окупаемость (раздел 6)

Единицы: деньги в месяц — тыс. сом; цена и показатели «на ночь» — сом.
Все исходные данные — со слов владельца, не аудированы; допущения автора кейса
помечены в классах Inputs / BridgeParams / SCENARIOS.

Запуск:
    python hotel_model.py                    # таблицы в консоль + сверка с кейсом
    python hotel_model.py --out results      # + CSV-таблицы и PNG-графики в папку
    python hotel_model.py --out results --no-plots

Зависимости: pandas, numpy; matplotlib — только для графиков.
Чтобы проверить свой сценарий, измените значения в Inputs / Scenario / Shock.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ════════════════════════════════════════════════════════════════════════════
# 1. ИСХОДНЫЕ ДАННЫЕ
# ════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Inputs:
    """Исходные данные кейса (тыс. сом в месяц, если не указано иное)."""

    # Объект и продажи (заявлено владельцем)
    rooms: int = 8
    days_per_year: int = 365
    occupancy: float = 0.94          # загрузка
    adr: float = 3755.0              # средняя цена за ночь, сом (прейскурантный ADR)
    revenue: float = 800.0           # выручка в месяц — ОПОРНАЯ ТОЧКА модели (раздел 4)

    # Постоянные затраты
    rent: float = 350.0
    payroll: float = 102.3           # ФОТ + взносы, как принято в модели (раздел 2)
    electricity: float = 60.0        # среднемесячное; зимой до 100
    water: float = 6.5

    # Расходники: середина диапазона 15–20 тыс. (допущение кейса)
    supplies_low: float = 15.0
    supplies_high: float = 20.0

    # Каналы и комиссия
    share_booking: float = 0.20      # доля ночей через Booking.com
    share_social: float = 0.03       # доля ночей из соцсетей (без комиссии)
    commission_rate: float = 0.23    # комиссия Booking.com

    # Единый налог: 6% с наличных, 4% с безналичных, 15% поступлений — наличные (допущение)
    cash_share: float = 0.15
    tax_cash: float = 0.06
    tax_noncash: float = 0.04

    # Для справочных расчётов (раздел 2)
    payroll_gross: float = 100.0     # ФОТ, названный владельцем
    social_rate: float = 0.1225      # ставка взносов в Соцфонд
    ffe_reserve: float = 0.05        # резерв FF&E от выручки

    # ── производные величины ──
    @property
    def nights_avail(self) -> float:          # номеро-ночей в месяц (243,3)
        return self.rooms * self.days_per_year / 12

    @property
    def sold_nights(self) -> float:           # проданных ночей в месяц
        return self.nights_avail * self.occupancy

    @property
    def implied_revenue(self) -> float:       # загрузка × ADR × номеро-ночи, тыс. сом
        return self.occupancy * self.adr * self.nights_avail / 1000

    @property
    def calib(self) -> float:                 # коэффициент приведения (заявленная ÷ расчётная)
        return self.revenue / self.implied_revenue

    @property
    def realized_adr(self) -> float:          # ADR, следующий из выручки и загрузки, сом
        return self.revenue * 1000 / self.sold_nights

    @property
    def supplies(self) -> float:
        return (self.supplies_low + self.supplies_high) / 2

    @property
    def fixed(self) -> float:                 # постоянные затраты (518,8)
        return self.rent + self.payroll + self.electricity + self.water

    @property
    def comm_pct(self) -> float:              # комиссия, % от выручки (4,6%)
        return self.share_booking * self.commission_rate

    @property
    def tax_rate(self) -> float:              # единый налог в среднем (4,3%)
        return self.cash_share * self.tax_cash + (1 - self.cash_share) * self.tax_noncash

    @property
    def var_share(self) -> float:             # переменные потери с выручки: комиссия + налог (8,9%)
        return self.comm_pct + self.tax_rate

    @property
    def share_noncontract(self) -> float:     # неконтрактные ночи (23%)
        return self.share_booking + self.share_social

    @property
    def share_contract(self) -> float:        # контрактные ночи (77%)
        return 1 - self.share_noncontract


# ════════════════════════════════════════════════════════════════════════════
# 2. БАЗА И ЮНИТ-ЭКОНОМИКА (раздел 2 кейса)
# ════════════════════════════════════════════════════════════════════════════
def baseline(inp: Inputs) -> dict:
    """Месячный P&L владельца, тыс. сом."""
    rev = inp.revenue
    commission = rev * inp.comm_pct
    tax = rev * inp.tax_rate
    costs = inp.fixed + inp.supplies + commission
    profit = rev - costs - tax
    return dict(
        revenue=rev, fixed=inp.fixed, supplies=inp.supplies, commission=commission,
        costs=costs, tax=tax, profit=profit,
        margin=profit / rev, margin_pre_tax=(rev - costs) / rev,
        profit_after_ffe=profit - rev * inp.ffe_reserve,
    )


def unit_economics(inp: Inputs) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Возвращает (на проданную ночь, на номер в месяц, «куда уходят 100 сом»)."""
    b = baseline(inp)
    n = inp.sold_nights

    price = inp.adr
    supplies = -inp.supplies * 1000 / n
    commission = -price * inp.comm_pct
    contrib_pre = price + supplies + commission
    tax = -price * inp.tax_rate
    contrib_post = contrib_pre + tax
    fixed = -inp.fixed * 1000 / n
    profit_at_adr = contrib_post + fixed
    owner = b["profit"] * 1000 / n
    recon = owner - profit_at_adr          # = −ADR·(1−k)·(1−var), сверка с заявленной выручкой

    per_night = pd.DataFrame(
        [
            ("Цена (ADR)", price, "сом"),
            ("Расходники", supplies, "сом"),
            ("Комиссия Booking.com, в среднем", commission, "сом"),
            ("Вклад до единого налога", contrib_pre, "сом"),
            ("Единый налог", tax, "сом"),
            ("Вклад после единого налога", contrib_post, "сом"),
            ("Постоянные затраты на проданную ночь", fixed, "сом"),
            ("Прибыль за ночь по заявленному ADR", profit_at_adr, "сом"),
            ("Сверка с фактической выручкой (×k)", recon, "сом"),
            ("Прибыль владельца за проданную ночь", owner, "сом"),
        ],
        columns=["Статья", "Значение", "Ед."],
    )

    r = inp.rooms
    per_room = pd.DataFrame(
        [
            ("Выручка", b["revenue"] / r, "тыс. сом/мес"),
            ("Затраты", -b["costs"] / r, "тыс. сом/мес"),
            ("Единый налог", -b["tax"] / r, "тыс. сом/мес"),
            ("Прибыль владельца на номер", b["profit"] / r, "тыс. сом/мес"),
        ],
        columns=["Статья", "Значение", "Ед."],
    )

    rev = b["revenue"]
    items = [
        ("Выручка", rev), ("Аренда", -inp.rent), ("ФОТ + взносы", -inp.payroll),
        ("Электричество", -inp.electricity), ("Вода", -inp.water),
        ("Расходники", -inp.supplies), ("Комиссия Booking.com", -b["commission"]),
        ("Единый налог", -b["tax"]), ("Прибыль владельца", b["profit"]),
    ]
    cascade = pd.DataFrame(
        [(name, v, v / rev * 100) for name, v in items],
        columns=["Статья", "тыс. сом/мес", "на 100 сом выручки"],
    )
    return per_night, per_room, cascade


def calibration(inp: Inputs) -> pd.DataFrame:
    """Сверка трёх заявленных цифр: загрузка × ADR × ночи ≠ выручка (раздел 4)."""
    rows = [
        ("Расчётная выручка (загрузка × ADR × номеро-ночи)", inp.implied_revenue, "тыс. сом/мес"),
        ("Заявленная выручка", inp.revenue, "тыс. сом/мес"),
        ("Разрыв", inp.implied_revenue - inp.revenue, "тыс. сом/мес"),
        ("Коэффициент приведения k (заявленная ÷ расчётная)", inp.calib, "коэф."),
        ("Разрыв в год", (inp.implied_revenue - inp.revenue) * 12 / 1000, "млн сом"),
        ("ADR, следующий из выручки и загрузки", inp.realized_adr, "сом"),
        ("Загрузка, следующая из выручки и ADR",
         inp.revenue * 1000 / (inp.adr * inp.nights_avail) * 100, "%"),
    ]
    return pd.DataFrame(rows, columns=["Показатель", "Значение", "Ед."])


# ════════════════════════════════════════════════════════════════════════════
# 3. БЕЗУБЫТОЧНОСТЬ, ЦЕННОСТЬ РЫЧАГОВ, КАРТА «ЦЕНА × ЗАГРУЗКА» (разделы 3–4)
# ════════════════════════════════════════════════════════════════════════════
def break_even_occupancy(inp: Inputs, list_adr: bool = False, after_tax: bool = True) -> float:
    """Загрузка, при которой прибыль владельца = 0.

    list_adr=False — по заявленной выручке (с коэффициентом k), как на карте кейса;
    list_adr=True  — по прейскурантному ADR 3 755 (k = 1).
    """
    k = 1.0 if list_adr else inp.calib
    revenue_at_100 = inp.adr * inp.nights_avail * k / 1000          # выручка при загрузке 100%
    var = inp.comm_pct + (inp.tax_rate if after_tax else 0.0)
    supplies_at_100 = inp.supplies / inp.occupancy
    return inp.fixed / (revenue_at_100 * (1 - var) - supplies_at_100)


def marginal_values(inp: Inputs) -> dict:
    """Ценность 1% цены и 1 пункта загрузки, тыс. сом/мес (раздел 3)."""
    v = inp.var_share
    price_1pct = inp.revenue * 0.01 * (1 - v)
    occ_1pt = inp.revenue / (inp.occupancy * 100) * (1 - v) - inp.supplies / (inp.occupancy * 100)
    return dict(price_1pct=price_1pct, occupancy_1pt=occ_1pt)


def profit_at(inp: Inputs, occupancy: float, adr_change: float = 0.0) -> float:
    """Прибыль владельца после налога при заданных загрузке и изменении ADR."""
    revenue = occupancy * inp.adr * (1 + adr_change) * inp.nights_avail * inp.calib / 1000
    supplies = inp.supplies * occupancy / inp.occupancy       # расходники растут с загрузкой
    return revenue * (1 - inp.var_share) - inp.fixed - supplies


OCC_GRID = (0.96, 0.94, 0.92, 0.90, 0.88, 0.84, 0.80, 0.75, 0.70, 0.65)
ADR_GRID = (-0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.10)


def sensitivity_map(inp: Inputs, occ_grid=OCC_GRID, adr_grid=ADR_GRID) -> pd.DataFrame:
    data = [[profit_at(inp, o, d) for d in adr_grid] for o in occ_grid]
    cols = [f"{d:+.1%} ({inp.adr * (1 + d):,.0f})" for d in adr_grid]
    return pd.DataFrame(data, index=[f"{o:.0%}" for o in occ_grid], columns=cols)


# ════════════════════════════════════════════════════════════════════════════
# 4. СТРЕСС-ТЕСТЫ (раздел 5 кейса)
# ════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Shock:
    """Шок как набор относительных изменений к базе.

    d_supplies / d_commission = None → следуют за выручкой (d_revenue).
    """
    name: str
    d_revenue: float = 0.0
    d_supplies: Optional[float] = None
    d_commission: Optional[float] = None
    d_rent: float = 0.0
    d_electricity: float = 0.0
    extra_fixed: float = 0.0          # прочие постоянные затраты, тыс. сом/мес
    in_case: bool = True              # False — расширение сверх таблицы кейса


def default_shocks(inp: Inputs) -> list[Shock]:
    """Шоки из таблицы раздела 5 + два из текста кейса + один комбинированный."""
    social_on_top = inp.payroll_gross * inp.social_rate - (inp.payroll - inp.payroll_gross)
    return [
        Shock("База"),
        Shock("Выручка −10%", d_revenue=-0.10),
        Shock("Выручка −15%", d_revenue=-0.15),
        # потеря операторов: уходят расходники и налог, комиссия Booking.com остаётся
        Shock("Потеря двух мобильных операторов (−8% выручки)", d_revenue=-0.08, d_commission=0.0),
        Shock("Аренда +10%", d_rent=0.10),
        Shock("Электричество +20%", d_electricity=0.20),
        Shock("Управляющий за 60 тыс.", extra_fixed=60.0),
        # из текста кейса (разделы 2 и 5)
        Shock("Электричество 100 тыс. (месяц отопления)", d_electricity=100 / inp.electricity - 1, in_case=False),
        Shock("Взносы 12,25% начисляются сверху на ФОТ", extra_fixed=social_on_top, in_case=False),
        # расширение: два шока одновременно (нет в кейсе)
        Shock("Комбинированный: выручка −10% и аренда +10%", d_revenue=-0.10, d_rent=0.10, in_case=False),
    ]


def stress_profit(inp: Inputs, s: Shock) -> dict:
    d_sup = s.d_revenue if s.d_supplies is None else s.d_supplies
    d_com = s.d_revenue if s.d_commission is None else s.d_commission
    b = baseline(inp)
    revenue = b["revenue"] * (1 + s.d_revenue)
    fixed = inp.fixed + inp.rent * s.d_rent + inp.electricity * s.d_electricity + s.extra_fixed
    supplies = b["supplies"] * (1 + d_sup)
    commission = b["commission"] * (1 + d_com)
    tax = revenue * inp.tax_rate
    profit = revenue - fixed - supplies - commission - tax
    delta = profit - b["profit"]
    if abs(delta) < 1e-9:                       # убрать «-0.0» от float-шума
        delta = 0.0
    return dict(revenue=revenue, fixed=fixed, supplies=supplies, commission=commission,
                tax=tax, profit=profit, delta=delta, delta_pct=delta / b["profit"],
                margin=profit / revenue)


def stress_tests(inp: Inputs, shocks: Optional[list[Shock]] = None) -> pd.DataFrame:
    shocks = shocks if shocks is not None else default_shocks(inp)
    rows = []
    for s in shocks:
        r = stress_profit(inp, s)
        pure_revenue = s.d_rent == 0 and s.d_electricity == 0 and s.extra_fixed == 0
        lever = r["delta_pct"] / s.d_revenue if (s.d_revenue and pure_revenue) else np.nan  # эффект рычага, ×
        rows.append({
            "Шок": s.name, "Выручка": r["revenue"], "Постоянные": r["fixed"],
            "Расходники": r["supplies"], "Комиссия": r["commission"], "Налог": r["tax"],
            "Прибыль владельца": r["profit"], "Δ, тыс.": r["delta"], "Δ, %": r["delta_pct"],
            "Маржа": r["margin"], "Рычаг, ×": lever, "В кейсе": s.in_case,
        })
    return pd.DataFrame(rows)


def revenue_safety_margin(inp: Inputs) -> float:
    """На сколько может упасть выручка (все переменные затраты — вместе с ней), прежде чем прибыль = 0."""
    x = inp.fixed / (inp.revenue * (1 - inp.var_share) - inp.supplies)
    return x - 1


# ════════════════════════════════════════════════════════════════════════════
# 5. МОСТ ПРИБЫЛИ (раздел 6 кейса)
# ════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class BridgeParams:
    """Общие параметры рычагов (разовые затраты — оценки без котировок)."""
    reprice_price: float = 0.04       # +4% к цене контрактов при пролонгации
    reprice_share: float = 0.90       # доля контрактной выручки, где цена пересматривается
    reprice_vol_loss: float = 0.01    # потеря контрактного объёма
    capex_pricing: float = 20.0       # рычаг 2: разовые затраты
    capex_energy: float = 120.0       # рычаг 5
    capex_staff: float = 10.0         # гигиена: персонал и SOP
    capex_direct: float = 30.0        # гигиена: линия прямых броней
    opex_staff: float = 3.0           # тыс. сом/мес
    opex_direct: float = 5.0          # тыс. сом/мес
    rent_reset_low: float = 0.05      # рычаг 1: возможный пересмотр аренды
    rent_reset_high: float = 0.10
    horizon_months: int = 36

    @property
    def one_off(self) -> float:       # 180
        return self.capex_pricing + self.capex_energy + self.capex_staff + self.capex_direct


@dataclass(frozen=True)
class Scenario:
    name: str
    price_nc: float                   # рост цены на неконтрактных ночах
    vol_loss_nc: float                # потеря объёма на неконтрактных ночах
    booking_pts: float                # пунктов ночей ушло с Booking.com
    elec_saving: float                # экономия электричества
    contract_repricing: bool = False  # рычаг 4 (апсайд)


SCENARIOS = (
    Scenario("Консервативный", 0.04, 0.03, 2, 0.05, False),
    Scenario("Базовый", 0.08, 0.02, 4, 0.10, False),
    Scenario("Апсайд", 0.08, 0.02, 4, 0.10, True),
)


def bridge_effects(inp: Inputs, bp: BridgeParams, sc: Scenario) -> dict:
    """Эффекты рычагов, тыс. сом/мес. Операционная прибыль — до налога; налог — на доп. выручку."""
    rev, commission = inp.revenue, inp.revenue * inp.comm_pct
    rev_nc = rev * inp.share_noncontract
    rev_c = rev * inp.share_contract

    # Рычаг 2. Цена на неконтрактных ночах: выручка и комиссия Booking.com меняются на g,
    # расходники экономятся на потерянном объёме
    g = (1 + sc.price_nc) * (1 - sc.vol_loss_nc) - 1
    pricing = rev_nc * g - commission * g + inp.supplies * inp.share_noncontract * sc.vol_loss_nc
    d_rev_pricing = rev_nc * g

    # Рычаг 3. Каналы: каждая проданная через Booking ночь стоит комиссию 23% реализованной цены
    commission_per_night = inp.commission_rate * inp.realized_adr          # ≈804 сом
    channel = sc.booking_pts / 100 * inp.nights_avail * commission_per_night / 1000

    # Рычаг 5. Энергия
    energy = inp.electricity * sc.elec_saving

    # Гигиена: затраты учтены, выгода — нет
    staff, direct = -bp.opex_staff, -bp.opex_direct

    # Рычаг 4 (апсайд). Пересмотр цен при пролонгации контрактов
    if sc.contract_repricing:
        d_rev_reprice = rev_c * bp.reprice_share * bp.reprice_price - rev_c * bp.reprice_vol_loss
        repricing = d_rev_reprice + inp.supplies * inp.share_contract * bp.reprice_vol_loss
    else:
        d_rev_reprice = repricing = 0.0

    pre_tax = pricing + channel + energy + staff + direct + repricing
    d_revenue = d_rev_pricing + d_rev_reprice
    tax = d_revenue * inp.tax_rate
    after_tax = pre_tax - tax

    profit0 = baseline(inp)["profit"]
    payback = bp.one_off / after_tax if after_tax * bp.horizon_months >= bp.one_off else np.nan
    return dict(
        pricing=pricing, channel=channel, energy=energy, staff=staff, direct=direct,
        repricing=repricing, pre_tax=pre_tax, d_revenue=d_revenue, tax=tax, after_tax=after_tax,
        new_profit=profit0 + after_tax, growth=after_tax / profit0,
        payback_months=payback, net_horizon=after_tax * bp.horizon_months - bp.one_off,
    )


def scenario_table(inp: Inputs, bp: BridgeParams, scenarios=SCENARIOS) -> pd.DataFrame:
    labels = {
        "pricing": "Рычаг 2. Цены на неконтрактных ночах", "channel": "Рычаг 3. Микс каналов",
        "energy": "Рычаг 5. Энергия", "staff": "Гигиена: персонал и SOP",
        "direct": "Гигиена: линия прямых броней", "repricing": "Рычаг 4. Пересмотр цен в контрактах",
        "pre_tax": "Δ операционной прибыли до налога", "tax": "Налог с доп. выручки (вычитается)",
        "after_tax": "Δ прибыли владельца после налога", "new_profit": "Прибыль владельца после программы",
        "growth": "Рост к текущей прибыли, %", "payback_months": "Окупаемость разовых затрат, мес.",
        "net_horizon": f"Чистый эффект за {bp.horizon_months} мес., тыс. сом",
    }
    res = {sc.name: bridge_effects(inp, bp, sc) for sc in scenarios}
    sign = {"tax": -1, "growth": 100}          # налог показываем со знаком «−», рост — в процентах
    return pd.DataFrame({name: {labels[k]: r[k] * sign.get(k, 1) for k in labels} for name, r in res.items()})


def waterfall_steps(inp: Inputs, bp: BridgeParams, base: Scenario, upside: Scenario):
    """Шаги моста прибыли владельца после налога: (подпись, значение, тип 'total'/'delta')."""
    p0 = baseline(inp)["profit"]
    eb, eu = bridge_effects(inp, bp, base), bridge_effects(inp, bp, upside)
    base_total = p0 + eb["after_tax"]
    return [
        ("Сегодня", p0, "total"),
        ("Цены на неконтрактные ночи", eb["pricing"], "delta"),
        ("Микс каналов", eb["channel"], "delta"),
        ("Энергия", eb["energy"], "delta"),
        ("Персонал и SOP", eb["staff"], "delta"),
        ("Линия прямых броней", eb["direct"], "delta"),
        ("Налог с доп. выручки", -eb["tax"], "delta"),
        ("База", base_total, "total"),
        ("Пересмотр цен в контрактах", eu["repricing"], "delta"),
        ("Налог с доп. выручки ", -(eu["tax"] - eb["tax"]), "delta"),
        ("Апсайд", eu["new_profit"], "total"),
    ]


def rent_protection(inp: Inputs, bp: BridgeParams) -> dict:
    """Рычаг 1: защита аренды (не входит в мост) — что стоил бы пересмотр аренды."""
    low, high = inp.rent * bp.rent_reset_low, inp.rent * bp.rent_reset_high
    h = bp.horizon_months
    return dict(monthly_low=low, monthly_high=high, horizon_low=low * h, horizon_high=high * h)


def contract_breakeven_volume_loss(inp: Inputs, bp: BridgeParams) -> float:
    """Потеря контрактного объёма, при которой пересмотр цен перестаёт приносить прибыль (3,7%)."""
    rev_c = inp.revenue * inp.share_contract
    gain = rev_c * bp.reprice_share * bp.reprice_price
    return gain / (rev_c - inp.supplies * inp.share_contract)


# ════════════════════════════════════════════════════════════════════════════
# 6. СВЕРКА С ЦИФРАМИ КЕЙСА
# ════════════════════════════════════════════════════════════════════════════
def verify(inp: Inputs, bp: BridgeParams) -> pd.DataFrame:
    """Сравнивает расчёт с цифрами, напечатанными в кейсе (допуск = округление в кейсе)."""
    b = baseline(inp)
    pn, pr, _ = unit_economics(inp)
    pn = dict(zip(pn["Статья"], pn["Значение"]))
    pr = dict(zip(pr["Статья"], pr["Значение"]))
    mv = marginal_values(inp)
    st = stress_tests(inp).set_index("Шок")
    sc = {s.name: bridge_effects(inp, bp, s) for s in SCENARIOS}
    cons, base, up = sc["Консервативный"], sc["Базовый"], sc["Апсайд"]
    rp = rent_protection(inp, bp)

    checks = [  # (показатель, значение в кейсе, расчёт, допуск, раздел)
        ("Затраты, тыс.", 573.1, b["costs"], 0.05, "2"),
        ("Единый налог, тыс.", 34.4, b["tax"], 0.05, "2"),
        ("Прибыль владельца, тыс.", 192.5, b["profit"], 0.05, "2"),
        ("Маржа после налога", 0.241, b["margin"], 0.0005, "2"),
        ("Прибыль после резерва FF&E 5%, тыс.", 152.5, b["profit_after_ffe"], 0.05, "2"),
        ("Расчётная выручка, тыс.", 858.9, inp.implied_revenue, 0.05, "4"),
        ("Коэффициент приведения", 0.931, inp.calib, 0.0005, "4"),
        ("ADR из выручки и загрузки, сом", 3498, inp.realized_adr, 1, "4"),
        ("Загрузка из выручки и ADR", 0.876, inp.revenue * 1000 / (inp.adr * inp.nights_avail), 0.0005, "4"),
        ("Безубыточная загрузка после налога (по заявл. выручке)", 0.69, break_even_occupancy(inp), 0.005, "3"),
        ("Безубыточная загрузка по прейскурантному ADR, после налога", 0.64, break_even_occupancy(inp, True), 0.005, "3"),
        ("Безубыточная загрузка по прейскурантному ADR, до налога", 0.61, break_even_occupancy(inp, True, False), 0.005, "3"),
        ("Запас прочности, п.п. (заявл. выручка)", 25, (inp.occupancy - break_even_occupancy(inp)) * 100, 0.5, "3"),
        ("Запас прочности, п.п. (прейскурантный ADR)", 30, (inp.occupancy - break_even_occupancy(inp, True)) * 100, 0.5, "3"),
        ("+1% цены, тыс./мес", 7.3, mv["price_1pct"], 0.05, "3"),
        ("+1 п.п. загрузки, тыс./мес", 7.6, mv["occupancy_1pt"], 0.05, "3"),
        ("Расходники на ночь, сом", -77, pn["Расходники"], 1, "2"),
        ("Комиссия на ночь, сом", -173, pn["Комиссия Booking.com, в среднем"], 1, "2"),
        ("Вклад до налога на ночь, сом", 3505, pn["Вклад до единого налога"], 1, "2"),
        ("Налог на ночь, сом", -161, pn["Единый налог"], 1, "2"),
        ("Вклад после налога на ночь, сом", 3344, pn["Вклад после единого налога"], 1, "2"),
        ("Постоянные затраты на ночь, сом", -2268, pn["Постоянные затраты на проданную ночь"], 1, "2"),
        ("Прибыль за ночь по заявл. ADR, сом", 1076, pn["Прибыль за ночь по заявленному ADR"], 1, "2"),
        ("Сверка с выручкой на ночь, сом", -234, pn["Сверка с фактической выручкой (×k)"], 1, "2"),
        ("Прибыль владельца за ночь, сом", 842, pn["Прибыль владельца за проданную ночь"], 1, "2"),
        ("Выручка на номер, тыс.", 100.0, pr["Выручка"], 0.05, "2"),
        ("Затраты на номер, тыс.", -71.6, pr["Затраты"], 0.05, "2"),
        ("Налог на номер, тыс.", -4.3, pr["Единый налог"], 0.05, "2"),
        ("Прибыль на номер, тыс.", 24.1, pr["Прибыль владельца на номер"], 0.05, "2"),
    ]
    for name, profit, delta, margin in [
        ("Выручка −10%", 121.4, -71.1, 0.169), ("Выручка −15%", 85.8, -106.7, 0.126),
        ("Потеря двух мобильных операторов (−8% выручки)", 132.7, -59.8, 0.180),
        ("Аренда +10%", 157.5, -35.0, 0.197), ("Электричество +20%", 180.5, -12.0, 0.226),
        ("Управляющий за 60 тыс.", 132.5, -60.0, 0.166),
    ]:
        short = name.split(" (")[0]
        checks += [
            (f"Стресс «{short}»: прибыль, тыс.", profit, st.loc[name, "Прибыль владельца"], 0.05, "5"),
            (f"Стресс «{short}»: Δ, тыс.", delta, st.loc[name, "Δ, тыс."], 0.05, "5"),
            (f"Стресс «{short}»: маржа", margin, st.loc[name, "Маржа"], 0.0005, "5"),
        ]
    checks += [
        ("Рычаг 2. Цены, тыс./мес", 8.7, base["pricing"], 0.05, "6"),
        ("Рычаг 3. Каналы, тыс./мес", 7.8, base["channel"], 0.05, "6"),
        ("Рычаг 5. Энергия, тыс./мес", 6.0, base["energy"], 0.05, "6"),
        ("Гигиена, тыс./мес", -8.0, base["staff"] + base["direct"], 0.05, "6"),
        ("Рычаг 4. Пересмотр контрактов, тыс./мес", 16.2, up["repricing"], 0.06, "6"),
        ("База: Δ операционной прибыли, тыс.", 14.5, base["pre_tax"], 0.05, "6"),
        ("Апсайд: Δ операционной прибыли, тыс.", 30.6, up["pre_tax"], 0.1, "6"),
        ("База: Δ прибыли после налога, тыс.", 14.0, base["after_tax"], 0.05, "6"),
        ("Апсайд: Δ прибыли после налога, тыс.", 29.5, up["after_tax"], 0.05, "6"),
        ("Прибыль владельца в базе, тыс.", 206.5, base["new_profit"], 0.05, "6"),
        ("Прибыль владельца в апсайде, тыс.", 222.0, up["new_profit"], 0.05, "6"),
        ("Консервативный: Δ до налога, тыс. (≈0)", 0.0, cons["pre_tax"], 0.5, "6"),
        ("Окупаемость базы, мес.", 13, base["payback_months"], 0.5, "6"),
        ("Окупаемость апсайда, мес.", 6, up["payback_months"], 0.5, "6"),
        ("Чистый эффект базы за 36 мес., млн", 0.3, base["net_horizon"] / 1000, 0.05, "6"),
        ("Чистый эффект апсайда за 36 мес., млн", 0.9, up["net_horizon"] / 1000, 0.05, "6"),
        ("Потеря контрактного объёма, при которой рычаг 4 = 0", 0.037, contract_breakeven_volume_loss(inp, bp), 0.0005, "6"),
        ("Защита аренды: низ, тыс./мес", 17.5, rp["monthly_low"], 0.05, "1"),
        ("Защита аренды: верх, тыс./мес", 35.0, rp["monthly_high"], 0.05, "1"),
        ("Защита аренды за 3 года: низ, млн", 0.6, rp["horizon_low"] / 1000, 0.05, "1"),
        ("Защита аренды за 3 года: верх, млн", 1.3, rp["horizon_high"] / 1000, 0.05, "1"),
    ]
    df = pd.DataFrame(checks, columns=["Показатель", "Кейс", "Модель", "Допуск", "Раздел"])
    df["Разница"] = df["Модель"] - df["Кейс"]
    df["Статус"] = np.where(df["Разница"].abs() <= df["Допуск"] + 1e-9, "OK", "РАСХОЖДЕНИЕ")
    return df


# ════════════════════════════════════════════════════════════════════════════
# 7. ГРАФИКИ (matplotlib)
# ════════════════════════════════════════════════════════════════════════════
INK, TEAL, GREY, CLAY, GRID = "#2B2F38", "#0F7A70", "#8A93A0", "#C65D47", "#E6E8EB"


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GREY)
    ax.tick_params(colors=GREY, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def plot_all(inp: Inputs, bp: BridgeParams, out: Path) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

    out.mkdir(parents=True, exist_ok=True)
    paths = []

    # 1) Мост прибыли
    steps = waterfall_steps(inp, bp, SCENARIOS[1], SCENARIOS[2])
    fig, ax = plt.subplots(figsize=(12, 5.5))
    level, ymin = 0.0, 170
    for i, (label, val, kind) in enumerate(steps):
        if kind == "total":
            ax.bar(i, val - ymin, bottom=ymin, color=INK if label != "Апсайд" else TEAL, width=0.62)
            level = val
            ax.text(i, val + 0.8, f"{val:.1f}", ha="center", fontsize=10, fontweight="bold", color=INK)
        else:
            new = level + val
            ax.bar(i, abs(val), bottom=min(level, new), width=0.62, color=TEAL if val >= 0 else GREY)
            ax.text(i, max(level, new) + 0.8, f"{val:+.1f}", ha="center", fontsize=9.5,
                    color=TEAL if val >= 0 else "#555C68")
            level = new
    ax.axvline(7.5, color=GREY, ls=":", lw=1)
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([textwrap.fill(s[0].strip(), 12) for s in steps], fontsize=8.5, color=INK)
    ax.set_ylim(ymin, max(s[1] for s in steps) + 12)
    ax.set_ylabel("Прибыль владельца после налога, тыс. сом/мес", color=INK, fontsize=9.5)
    ax.set_title("Мост прибыли: сегодня → база → апсайд (ось начинается со 170)", loc="left", color=INK, fontsize=11)
    _style(ax)
    fig.tight_layout()
    p = out / "bridge.png"; fig.savefig(p, dpi=150); plt.close(fig); paths.append(p)

    # 2) Карта «цена × загрузка»
    m = sensitivity_map(inp)
    fig, ax = plt.subplots(figsize=(11, 6.2))
    cmap = LinearSegmentedColormap.from_list("div", [CLAY, "#F4F1EE", TEAL])
    vals = m.values
    im = ax.imshow(vals, cmap=cmap, norm=TwoSlopeNorm(vmin=vals.min(), vcenter=0, vmax=vals.max()), aspect="auto")
    ax.set_xticks(range(m.shape[1])); ax.set_xticklabels([c.replace(" ", "\n") for c in m.columns], fontsize=9)
    ax.set_yticks(range(m.shape[0])); ax.set_yticklabels(m.index, fontsize=9.5)
    ax.xaxis.tick_top()
    def _lum(rgb):  # относительная яркость (WCAG)
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb[:3]]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    norm = im.norm
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            white_ok = 1.05 / (_lum(cmap(norm(vals[i, j]))) + 0.05) >= 4.5   # контраст белого текста ≥ 4,5
            ax.text(j, i, f"{vals[i, j]:.1f}", ha="center", va="center", fontsize=9.5,
                    color="white" if white_ok else INK)
    ti, tj = OCC_GRID.index(inp.occupancy), ADR_GRID.index(0.0)
    ax.add_patch(plt.Rectangle((tj - 0.5, ti - 0.5), 1, 1, fill=False, lw=3, ec="black"))
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_ylabel("Загрузка"); ax.set_xlabel("")
    fig.suptitle(f"Прибыль владельца после налога, тыс. сом/мес (безубыточность ≈{break_even_occupancy(inp):.0%} загрузки)",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout()
    p = out / "price_occupancy_map.png"; fig.savefig(p, dpi=150); plt.close(fig); paths.append(p)

    # 3) Стресс-тесты: потеря прибыли по шокам
    st = stress_tests(inp)
    st = st[st["Шок"] != "База"].iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = [CLAY if cs else GREY for cs in st["В кейсе"]]
    ax.barh(st["Шок"], st["Δ, тыс."], color=colors, height=0.6)
    for y, (d, pct, prof) in enumerate(zip(st["Δ, тыс."], st["Δ, %"], st["Прибыль владельца"])):
        ax.text(d - 1.5, y, f"{d:.1f} ({pct:.0%}) → {prof:.1f}", va="center", ha="right", fontsize=9, color=INK)
    ax.set_xlim(st["Δ, тыс."].min() * 1.75, 0)
    ax.set_xlabel("Изменение прибыли владельца, тыс. сом/мес (база 192,5)", color=INK, fontsize=9.5)
    ax.set_title("Стресс-тесты: каждый шок по отдельности (серые — расширения сверх таблицы кейса)",
                 loc="left", color=INK, fontsize=11)
    _style(ax); ax.yaxis.grid(False); ax.xaxis.grid(True, color=GRID)
    fig.tight_layout()
    p = out / "stress_tests.png"; fig.savefig(p, dpi=150); plt.close(fig); paths.append(p)
    return paths


# ════════════════════════════════════════════════════════════════════════════
# 8. ЗАПУСК
# ════════════════════════════════════════════════════════════════════════════
def _show(title: str, df: pd.DataFrame, fmt: Optional[dict] = None) -> None:
    print(f"\n{'═' * 100}\n{title}\n{'═' * 100}")
    out = df.copy()
    for col, f in (fmt or {}).items():
        out[col] = out[col].map(lambda x, f=f: "–" if pd.isna(x) else format(x, f))
    print(out.to_string(index=not isinstance(df.index, pd.RangeIndex), float_format=lambda x: f"{x:,.2f}"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Модель прибыльности отеля: юнит-экономика, стресс-тесты, мост прибыли")
    ap.add_argument("--out", help="папка для CSV и PNG (если не задана — только вывод в консоль)")
    ap.add_argument("--no-plots", action="store_true", help="не строить графики")
    args = ap.parse_args(argv)

    inp, bp = Inputs(), BridgeParams()
    b = baseline(inp)
    per_night, per_room, cascade = unit_economics(inp)
    calib = calibration(inp)
    stress = stress_tests(inp)
    scen = scenario_table(inp, bp)
    smap = sensitivity_map(inp)
    check = verify(inp, bp)
    mv = marginal_values(inp)

    print(f"Прибыль владельца: {b['profit']:.1f} тыс. сом/мес, маржа {b['margin']:.1%}; "
          f"безубыточная загрузка {break_even_occupancy(inp):.1%} (запас {(inp.occupancy - break_even_occupancy(inp)) * 100:.1f} п.п.)")
    _show("1. ЮНИТ-ЭКОНОМИКА — на проданную ночь, сом", per_night, {"Значение": ",.0f"})
    _show("   на номер в месяц, тыс. сом", per_room, {"Значение": ",.1f"})
    _show("   куда уходят каждые 100 сом выручки", cascade, {"тыс. сом/мес": ",.1f", "на 100 сом выручки": ",.1f"})
    _show("   сверка загрузки, ADR и выручки (раздел 4)", calib, {"Значение": ",.3f"})
    print(f"\n   +1% цены = +{mv['price_1pct']:.1f} тыс./мес;  +1 п.п. загрузки = +{mv['occupancy_1pt']:.1f} тыс./мес")
    print(f"   Безубыточность по прейскурантному ADR: {break_even_occupancy(inp, True, False):.1%} до налога, "
          f"{break_even_occupancy(inp, True):.1%} после налога")

    _show("2. СТРЕСС-ТЕСТЫ, тыс. сом/мес", stress,
          {"Выручка": ",.1f", "Постоянные": ",.1f", "Расходники": ",.1f", "Комиссия": ",.1f", "Налог": ",.1f",
           "Прибыль владельца": ",.1f", "Δ, тыс.": ",.1f", "Δ, %": ".0%", "Маржа": ".1%", "Рычаг, ×": ".1f"})
    print(f"\n   Запас прочности по выручке: прибыль обнуляется при падении выручки на {-revenue_safety_margin(inp):.1%}")
    _show("   карта «цена × загрузка»: прибыль владельца, тыс. сом/мес", smap, {c: ",.1f" for c in smap.columns})

    _show("3. МОСТ ПРИБЫЛИ — сценарии, тыс. сом/мес", scen, {c: ",.1f" for c in scen.columns})
    rp = rent_protection(inp, bp)
    print(f"\n   Рычаг 1 (вне моста): защита аренды стоит {rp['monthly_low']:.1f}–{rp['monthly_high']:.1f} тыс./мес, "
          f"{rp['horizon_low'] / 1000:.2f}–{rp['horizon_high'] / 1000:.2f} млн за {bp.horizon_months} мес.")
    print(f"   Пересмотр цен в контрактах окупается, пока потеря объёма < {contract_breakeven_volume_loss(inp, bp):.1%}")
    steps = pd.DataFrame(waterfall_steps(inp, bp, SCENARIOS[1], SCENARIOS[2]), columns=["Шаг", "Значение", "Тип"])
    _show("   шаги моста (после налога)", steps, {"Значение": ",.1f"})

    bad = check[check["Статус"] != "OK"]
    print(f"\n{'═' * 100}\n4. СВЕРКА С ЦИФРАМИ КЕЙСА\n{'═' * 100}")
    if len(bad):
        print(bad[["Показатель", "Кейс", "Модель", "Разница", "Допуск"]].to_string(index=False))
    print(f"Проверено показателей: {len(check)}; сходится: {(check['Статус'] == 'OK').sum()}; расхождений: {len(bad)}")

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for name, df in [("unit_economics_per_night", per_night), ("unit_economics_per_room", per_room),
                         ("cost_cascade_100_som", cascade), ("calibration", calib), ("stress_tests", stress),
                         ("price_occupancy_map", smap), ("bridge_scenarios", scen),
                         ("bridge_steps", steps), ("verification", check)]:
            df.to_csv(out / f"{name}.csv", encoding="utf-8-sig", index=not isinstance(df.index, pd.RangeIndex))
        if not args.no_plots:
            for p in plot_all(inp, bp, out):
                print(f"   график: {p}")
        print(f"   таблицы сохранены в {out.resolve()}")
    return 1 if len(bad) else 0


if __name__ == "__main__":
    sys.exit(main())
