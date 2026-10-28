# Small-Business Case Studies: Financial Modeling and Strategic Analysis in an Emerging Market

Two independent, field-based case studies of owner-operated small businesses in a Central Asian capital city. One is a financial-modeling study of a corporate hotel; the other is a strategic and unit-economics study of an independent electronics retailer.

## Project Overview and Objective

The objective of this project is to apply core business and finance tools to real operating data from small enterprises, a setting where audited accounts rarely exist and information comes from owners themselves. Each case turns owner-reported figures into decision-ready analysis: it reconstructs the economics from the bottom up, tests how fragile they are, identifies the levers that matter, and proposes prioritized actions. Both cases state their data limits and assumptions openly.

| | Case 1 | Case 2 |
|---|---|---|
| Business | 8-room corporate hotel | Independent electronics retailer (15-year history) |
| Sector | Hospitality | Retail |
| Emphasis | Financial modeling and quantitative analysis | Strategy, unit economics and behavioral economics |
| Data source | 32-question structured owner interview and follow-up figures | Audio-recorded owner interview, direct observation and internal operating data |
| Deliverables | Case study, Excel model, Python model | Case study |

## Executive Summary

### Case 1 — Profitability and Lease-Risk Analysis of a Corporate Hotel

**Problem.** An 8-room corporate hotel reports 94% occupancy and a healthy margin, but it is unclear how resilient that profit is, which growth levers remain, and how exposed the business is to its lease. **Methodology.** The case reconstructs the economics bottom-up through unit economics, break-even analysis, a price-and-occupancy sensitivity map, stress tests and a scenario-based profit bridge, in an Excel model replicated in Python. **Findings.** The hotel earns about 192.5k som a month (24.1% margin), roughly 4.2× its ≈0.55M som of invested capital each year, but rent equals 43.8% of revenue and 1.8× profit, and a 15% fall in revenue would cut profit by 55%. **Impact.** A prioritized programme that starts with lease protection and pricing on non-contract nights lifts owner profit by about 7% (base) to 15% (upside) for a one-off cost of ≈180k som, with payback in roughly 13 and 6 months.

### Case 2 — Unit Economics and Brand Positioning of an Electronics Retailer

**Problem.** A family-operated electronics retailer with a 15-year history holds a prime location in a central department store, yet it is nearly invisible to new visitors while a better-presented competitor captures their first attention. **Methodology.** The study applies the Business Model Canvas, unit-economics analysis, seasonality mapping, competitive positioning and behavioral economics to owner interviews, direct observation and internal operating data. **Findings.** Laptops bring about 30% of revenue at a flat ≈$80 margin per unit, while accessories, builds and repairs bring about 70% at a ≈30% markup and carry a fixed-cost floor of ≈340–350k som a month through two dry seasons totalling about four months; the core asset is trust held by the "expert" who accompanies student buyers, and it is generationally finite. **Impact.** A three-tier roadmap moves from near-zero-budget quick wins (signage, a digital catalogue, business-to-business outreach) to counter-seasonal service revenue and easier installment financing, then to supply and margin de-risking; the impact is directional, as the case does not model financial projections.

## Repository Structure

```text
.
├── README.md                      # Project overview (this file)
├── case-1/                        # Corporate hotel: profitability and lease risk
│   ├── README.md                  # Case summary, findings, recommendations
│   ├── Hotel_Profitability_Case_Study.docx   # Full case study (English and Russian)
│   ├── Hotel_Model.xlsx           # Formula-driven Excel model (7 sheets)
│   ├── hotel_model.py             # Python replication with automated reconciliation
│   └── interview_qa_anonymized.docx          # Anonymized owner interview (Q&A)
└── case-2/                        # Electronics retailer: unit economics and positioning
    ├── README.md                  # Case summary, findings, recommendations
    └── Electronics_Retail_Case_Study.docx    # Full case study (English and Russian)
```

## Skills & Methodology

**Financial modeling**
- Unit economics per sold night, per room and per 100 currency units of revenue
- Contribution margin, fixed/variable cost structure and operating leverage
- Break-even analysis and two-way sensitivity maps
- Scenario analysis, profit bridges, payback and multi-year net-effect estimates
- Return-on-capital comparison between landlord and operator

**Quantitative analysis**
- Stress testing of revenue, rent, electricity and staffing shocks
- Data reconciliation and calibration when reported figures do not tie
- Marginal analysis (value of 1% of price versus 1 point of occupancy)
- Excel (formula-driven, with colour-coded inputs, assumptions and formulas) and Python (pandas, NumPy, Matplotlib)

**Process and operations audit**
- Pricing practice, channel management and revenue-management gaps
- Inventory, sourcing, defect-cost and installment-financing process friction
- Seasonality mapped against fixed-cost commitments

**Strategy frameworks**
- Business Model Canvas
- Porter-style competitive and brand positioning
- Behavioral economics (information asymmetry, trust as a switching cost, expert-assisted purchasing)
- Tiered roadmaps and 30 / 60 / 90-day implementation plans

**Research practice**
- Structured interviews (including a 32-question written interview), audio recording and direct observation
- Explicit assumption logging; ranges and caveats where data was unclear
- Bilingual (English and Russian) case write-ups
- Methodology and findings were reviewed and validated by the school's economics faculty advisor to ensure analytical rigor and academic integrity.

AI tools were used to help structure and refine the analysis in Case 1, as disclosed in that case study.

## Data Integrity & Verification

All sensitive business data and direct contact details of data sources are anonymized/withheld for privacy, but official verification is available upon request.

- All figures are as reported by business owners and were not audited. Where data did not tie or was unclear, the case studies state the assumption used.
- Case 1 includes a reconciliation of the Python model to the case study (68 checks) and a reconciliation sheet in the Excel model.
- Case 2 relies on rounded, owner-reported estimates; its author had access to the business through a personal connection with its ownership, which the case study discloses.
- Businesses, owners, landlords, competitors, suppliers and corporate clients are not named.

## Reproducing the Case 1 Model

```bash
pip install pandas numpy matplotlib
cd case-1
python hotel_model.py --out results
```

See [`case-1/README.md`](case-1/README.md) and [`case-2/README.md`](case-2/README.md) for the full summaries of each case.
