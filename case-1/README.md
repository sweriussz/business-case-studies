# Case 1 — Profitability and Lease-Risk Analysis of an 8-Room Corporate Hotel

**Industry:** Hospitality (small-format, corporate-focused accommodation)
**Market:** Central Asian capital city
**Currency:** local som; USD figures at 87.45 som per USD (21 October 2026)
**Data basis:** owner-reported, unaudited

> **Terminology.** *Owner* or *operator* refers to the tenant who runs the hotel; *landlord* refers to the owner of the building. *Owner profit* is the profit left to the operator after rent, all operating costs and the single tax, before any salary for the owner's own labour.

---

## At a Glance

| Metric | Result |
|---|---|
| Owner profit | ≈192.5k som per month (≈$2.2k) |
| Margin after single tax | 24.1% bottom-up (owner reported ≈25%) |
| Break-even occupancy | ≈69% on reported revenue (≈64% at list ADR), against 94% today |
| Annual return on capital invested | ≈4.2× on ≈0.55M som (excludes the owner's unpaid labour) |
| Rent relative to profit | Rent is 43.8% of revenue and 1.8× owner profit |

---

## Business Context

- Eight standard double rooms; accommodation only (no food and beverage), so accommodation is 100% of revenue.
- Reported performance: 94% average annual occupancy, average daily rate (ADR) of 3,755 som, revenue of about 800k som per month.
- Sales mix by nights: roughly 77–80% from about 50 one-year corporate contracts (fixed prices, no discounts or commissions), about 20% from an online travel agency (23% commission) and about 3% from social media. Two mobile operators together account for about 8% of occupancy.
- Fixed-rent lease: 3-year term with renewal and no indexation for the first 5 years. The landlord funded the building (about 70M som) and carries all capital expenditure. The operator invested about 200k som in refurbishment and a deposit of one month's rent (350k som).
- Four staff; no hired manager.

## Problem Statement

A hotel reporting 94% occupancy and a healthy margin raises questions that headline figures do not answer:

1. What does the hotel earn on a bottom-up basis, and does it agree with the reported margin?
2. How far can occupancy or revenue fall before profit disappears, and which shocks matter most?
3. With occupancy close to its ceiling, which growth levers are still available?
4. How exposed is the business to its lease, its largest single cost, and what would a less favourable renewal cost?

A fifth, data-quality question emerged during the work: the three headline figures reported by the owner (occupancy, ADR and revenue) do not reconcile with one another.

## Methodology & Frameworks

| Technique | Application in this case |
|---|---|
| Unit economics | Profit per sold night and per room per month; cost cascade showing where each 100 som of revenue goes |
| Cost-structure and operating-leverage analysis | Separation of fixed costs (rent, payroll, electricity, water) from revenue-linked costs (supplies, commission, single tax) |
| Break-even and marginal analysis | Break-even occupancy; profit value of 1% of price versus 1 point of occupancy |
| Two-way sensitivity map | Owner profit across occupancy (65–96%) and ADR change (−5% to +10%) |
| Data reconciliation | Calibration factor of 0.931 linking occupancy × ADR × room-nights to reported revenue |
| Stress testing | Six single-factor shocks, plus three extensions in the model (heating-month electricity, payroll contributions added on top, a combined revenue and rent shock) |
| Scenario analysis and profit bridge | Conservative, base and upside programmes; payback and 36-month net effect |
| Return-on-capital comparison | Landlord versus operator-owner |
| Implementation planning | 30 / 60 / 90-day plan with control metrics |

**Tools.** A formula-driven Excel model (inputs, baseline, unit economics, stress tests, profit bridge, sensitivity map and a reconciliation sheet) with colour-coded inputs, assumptions and formulas, replicated in Python (pandas, NumPy, Matplotlib). The Python model checks 68 outputs against the figures printed in the case study. AI tools were used to help structure and refine the analysis.

**Evidence base.** A structured written interview with the owner (32 questions on business model, unit economics, costs, sales channels and risks) and a few follow-up figures. Where data was unclear or did not tie, the case states the assumption used.

**Validation.** Methodology and findings were reviewed and validated by the school's economics faculty advisor to ensure analytical rigor and academic integrity.

---

## Key Findings & Analysis

### 1. A profitable business that rests on a single lease

- Revenue of 800k som less costs of 573.1k and single tax of 34.4k leaves **192.5k som a month (24.1%)**; the margin is about 29% before the single tax and the owner keeps 152.5k after a 5% reserve for furniture and equipment.
- Fixed costs of 518.8k som absorb about 65% of revenue. **Rent alone is 350k som, 43.8% of revenue and 1.8× owner profit.**
- Only 24 of every 100 som of revenue reach the owner:

| Where 100 som of revenue goes (rounded) | som |
|---|---|
| Rent | 43.8 |
| Payroll and contributions | 12.8 |
| Electricity and water | 8.3 |
| Supplies | 2.2 |
| Online travel agency commission | 4.6 |
| Single tax | 4.3 |
| **Owner profit** | **24.1** |

- Landlord and operator-owner earn very differently on the same asset:

| | Landlord | Operator-owner |
|---|---|---|
| Capital invested | ≈70M som | ≈0.55M som (200k refurbishment + 350k deposit) |
| Annual cash income | 4.2M som (rent) | ≈2.3M som (after single tax) |
| Annual return on capital | 6.0% gross yield | ≈4.2× |
| Capital recovered from income | ≈16.7 years | ≈3 months |
| Main exposure | Building capital expenditure | Lease renewal: +10% rent costs 35k som a month (18% of profit) |

The 4.2× figure excludes the owner's unpaid labour (with a manager at 60k som a month it would be ≈2.9×) and a one-month cash cushion (counting it gives ≈2.0–2.6×).

### 2. At 94% occupancy, price is the only free lever

- **+1% price is worth about 7.3k som a month; +1 point of occupancy about 7.6k.** Moving from 94% to 100% would add only 6.4% volume, and practical headroom is estimated at 1–2 points.
- Process audit observations: prices are set by hand within a 3,500–4,000 som corridor (a 14% spread) although weekends and city events already fill the hotel; RevPAR is not tracked; the average stay is 2 nights, while stays of 3 nights or more are more profitable.

### 3. The three reported headline figures do not tie

- Occupancy × ADR × room-nights implies 858.9k som a month against reported revenue of 800k: a gap of about 58.9k a month (≈0.7M a year).
- Reconciling them requires either an ADR of ≈3,498 som or an occupancy of ≈87.6%. The cause could not be established because follow-up questions were no longer possible.
- Treatment: reported revenue is the anchor of the model, so price, cost and margin results do not depend on which figure is off; break-even and the value of an occupancy point do, and are therefore stated on the reported-revenue basis. A monthly reconciliation against booking and payment records is recommended.

### 4. Profit survives any single shock, but revenue shocks are amplified about 3.7×

| Shock (one at a time) | Owner profit, k som/month | Change |
|---|---|---|
| Baseline | 192.5 | — |
| Revenue −10% | 121.4 | −37% |
| Revenue −15% | 85.8 | −55% |
| Loss of the two mobile-operator accounts (−8% revenue) | 132.7 | −31% |
| Rent +10% | 157.5 | −18% |
| Electricity +20% | 180.5 | −6% |
| Hired manager at 60k som | 132.5 | −31% |

- Break-even occupancy is **≈69%** after tax on reported revenue (a safety margin of about 25 points) and **≈64%** at list ADR (about 30 points).
- In a heating month, electricity of 100k som lowers that month's profit by 40k; if payroll contributions of 12.25% are charged on top of the reported payroll, profit would be ≈182k (22.8%).
- The owner names the loss of a trained employee (the team has four people) as the main operational risk.

---

## Recommendations & Business Impact

Five actions, in this order:

1. **Protect the lease first.** Open renewal talks for a longer term and an indexation cap. A reset of +5–10% would cost 17.5–35.0k som a month, or 0.6–1.3M som over three years, more than the base programme earns over the same period (≈0.5M).
2. **Raise prices on non-contract nights** (23% of nights) within a 3,500–4,400 som corridor, with fences for peak dates and a 2–3-night minimum stay on peaks.
3. **Sell the online travel agency channel only on dates corporate demand does not fill.** Each night sold there costs ≈804 som in commission; moving 4 points of nights saves ≈7.8k som a month.
4. **Reprice corporate contracts at each prolongation** (about four a month, +4%), stopping if contract attrition exceeds 3.7%, the break-even point.
5. **Reconcile occupancy, ADR and revenue every month**, because break-even and the value of an occupancy point depend on which figure is correct.

**Programme scenarios** (owner profit after single tax; one-off cost of ≈180k som, estimated without supplier quotes):

| | Conservative | Base | Upside |
|---|---|---|---|
| Price on non-contract nights | +4% | +8% | +8% |
| Volume lost on non-contract nights | 3% | 2% | 2% |
| Nights moved off the online agency | 2 pts | 4 pts | 4 pts |
| Electricity saving | 5% | 10% | 10% |
| Contract repricing | not applied | not applied | +4% on 90% of contract revenue; 1% volume lost |
| Change in owner profit, k som/month | ≈0 | +14.0 | +29.5 |
| Owner profit after programme, k som/month | ≈192.8 | 206.5 (+7%) | 222.0 (+15%) |
| Payback of one-off cost | not recovered | ≈13 months | ≈6 months |
| Net effect over 36 months | negative | ≈0.3M som | ≈0.9M som |

**Business impact.** In the base case, owner profit rises from 192.5k to 206.5k som a month (+7%), and to 222.0k (+15%) with contract repricing. Lease protection is not counted in the bridge but is the largest single value at stake. A 30 / 60 / 90-day plan sequences the work: lease talks, price corridor and channel rules and a monthly reconciliation in the first 30 days; the contract-renewal calendar in days 31–60; completion of energy works and a comparison against the base case in days 61–90 (control metric: owner profit of about 207k som a month).

## Limitations & Assumptions

- All figures were reported by the owner and not audited. Assumptions are flagged in the Excel model (yellow fill) and in the Python model.
- Assumptions made by the author: supplies at the midpoint of the reported 15–20k range; 15% of receipts in cash for the single-tax blend (4.3%); payroll and contributions carried at 102.3k; the size of a possible rent reset (+5–10%); the price, volume, channel and energy effects in the scenarios.
- Implementation costs (20k, 120k, 30k and 10k som) are estimates; payback and the 36-month effect should be read as ranges.
- Contract repricing assumes prices can be revised at prolongation; the upside depends on renewal terms.
- Lease protection in years 4–5 could not be clarified and is treated as the risk point.

---

## Directory Contents

| File | Description |
|---|---|
| `README.md` | This document |
| Case study document (English and Russian) | Full written analysis |
| `Hotel_Model.xlsx` | Formula-driven Excel model (7 sheets) |
| `hotel_model.py` | Python replication of the model with automated reconciliation |
| Interview Q&A (anonymized) | Structured owner interview used as the data source |

**Reproducing the results**

```bash
pip install pandas numpy matplotlib
python hotel_model.py                       # tables in the console + reconciliation
python hotel_model.py --out results         # also writes CSV tables and PNG charts
```

Console output and table labels are in Russian. The script exits with a non-zero status if any of the 68 reconciliation checks fails.

## Data & Verification Note

Underlying calculation models and anonymized data files are included in this directory. Source contact details are available upon request. The hotel, its operator, the landlord and its corporate clients are not named.
