"""
Competition Department — Automated Operations  (ILLUSTRATIVE PROTOTYPE)

A demo of how a competition authority's daily work can be automated end to end, applied to the
online food delivery market and to the UAE competition framework (Federal Decree-Law No. 36 of 2023,
Cabinet Resolution No. 3 of 2025, Cabinet Decision No. 59 of 2026, Cabinet Resolution No. 105 of 2026,
Ministerial Decision No. 32 of 2026, Dubai Guidelines for Online Food Delivery Platforms).

All six platforms, every firm, case, complaint and figure are invented. API connections are simulated.
This is not an official system of any government entity.

Run:      streamlit run app.py
Requires: streamlit>=1.35, plotly, pandas, numpy
"""

import html
import time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================================
# LOOK & FEEL
# ============================================================================
INK, PRIMARY, PRIMARY_DK, PRIMARY_MD = "#12303F", "#1C7C9C", "#155E76", "#4B9DB8"
PRIMARY_LT, PRIMARY_XL, GOLD = "#9FCAD8", "#DCEAF0", "#D9A441"
BG, BORDER, MUTED = "#F5F7F9", "#E2E8EC", "#5F707A"
OK, WARN, ALERT = "#2E9E7B", "#E1A32E", "#CE4B48"
PCOL = {"Nexa Eats": "#1C7C9C", "Dunebite": "#D9A441", "Saffron Go": "#B4553A",
        "Falcon Feast": "#2E9E7B", "Palm Plate": "#64748B", "Oasis Delivery": "#7B6BB0"}

PAGES = ["Overview", "Data sources", "Merger control", "Market monitoring (ex-ante)",
         "Complaints & sentiment", "Authority statistics", "Methodology"]

# ============================================================================
# UAE LEGAL FRAMEWORK  (as researched, October 2026)
# ============================================================================
LEGAL = [
    ("Federal Decree-Law No. 36 of 2023 on the Regulation of Competition", "2023",
     "Core law: restrictive agreements (Art. 5), abuse of dominance (Art. 6), abuse of economic dependence (Art. 7), "
     "predatory pricing (Art. 8), economic concentrations (Arts. 12–15), Ministry powers incl. market studies (Art. 18), "
     "penalties (Arts. 24–27), complaints (Arts. 32, 34)."),
    ("Cabinet Resolution No. 3 of 2025 (thresholds)", "In force 31 March 2025",
     "Merger filing required if annual sales in the relevant UAE market exceed AED 300 million or combined market share "
     "exceeds 40%; either threshold may be met by one party alone."),
    ("Cabinet Decision No. 59 of 2026 (Executive Regulations)", "In force 30 July 2026",
     "Replaces the 2014 regulations: completeness review (10 business days), third-party observations (15 working days), "
     "dominance criteria, below-cost pricing, complaints and ex officio investigations, settlements."),
    ("Cabinet Resolution No. 105 of 2026 (fees)", "Fees payable from 12 July 2026",
     "Merger filing fee of 0.02% of the parties' aggregate annual turnover, capped at AED 150,000."),
    ("Ministerial Decision No. 32 of 2026 (food delivery block exemption)", "Issued 11 February 2026",
     "Exclusive dealing between delivery platforms and restaurants exempted only if exclusivity lasts at most 12 months, "
     "covers no more than 10% of a platform's listed restaurants, and has no post-exclusivity non-compete."),
    ("Dubai Guidelines for Online Food Delivery Platforms (DCCPFT)", "2026",
     "Multi-homing without penalty; itemised fees; 30 days' notice for contract changes; no self-preferencing of "
     "own brands or affiliated cloud kitchens; 100% of tips to riders."),
    ("Guidelines on Relevant Market Definition", "July 2026",
     "Demand-side substitution, SSNIP test (5–10%); geographic markets may be local, national or digital."),
]
MERGER_REVIEW_DAYS, MERGER_EXTENSION = 90, 45
FEE_RATE, FEE_CAP = 0.0002, 150_000
TURNOVER_THRESHOLD, SHARE_THRESHOLD = 300, 40          # AED million ; %
EXCLUSIVITY_CAP = 10                                   # % of listed restaurants (Ministerial Decision 32/2026)

# ============================================================================
# MOCK MARKET: six invented food delivery platforms
# ============================================================================
MONTHS = pd.period_range("2023-01", "2026-09", freq="M")
T = len(MONTHS)
PLATFORMS = {
    #             order share path                                   commission path (%)                         2025 revenue (AED m)
    "Nexa Eats": dict(share=[("2023-01", 44), ("2024-12", 47), ("2026-09", 42)], comm=[("2023-01", 25), ("2026-09", 27)], rev=1450),
    "Dunebite": dict(share=[("2023-01", 24), ("2024-12", 21), ("2026-09", 20)], comm=[("2023-01", 23), ("2026-09", 24)], rev=690),
    "Saffron Go": dict(share=[("2023-01", 14), ("2024-12", 13), ("2026-09", 12)],
                       comm=[("2023-01", 19), ("2026-05", 19), ("2026-06", 22), ("2026-09", 22)], rev=410),
    "Falcon Feast": dict(share=[("2024-03", 0.8), ("2024-12", 3), ("2026-09", 10)], comm=[("2024-03", 14), ("2026-09", 15)],
                         rev=260, enter="2024-03"),
    "Palm Plate": dict(share=[("2023-01", 10), ("2024-12", 9), ("2026-09", 9)], comm=[("2023-01", 19), ("2026-09", 19)], rev=300),
    "Oasis Delivery": dict(share=[("2023-01", 8), ("2024-12", 7), ("2026-09", 7)], comm=[("2023-01", 18), ("2026-09", 18)], rev=220),
}
NAMES = list(PLATFORMS)

# Platform-reported compliance data (latest month)
AOV = 62.0   # average order value, AED
COMPLIANCE_DATA = {
    # excl: exclusive restaurants %, excl_months: longest exclusivity, own_top / own_list: own brands in top-10 results / in listings %,
    # notice: days' notice of contract changes, tips: % of tips paid to riders, itemised: fees shown before checkout,
    # comm: commission %, fee: delivery fee AED, avc: average variable cost per order AED (riders, payments, support),
    # dependent: % of the platform's restaurants earning >60% of online sales on it
    "Nexa Eats":      dict(excl=14.2, excl_months=12, own_top=5, own_list=4, notice=30, tips=100, itemised=True, comm=27, fee=7.0, avc=10.6, dependent=48),
    "Dunebite":       dict(excl=6.1, excl_months=9, own_top=21, own_list=6, notice=30, tips=100, itemised=True, comm=24, fee=6.5, avc=10.5, dependent=19),
    "Saffron Go":     dict(excl=3.4, excl_months=6, own_top=0, own_list=0, notice=7, tips=100, itemised=True, comm=22, fee=6.0, avc=10.2, dependent=9),
    "Falcon Feast":   dict(excl=0.0, excl_months=0, own_top=0, own_list=0, notice=30, tips=100, itemised=True, comm=15, fee=0.0, avc=10.4, dependent=4),
    "Palm Plate":     dict(excl=2.0, excl_months=6, own_top=0, own_list=0, notice=30, tips=100, itemised=True, comm=19, fee=6.0, avc=10.1, dependent=6),
    "Oasis Delivery": dict(excl=0.0, excl_months=0, own_top=0, own_list=0, notice=30, tips=86, itemised=False, comm=18, fee=5.5, avc=9.8, dependent=5),
}


def revenue_per_order(d):
    """Platform revenue per order = commission on the average order + delivery fee charged to the consumer."""
    return d["comm"] / 100 * AOV + d["fee"]


def _path(points):
    idx = [MONTHS.get_loc(pd.Period(p, "M")) for p, _ in points]
    return np.interp(np.arange(T), idx, [v for _, v in points])


@st.cache_data(show_spinner=False)
def market():
    rng = np.random.default_rng(21)
    total = 13.0e6 * 1.01 ** np.arange(T) * (1 + 0.04 * np.sin(2 * np.pi * np.arange(T) / 12))
    raw = {}
    for p, c in PLATFORMS.items():
        s = _path(c["share"]) * (1 + rng.normal(0, 0.01, T))
        if "enter" in c:
            s[: MONTHS.get_loc(pd.Period(c["enter"], "M"))] = 0
        raw[p] = np.clip(s, 0, None)
    tot = sum(raw.values()); rows = []
    for p, c in PLATFORMS.items():
        sh = raw[p] / tot * 100; com = _path(c["comm"]) + rng.normal(0, 0.1, T)
        for t in range(T):
            if sh[t] > 0:
                rows.append(dict(Month=str(MONTHS[t]), Date=MONTHS[t].to_timestamp(), Platform=p, Share=sh[t],
                                 Orders=total[t] * sh[t] / 100, GMV=total[t] * sh[t] / 100 * 62, Commission=com[t]))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- geography (emirate level)
EMIRATES = {   # name: (lat, lon, share of national orders) — points placed on land, slightly inland of each city
    "Abu Dhabi": (24.40, 54.50, .30), "Dubai": (25.15, 55.33, .42), "Sharjah": (25.30, 55.48, .14),
    "Ajman": (25.39, 55.55, .06), "Umm Al Quwain": (25.52, 55.66, .015),
    "Ras Al Khaimah": (25.74, 55.98, .04), "Fujairah": (25.13, 56.30, .025)}
REGIONAL_TILT = {   # relative strength of each platform by emirate (1 = national average)
    "Nexa Eats": {"Dubai": 1.05},
    "Dunebite": {"Dubai": 1.1, "Fujairah": 0.8, "Abu Dhabi": 0.9},
    "Saffron Go": {"Abu Dhabi": 1.25, "Dubai": 0.85},
    "Falcon Feast": {"Dubai": 1.35, "Abu Dhabi": 0.8, "Fujairah": 0.5, "Umm Al Quwain": 0.6, "Ras Al Khaimah": 0.6},
    "Palm Plate": {"Abu Dhabi": 1.45, "Dubai": 0.7},
    "Oasis Delivery": {"Sharjah": 1.7, "Ajman": 1.8, "Umm Al Quwain": 1.8, "Ras Al Khaimah": 1.6, "Fujairah": 1.5, "Dubai": 0.75},
}
HEADQUARTERS = {"Nexa Eats": "Dubai", "Dunebite": "Dubai", "Saffron Go": "Abu Dhabi", "Falcon Feast": "Dubai",
                "Palm Plate": "Abu Dhabi", "Oasis Delivery": "Sharjah"}
HQ_POINTS = {   # invented office locations, all on land: (lat, lon, label position)
    "Nexa Eats": (25.19, 55.28, "top left"),          # central Dubai
    "Falcon Feast": (25.20, 55.43, "top right"),      # eastern Dubai
    "Dunebite": (25.05, 55.25, "bottom right"),       # southern Dubai
    "Saffron Go": (24.47, 54.38, "top left"),         # Abu Dhabi city
    "Palm Plate": (24.36, 54.53, "bottom right"),     # Abu Dhabi mainland
    "Oasis Delivery": (25.30, 55.50, "top right"),    # Sharjah, inland
}


@st.cache_data(show_spinner=False)
def emirate_shares():
    """Platform shares by emirate (latest month). Regional tilts are balanced so that the order-weighted
    average across emirates equals each platform's national share exactly."""
    nat = latest_shares(); em = list(EMIRATES); w = np.array([EMIRATES[e][2] for e in em])
    n = np.array([nat[p] for p in NAMES])
    M = np.array([[nat[p] * REGIONAL_TILT[p].get(e, 1.0) for p in NAMES] for e in em])
    for _ in range(200):
        M = M / M.sum(1, keepdims=True) * 100
        M = M * (n / ((w[:, None] * M).sum(0) / w.sum()))
    M = M / M.sum(1, keepdims=True) * 100
    rows = []
    for i, e in enumerate(em):
        for j, p in enumerate(NAMES):
            rows.append(dict(Emirate=e, Platform=p, Share=float(M[i, j]), Lat=EMIRATES[e][0], Lon=EMIRATES[e][1],
                             OrderWeight=EMIRATES[e][2]))
    return pd.DataFrame(rows)


def local_check(a, b):
    """Merged share and rank of a + b in every emirate."""
    df = emirate_shares(); out = []
    for e, g in df.groupby("Emirate", sort=False):
        sh = dict(zip(g["Platform"], g["Share"])); merged = sh[a] + sh[b]
        rank = 1 + sum(v > merged for k, v in sh.items() if k not in (a, b))
        leader = max((v for k, v in sh.items() if k not in (a, b)))
        out.append(dict(Emirate=e, merged=merged, rank=rank, leader=leader))
    return out


def uae_map(selected):
    df = emirate_shares(); piv = df.pivot(index="Emirate", columns="Platform", values="Share").reindex(list(EMIRATES))
    m = pd.DataFrame({"Emirate": piv.index, "Lat": [EMIRATES[e][0] for e in piv.index], "Lon": [EMIRATES[e][1] for e in piv.index],
                      "Orders (% of UAE)": [EMIRATES[e][2] * 100 for e in piv.index]})
    m["Leader"] = piv.idxmax(axis=1).values
    m["Detail"] = ["<br>".join(f"{p}: {piv.loc[e, p]:.1f}%" for p in piv.columns[np.argsort(-piv.loc[e].values)]) for e in piv.index]
    if selected == "Leading platform":
        color, cmap, cscale, title = "Leader", PCOL, None, "Leader"
    else:
        m["Share (%)"] = piv[selected].values
        color, cmap, cscale, title = "Share (%)", None, [[0, "#EAF3F6"], [1, PCOL[selected]]], f"{selected} share"
    kw = dict(lat="Lat", lon="Lon", size="Orders (% of UAE)", size_max=45, color=color, hover_name="Emirate",
              hover_data={"Lat": False, "Lon": False, "Orders (% of UAE)": ":.1f", "Detail": True},
              center=dict(lat=24.75, lon=55.1), zoom=6.1, height=470)
    if cmap:
        kw["color_discrete_map"] = cmap
    if cscale:
        kw["color_continuous_scale"] = cscale
    try:
        fig = px.scatter_map(m, map_style="carto-positron", **kw)
    except AttributeError:          # older plotly
        fig = px.scatter_mapbox(m, mapbox_style="carto-positron", **kw)
    hq = pd.DataFrame([dict(Platform=p, Emirate=HEADQUARTERS[p], Lat=HQ_POINTS[p][0], Lon=HQ_POINTS[p][1], Pos=HQ_POINTS[p][2])
                       for p in NAMES])
    # one small trace per headquarters: map traces accept only a single label position per trace
    Trace = getattr(go, "Scattermap", None) or go.Scattermapbox
    for i, r in hq.iterrows():
        fig.add_trace(Trace(lat=[r["Lat"]], lon=[r["Lon"]], mode="markers+text", text=[f"{r['Platform']} HQ"],
                            textposition=r["Pos"], marker=dict(size=10, color=INK), name="Headquarters",
                            legendgroup="hq", showlegend=bool(i == 0), hoverinfo="text",
                            hovertext=[f"{r['Platform']} headquarters, {r['Emirate']}"],
                            textfont=dict(size=11, color=INK)))
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.02, x=0, font=dict(size=11)))
    if cscale:
        fig.update_layout(coloraxis_colorbar=dict(title=title))
    return fig, piv


def latest_shares():
    m = market(); g = m[m["Month"] == m["Month"].max()]
    return {p: float(g.loc[g["Platform"] == p, "Share"].iloc[0]) for p in NAMES}


def hhi(sh):
    return float(sum(v * v for v in sh.values()))


@st.cache_data(show_spinner=False)
def hhi_series():
    m = market()
    return m.groupby("Date")["Share"].apply(lambda s: float((s ** 2).sum())).reset_index(name="HHI")


@st.cache_data(show_spinner=False)
def sentiment_series():
    base = {"Nexa Eats": [("2025-01", 58), ("2026-09", 51)], "Dunebite": [("2025-01", 61), ("2026-09", 59)],
            "Saffron Go": [("2025-01", 63), ("2026-05", 62), ("2026-07", 47), ("2026-09", 46)],
            "Falcon Feast": [("2025-01", 66), ("2026-09", 71)], "Palm Plate": [("2025-01", 62), ("2026-09", 63)],
            "Oasis Delivery": [("2025-01", 58), ("2026-09", 49)]}
    months = pd.period_range("2025-01", "2026-09", freq="M"); rng = np.random.default_rng(4); rows = []
    for p, pts in base.items():
        idx = [months.get_loc(pd.Period(a, "M")) for a, _ in pts]
        v = np.interp(np.arange(len(months)), idx, [b for _, b in pts]) + rng.normal(0, 1.2, len(months))
        rows += [dict(Date=m.to_timestamp(), Platform=p, Sentiment=float(x)) for m, x in zip(months, v)]
    return pd.DataFrame(rows)


COMPLAINT_TEMPLATES = [   # text, complainant, category, route, sentiment, platform weights
    # --- consumers (people ordering food)
    ("Order arrived late and cold", "Consumer", "Service quality", "Consumer protection (MoET / DCCPFT)", -0.6, None),
    ("Refund not processed after cancelled order", "Consumer", "Refunds", "Consumer protection (MoET / DCCPFT)", -0.7, None),
    ("Service fee added after payment, not shown at checkout", "Consumer", "Hidden fees", "Consumer protection (MoET / DCCPFT)", -0.8, {"Oasis Delivery": 5}),
    ("Delivery fee changed between browsing and checkout", "Consumer", "Hidden fees", "Consumer protection (MoET / DCCPFT)", -0.6, {"Oasis Delivery": 3}),
    ("Menu prices on the app higher than in the restaurant", "Consumer", "Price mark-ups", "Consumer protection (MoET / DCCPFT)", -0.5, None),
    ("Fast delivery and helpful support", "Consumer", "Positive feedback", "No action", 0.7, {"Falcon Feast": 3}),
    # --- restaurants (business users of the platforms)
    ("Commission raised with one week's notice", "Restaurant", "Commission terms", "Competition Department", -0.8, {"Saffron Go": 12}),
    ("Told we lose promotions unless we sign exclusivity", "Restaurant", "Exclusivity", "Competition Department", -0.9, {"Nexa Eats": 8}),
    ("Our ranking dropped after we joined another app", "Restaurant", "Retaliation for multi-homing", "Competition Department", -0.8, {"Nexa Eats": 7}),
    ("Platform's own kitchens always shown above us", "Restaurant", "Self-preferencing", "Competition Department", -0.7, {"Dunebite": 9}),
    ("We depend on one app for most of our online sales", "Restaurant", "Economic dependence", "Competition Department", -0.5, {"Nexa Eats": 6}),
    ("Settlement payments delayed beyond agreed terms", "Restaurant", "Late payments", "DCCPFT (commercial terms)", -0.6, None),
    ("Marketing fees added without our consent", "Restaurant", "Unconsented fees", "DCCPFT (commercial terms)", -0.7, {"Dunebite": 2}),
    ("Customer data not shared after we left the platform", "Restaurant", "Data access", "DCCPFT (commercial terms)", -0.4, None),
    # --- riders
    ("Tips are not fully passed to riders", "Rider", "Rider payments", "Consumer protection (MoET / DCCPFT)", -0.7, {"Oasis Delivery": 8}),
    ("Per-delivery pay cut without notice", "Rider", "Rider pay", "Labour authorities (referral)", -0.6, None),
]
COMPETITION_CATEGORIES = {"Commission terms", "Exclusivity", "Retaliation for multi-homing", "Self-preferencing", "Economic dependence"}
LISTED_RESTAURANTS = {"Nexa Eats": 11500, "Dunebite": 6800, "Saffron Go": 4200, "Falcon Feast": 3600,
                      "Palm Plate": 3000, "Oasis Delivery": 2400}
REC_LINK = {"Commission terms": "R3", "Exclusivity": "R1", "Retaliation for multi-homing": "R1", "Self-preferencing": "R2",
            "Economic dependence": "R6", "Rider payments": "R4", "Hidden fees": "R4"}


@st.cache_data(show_spinner=False)
def complaints():
    rng = np.random.default_rng(9); sh = latest_shares(); rows = []
    for d in pd.date_range("2025-10-01", "2026-10-18", freq="D"):
        for text, who, cat, route, sent, w in COMPLAINT_TEMPLATES:
            lam = {"Consumer": 3.0, "Restaurant": 0.45, "Rider": 0.4}[who] / (3 if cat == "Positive feedback" else 1)
            if cat == "Commission terms" and d >= pd.Timestamp("2026-06-01"):
                lam *= 3.0
            for _ in range(rng.poisson(lam)):
                wts = np.array([sh[p] * (w or {}).get(p, 1) for p in NAMES]); wts = wts / wts.sum()
                p = str(rng.choice(NAMES, p=wts))
                rows.append(dict(Date=d, Platform=p, Complainant=who, Text=text, Category=cat, Route=route,
                                 Channel=str(rng.choice(["MoET consumer protection", "DCCPFT", "App reviews"], p=[.35, .35, .30])),
                                 Sentiment=float(np.clip(sent + rng.normal(0, .12), -1, 1)),
                                 Days=int(rng.integers(2, 12))))
    return pd.DataFrame(rows)


# ============================================================================
# DATA SOURCES  (simulated API connections)
# ============================================================================
SOURCES = [
    dict(key="platforms", cat="Market data", name="Food delivery platforms (6)",
         who="Nexa Eats · Dunebite · Saffron Go · Falcon Feast · Palm Plate · Oasis Delivery",
         api="GET /v1/orders · /v1/commissions · /v1/contracts · /v1/rankings", freq="Daily", records=1_284_400,
         data="Orders, GMV, commissions, fees, exclusive contracts, search rankings, rider payouts, costs",
         why="Market shares, concentration, compliance with Ministerial Decision 32/2026 and the Dubai Guidelines"),
    dict(key="efiling", cat="Competition Department", name="Merger e-filing portal",
         who="Ministry of Economy and Tourism · Competition Department",
         api="GET /v1/notifications · /v1/fees", freq="Real-time", records=172,
         data="Economic concentration notifications, documents, fee payments",
         why="Starts the merger workflow and the 90-day clock automatically"),
    dict(key="studies", cat="Competition Department", name="Market studies & case archive",
         who="Competition Department · earlier market studies, investigations and decisions",
         api="GET /v1/studies?sector=food-delivery · /v1/cases", freq="On update", records=214,
         data="Findings, benchmarks and recommendations of earlier market studies; past cases and decisions",
         why="Baselines for early-warning signs; consistency with earlier findings and decisions"),
    dict(key="ner", cat="Government registers", name="National Economic Register",
         who="Ministry of Economy and Tourism",
         api="GET /v1/establishments · /v1/owners", freq="Daily", records=48_210,
         data="Licensed establishments, shareholders, beneficial owners, board members",
         why="Identifies ownership links and the undertakings concerned"),
    dict(key="emirates", cat="Government registers", name="Emirate economic departments",
         who="e.g. Dubai DET, Abu Dhabi ADDED and other emirates",
         api="GET /v1/licences?activity=restaurant,cloud-kitchen", freq="Daily", records=31_870,
         data="Trade licences for restaurants, cloud kitchens and delivery platforms",
         why="Counts restaurants and new entry; flags platform-owned cloud kitchens"),
    dict(key="fta", cat="Government registers", name="Federal Tax Authority",
         who="VAT returns / e-invoicing (aggregated)",
         api="GET /v1/turnover?entity_id=…", freq="Quarterly", records=1_164,
         data="Declared turnover of platforms and merging parties",
         why="Verifies the AED 300m filing threshold and the filing fee base"),
    dict(key="fcsc", cat="Statistics", name="Federal Competitiveness and Statistics Centre",
         who="National statistics",
         api="GET /v1/cpi?item=food-away-from-home", freq="Monthly", records=3_312,
         data="Consumer prices for restaurant meals, population",
         why="Separates price rises caused by costs from those caused by market power"),
    dict(key="complaints_cp", cat="Complaints & sentiment", name="Consumer protection complaints",
         who="MoET consumer protection · Dubai Corporation for Consumer Protection and Fair Trade",
         api="GET /v1/complaints?sector=food-delivery", freq="Real-time", records=None,
         data="Complaints from consumers, restaurants and riders; mediation outcomes",
         why="Early warning of unfair terms; routing between competition and consumer protection"),
    dict(key="reviews", cat="Complaints & sentiment", name="Public app reviews & social media",
         who="App stores and public posts (personal data removed)",
         api="GET /v1/reviews?apps=…", freq="Daily", records=96_400,
         data="Ratings and review text in Arabic and English",
         why="Consumer sentiment per platform"),
]
SRC = {s_["key"]: s_ for s_ in SOURCES}
MODULE_SOURCES = {   # which sources each module uses, and for what
    "merger": [("efiling", "Notifications, parties, documents, fee payment"),
               ("platforms", "Market shares by orders, national and by emirate"),
               ("fta", "Turnover for the AED 300m threshold and the fee"),
               ("ner", "Ownership links and undertakings concerned")],
    "monitoring": [("platforms", "Shares, commissions, exclusivity, rankings, costs"),
                   ("studies", "Baselines and findings of earlier market studies"),
                   ("complaints_cp", "Complaint spikes and coercion signals"),
                   ("ner", "Common shareholders and board links"),
                   ("emirates", "Restaurant counts, platform-owned cloud kitchens"),
                   ("fcsc", "Restaurant price inflation (cost vs market power)")],
    "complaints": [("complaints_cp", "Consumer, restaurant and rider complaints"),
                   ("reviews", "App ratings and review text"),
                   ("platforms", "Orders and restaurant counts to normalise complaint rates")],
}
MODULE_NAMES = {"merger": "Merger control", "monitoring": "Market monitoring", "complaints": "Complaints & sentiment"}
PRESETS = {"All sources": [s_["key"] for s_ in SOURCES],
           "Merger control set": [k for k, _ in MODULE_SOURCES["merger"]],
           "Market monitoring set": [k for k, _ in MODULE_SOURCES["monitoring"]],
           "Complaints set": [k for k, _ in MODULE_SOURCES["complaints"]]}


def source_records(key):
    r = SRC[key]["records"]
    return r if r else len(complaints())


# ---------------------------------------------------------------- earlier market study (archive)
MARKET_STUDY = dict(
    id="MS-2025-02", title="Online food delivery platforms in the UAE", completed="June 2025", month="2025-06",
    findings=["Exclusive deals with restaurants were spreading and limiting multi-homing (led to Ministerial Decision No. 32 of 2026).",
              "Many restaurants depend on the leading platform for most of their online sales.",
              "Platform-owned cloud kitchens are an emerging self-preferencing risk.",
              "Commissions charged by the leader should be reviewed if they exceed 28%."],
    baselines=dict(exclusivity=9.0, dependence=41, own_top_dunebite=8, own_list_dunebite=5, commission_review=28.0),
)
OWNERSHIP_LINKS = [("Dunebite", "Palm Plate", "A shareholder holding 12% of Dunebite also holds 9% of Palm Plate (National Economic Register)")]


# ============================================================================
# MERGER CASES  (two cases: one recommended for approval, one for rejection)
# ============================================================================
MERGER_STEPS = [
    ("Notification received", "E-filing portal", True),
    ("Completeness check (10 business days)", "System", True),
    ("Filing fee calculated & paid", "System", True),
    ("Published for third-party observations (15 working days)", "System", True),
    ("Automated assessment & recommendation", "System", True),
    ("Case officer review", "Case officer", False),
    ("Director of Competition: reasoned report to Minister", "Director", False),
    ("Minister's decision (Art. 15)", "Minister", False),
    ("Decision published & statistics updated", "System", True),
]


def merger_cases():
    sh = latest_shares(); pre = hhi(sh)

    def calc(a, b):
        sa, sb = sh[a], sh[b]; delta = 2 * sa * sb
        turnover = PLATFORMS[a]["rev"] + PLATFORMS[b]["rev"]
        return dict(sa=sa, sb=sb, merged=sa + sb, delta=delta, pre=pre, post=pre + delta, turnover=turnover,
                    fee=min(FEE_RATE * turnover * 1e6, FEE_CAP), rank=1 + sum(v > sa + sb for k, v in sh.items() if k not in (a, b)))
    A = calc("Palm Plate", "Oasis Delivery"); B = calc("Nexa Eats", "Falcon Feast")
    la = local_check("Palm Plate", "Oasis Delivery"); lb = local_check("Nexa Eats", "Falcon Feast")
    la_max = max(la, key=lambda r: r["merged"]); la_no2 = [r["Emirate"] for r in la if r["rank"] <= 2]
    lb_min = min(lb, key=lambda r: r["merged"])
    la_ratio = max(r["merged"] / r["leader"] for r in la)
    local_a = (f"Local check by emirate: the merged firm's share peaks at {la_max['merged']:.0f}% ({la_max['Emirate']}) and never "
               f"exceeds {la_ratio * 100:.0f}% of the leader's share. It would become the #2 platform in {len(la_no2)} of 7 emirates "
               f"({', '.join(la_no2)}), creating a regional challenger to Nexa Eats.")
    local_b = (f"Local check by emirate: the combined share exceeds 45% in every emirate (lowest {lb_min['merged']:.0f}% in "
               f"{lb_min['Emirate']}), so a narrower local market would not change the conclusion.")
    rival_b = max(v for k, v in sh.items() if k not in ("Nexa Eats", "Falcon Feast"))
    return {
        "M-2026-041": dict(
            title="Palm Plate / Oasis Delivery — full merger", acquirer="Palm Plate", target="Oasis Delivery", kind="Horizontal merger",
            received="2026-09-14", complete="2026-09-24", m=A, rec="Approve", confidence="Medium",
            headline="Recommend approval without conditions: the merger creates a stronger third player and does not adversely affect competition (Art. 15).",
            sections=[
                ("Notifiability (Cabinet Resolution No. 3 of 2025)",
                 [f"Combined annual sales in the UAE market: AED {A['turnover']:,}m, above the AED 300m threshold → notification mandatory.",
                  f"Combined share {A['merged']:.1f}%, below the 40% share threshold.",
                  "Notification filed before completion, as required by Art. 12; the parties may not complete during review (Art. 13)."]),
                ("Filing fee (Cabinet Resolution No. 105 of 2026)",
                 [f"0.02% × AED {A['turnover']:,}m = AED {A['fee']:,.0f} (below the AED 150,000 cap). Paid through the portal."]),
                ("Relevant market (Market Definition Guidelines, July 2026)",
                 ["Online food ordering and delivery platforms, national (UAE) for screening purposes.",
                  "SSNIP check: a 5–10% rise in commissions would not move enough restaurants to dine-in or own delivery to be unprofitable → platforms form a distinct market.",
                  "Two-sided platform: shares measured on orders (consumer side); restaurant-side measures (listings, commission revenue) give the same ranking.",
                  local_a]),
                ("Market structure (calculated automatically from platform data)",
                 [f"Shares: Palm Plate {A['sa']:.1f}% + Oasis Delivery {A['sb']:.1f}% = {A['merged']:.1f}% → merged firm ranks #{A['rank']} behind Nexa Eats ({sh['Nexa Eats']:.0f}%) and Dunebite ({sh['Dunebite']:.0f}%).",
                  f"HHI {A['pre']:,.0f} → {A['post']:,.0f} (ΔHHI {A['delta']:,.0f}).",
                  "UAE law sets no HHI presumption. For reference, this change would trigger a structural presumption under "
                  "the US 2023 Merger Guidelines (HHI above 1,800, ΔHHI above 100), so the recommendation rests on the "
                  "qualitative evidence below, not on concentration figures."]),
                ("Competitive effects",
                 ["Parties are not each other's closest competitors: 61% of their restaurants also list on Nexa Eats or Dunebite (multi-homing).",
                  "Entry is possible: Falcon Feast grew from under 1% to 10% in 30 months.",
                  "No dominance created or strengthened; a larger #3 increases pressure on the 42% market leader."]),
                ("Third-party observations (Executive Regulations)",
                 ["2 observations received within 15 working days.",
                  "Restaurant association: supportive (lower delivery costs).",
                  "Nexa Eats objection: not substantiated with evidence of harm → dismissed at admissibility review."]),
                ("Economic benefits",
                 ["Shared rider fleet: delivery cost down about AED 1.1 per order (verified against platform cost data).",
                  "Parties commit to keep restaurant commissions at current levels (18–19%) for 24 months."]),
                ("Conclusion under Art. 15",
                 ["The concentration does not adversely affect competition → approve (Art. 15, approval without conditions)."]),
            ]),
        "M-2026-044": dict(
            title="Nexa Eats acquires 100% of Falcon Feast", acquirer="Nexa Eats", target="Falcon Feast", kind="Horizontal acquisition",
            received="2026-08-31", complete="2026-09-10", m=B, rec="Reject", confidence="High",
            headline="Recommend rejection: the acquisition strengthens a dominant position and removes the fastest-growing challenger; benefits do not outweigh the harm (Art. 15).",
            sections=[
                ("Notifiability (Cabinet Resolution No. 3 of 2025)",
                 [f"Combined annual sales in the UAE market: AED {B['turnover']:,}m, above the AED 300m threshold.",
                  f"Combined share {B['merged']:.1f}%, above the 40% share threshold. Both thresholds met → notification mandatory."]),
                ("Filing fee (Cabinet Resolution No. 105 of 2026)",
                 [f"0.02% × AED {B['turnover']:,}m = AED {FEE_RATE * B['turnover'] * 1e6:,.0f} → capped at AED 150,000."]),
                ("Relevant market (Market Definition Guidelines, July 2026)",
                 ["Online food ordering and delivery platforms, national (UAE) for screening purposes; same definition as M-2026-041.",
                  "Two-sided platform: the restaurant side shows the same pattern (Nexa Eats and Falcon Feast together list the most restaurants).",
                  local_b]),
                ("Market structure (calculated automatically from platform data)",
                 [f"Shares: Nexa Eats {B['sa']:.1f}% + Falcon Feast {B['sb']:.1f}% = {B['merged']:.1f}%, more than 2.5 times the next rival ({rival_b:.0f}%).",
                  f"HHI {B['pre']:,.0f} → {B['post']:,.0f} (ΔHHI {B['delta']:,.0f}): a very large increase in an already concentrated market."]),
                ("Competitive effects",
                 ["Dominance: Nexa Eats holds 42%, above the 40% level the system uses to screen for dominance. The qualitative criteria of "
                  "Cabinet Decision No. 59 of 2026 point the same way (exclusive and long-term relationships with restaurants, network effects, "
                  "independence from competitive pressure). The deal would entrench this position (Art. 6).",
                  "Loss of a maverick: Falcon Feast charges the lowest commission (15% vs 27% at Nexa Eats) and has won most of the market's recent switching.",
                  f"Restaurant dependence: 48% of Nexa Eats restaurants already earn over 60% of their online sales on the platform (Art. 7 risk); the deal removes their main outside option.",
                  f"Nexa Eats currently exceeds the 10% exclusivity cap of Ministerial Decision No. 32 of 2026 ({COMPLIANCE_DATA['Nexa Eats']['excl']:.1f}% of restaurants)."]),
                ("Third-party observations (Executive Regulations)",
                 ["5 observations; 3 objections accepted after admissibility review: two restaurant groups and Dunebite.",
                  "Evidence submitted: commission increases following past exclusivity drives; switching data."]),
                ("Economic benefits and remedies offered",
                 ["Claimed: AED 40m technology savings. Not shown to be merger-specific or passed on to restaurants or consumers.",
                  "Offered: 12-month commission freeze and keeping the Falcon Feast brand. Behavioural and temporary; does not restore the lost competition."]),
                ("Conclusion under Art. 15",
                 ["The concentration adversely affects competition and its economic benefits do not outweigh the harm → reject (Art. 15).",
                  "Note: if no decision is issued within the review period, the application is deemed rejected (Art. 13)."]),
            ]),
    }


# ============================================================================
# EX-ANTE MONITORING: compliance rules and recommendations
# ============================================================================
RULES = [
    ("Exclusive restaurants ≤ 10% of listings", "Ministerial Decision No. 32 of 2026", lambda d: d["excl"] <= EXCLUSIVITY_CAP, lambda d: f"{d['excl']:.1f}%"),
    ("Exclusivity term ≤ 12 months", "Ministerial Decision No. 32 of 2026", lambda d: d["excl_months"] <= 12, lambda d: f"{d['excl_months']} mo" if d["excl_months"] else "none"),
    ("No self-preferencing of own kitchens", "Dubai Guidelines (DCCPFT); Art. 6 if dominant", lambda d: d["own_top"] <= 2 * max(d["own_list"], 1), lambda d: f"{d['own_top']}% of top-10 vs {d['own_list']}% of listings"),
    ("30 days' notice of contract changes", "Dubai Guidelines (DCCPFT)", lambda d: d["notice"] >= 30, lambda d: f"{d['notice']} days"),
    ("Fees itemised before checkout", "Dubai Guidelines (DCCPFT)", lambda d: d["itemised"], lambda d: "yes" if d["itemised"] else "no"),
    ("100% of tips paid to riders", "Dubai Guidelines (DCCPFT)", lambda d: d["tips"] >= 100, lambda d: f"{d['tips']}%"),
    ("Revenue per order ≥ average variable cost", "Art. 8 (predatory pricing; AVC test in Cabinet Decision No. 59 of 2026)",
     lambda d: revenue_per_order(d) >= d["avc"], lambda d: f"AED {revenue_per_order(d):.1f} vs AVC {d['avc']:.1f}"),
]

RECOMMENDATIONS = [
    dict(id="R1", platform="Nexa Eats", priority="High", title="Exclusivity above the 10% cap",
         finding=f"{COMPLIANCE_DATA['Nexa Eats']['excl']:.1f}% of Nexa Eats restaurants are on exclusive terms, above the 10% cap. These agreements fall outside the block exemption.",
         basis="Ministerial Decision No. 32 of 2026; Arts. 5–7 of Federal Decree-Law No. 36 of 2023",
         action="Open an investigation and request all exclusive contracts", result="Investigation INV-2026-018 opened; information request sent to Nexa Eats via API (deadline 15 working days)"),
    dict(id="R2", platform="Dunebite", priority="High", title="Own cloud kitchens favoured in search",
         finding="Dunebite's own cloud-kitchen brands take 21% of top-10 search results while making up 6% of listings.",
         basis="Dubai Guidelines, enforced by DCCPFT (no self-preferencing); Art. 6 of the federal law only if dominance is established",
         action="Request ranking criteria and weights; refer to DCCPFT", result="Ranking-data request sent; joint file opened with DCCPFT"),
    dict(id="R3", platform="Saffron Go", priority="Medium", title="Commission raised on 7 days' notice",
         finding="Saffron Go raised commissions from 19% to 22% in June 2026 with 7 days' notice; restaurant complaints rose almost fourfold.",
         basis="Dubai Guidelines, enforced by DCCPFT (30 days' notice; right to terminate)",
         action="Refer to DCCPFT and monitor commissions monthly", result="Referral sent to DCCPFT; commission indicator added to monthly watch list"),
    dict(id="R4", platform="Oasis Delivery", priority="Medium", title="Tips not fully passed to riders; fees not itemised",
         finding="Oasis Delivery passes 86% of tips to riders and adds a service fee after payment.",
         basis="Dubai Guidelines, enforced by DCCPFT (100% tips to riders; itemised fees)",
         action="Refer to consumer protection", result="Referral sent to MoET consumer protection and DCCPFT"),
    dict(id="R5", platform="Falcon Feast", priority="Low", title="Revenue per order below average variable cost",
         finding=(f"Falcon Feast earns AED {revenue_per_order(COMPLIANCE_DATA['Falcon Feast']):.1f} per order (15% commission on an AED {AOV:.0f} order, "
                  f"no delivery fee) against an average variable cost of AED {COMPLIANCE_DATA['Falcon Feast']['avc']:.1f}. Pricing below AVC can be "
                  "predatory, but Falcon Feast is a recent entrant with a 10% share: low prices may be legitimate penetration pricing."),
         basis="Art. 8 (applies regardless of dominance but requires an aim to exclude competitors); cost tests in Cabinet Decision No. 59 of 2026",
         action="Monitor; request cost data if pricing stays below AVC for 6 more months", result="Added to watch list; review date set for April 2027"),
    dict(id="R6", platform="Market-wide", priority="High", title="Leader above the 40% screening level; restaurant dependence",
         finding="Nexa Eats holds 42% of orders and 48% of its restaurants earn over 60% of their online sales on it. Market share alone does not establish dominance; a market study would test the qualitative criteria.",
         basis="Art. 6 and Art. 7; dominance criteria in Cabinet Decision No. 59 of 2026; market studies under Art. 18",
         action="Launch a market study on food delivery commissions and dependence", result="Market study MS-2026-03 launched; data requests sent to all six platforms"),
]


# Plain-language explanations shown under each recommendation card
def _rev(p):
    return revenue_per_order(COMPLIANCE_DATA[p])


EXPLANATIONS = {
    "R1": [
        ("What the finding means",
         f"An exclusive arrangement means a restaurant agrees to sell only through Nexa Eats and not through any other app. "
         f"According to Nexa Eats' own reported data, {COMPLIANCE_DATA['Nexa Eats']['excl']:.1f}% of the restaurants on its "
         f"platform are on such terms. The other platforms range from 0% to {max(d['excl'] for p, d in COMPLIANCE_DATA.items() if p != 'Nexa Eats'):.1f}%."),
        ("Why it matters for competition",
         "Food delivery runs on network effects: consumers go where the restaurants are, and restaurants go where the "
         "consumers are. If the largest platform (42% of orders) locks restaurants in, rival apps cannot offer the same "
         "choice, consumers have less reason to switch, and smaller platforms struggle to grow (foreclosure). Restaurants "
         "also lose bargaining power, because they cannot threaten to move their sales when commissions rise."),
        ("The legal basis, explained",
         "Arts. 5–7 of Federal Decree-Law No. 36 of 2023 prohibit restrictive agreements (Art. 5), abuse of a dominant "
         "position (Art. 6) and abuse of economic dependence (Art. 7). Ministerial Decision No. 32 of 2026 creates a safe "
         "harbour for exclusive deals in food delivery, but only if each deal lasts at most 12 months, no more than 10% of "
         "a platform's listed restaurants are exclusive, and there is no non-compete after the exclusivity ends. Above the "
         "10% cap the deals lose that automatic protection. This does not make them illegal by itself: they must then be "
         "assessed under Arts. 5–7. The exact consequence for deals below the cap depends on the wording of the Decision."),
        ("Why this action",
         "An investigation with a request for all exclusive contracts lets the department verify the figure, check the "
         "duration of each deal, look for post-exclusivity non-competes, and see what restaurants receive in return. "
         "Restaurant complaints such as 'Told we lose promotions unless we sign exclusivity' suggest pressure, which the "
         "investigation would test."),
        ("How the system detected it",
         "The monitoring rule compares each platform's reported share of exclusive restaurants with the 10% cap. It is "
         "High priority because it concerns a federal competition provision and the market leader."),
        ("Possible outcomes",
         "No infringement; commitments (e.g. reducing exclusivity below 10%); a settlement; or fines under Art. 24 "
         "(at least AED 100,000 and up to 10% of annual UAE sales)."),
    ],
    "R2": [
        ("What the finding means",
         f"Dunebite runs its own cloud-kitchen brands and also lists independent restaurants. Its own brands make up "
         f"{COMPLIANCE_DATA['Dunebite']['own_list']}% of its listings but take {COMPLIANCE_DATA['Dunebite']['own_top']}% of "
         "the top-10 search results. Showing your own products more prominently than rivals' is called self-preferencing."),
        ("Why it matters for competition",
         "A platform that is both the marketplace and a seller on it can steer consumers towards its own brands. "
         "Independent restaurants then lose visibility and sales for reasons unrelated to price or quality, which "
         "distorts competition between restaurants and discourages new ones from entering."),
        ("The legal basis, explained",
         "The Dubai Guidelines for Online Food Delivery Platforms, issued and enforced by the Dubai Corporation for "
         "Consumer Protection and Fair Trade (DCCPFT), prohibit platforms from favouring their own brands or affiliated "
         "cloud kitchens in ranking and recommendations. Under federal law, self-preferencing could be an abuse under "
         "Art. 6, but only if the platform is dominant. Dunebite holds about 20% of orders, so Art. 6 is unlikely to apply."),
        ("Why this action",
         "Requesting the ranking criteria and their weights shows whether own brands rank higher because of genuine "
         "factors (ratings, delivery time) or because of ownership. Referral to DCCPFT respects its role as the enforcer "
         "of the Dubai Guidelines; the federal department detects and refers."),
        ("How the system detected it",
         "The rule flags a platform when its own brands' share of top-10 results is more than twice their share of "
         "listings. This threshold is an analytical choice to trigger review, not a legal standard."),
        ("Possible outcomes",
         "Ranking changes agreed with DCCPFT; DCCPFT enforcement in Dubai; or, if Dunebite's position grows, a federal "
         "Art. 6 assessment."),
    ],
    "R3": [
        ("What the finding means",
         f"Saffron Go raised its commission from 19% to 22% in June 2026, giving restaurants "
         f"{COMPLIANCE_DATA['Saffron Go']['notice']} days' notice. Restaurant complaints about commission terms rose almost fourfold "
         "afterwards, and Saffron Go's sentiment index fell below the watch level."),
        ("Why it matters for competition",
         "Sudden changes to terms leave restaurants no time to compare alternatives or move to another platform. "
         "Short notice turns a commission increase into a take-it-or-leave-it choice, which weakens the competitive "
         "pressure that switching would normally create."),
        ("The legal basis, explained",
         "The Dubai Guidelines require at least 30 days' notice of contract changes and give restaurants a right to "
         "terminate if they do not agree. Seven days falls short. The rule is enforced by DCCPFT. A 22% commission is not "
         "in itself unlawful, and Saffron Go (about 12% of orders) is not dominant, so federal abuse rules do not apply."),
        ("Why this action",
         "A referral to DCCPFT addresses the notice breach. Adding Saffron Go's commission to the monthly watch list lets "
         "the department see whether other platforms follow with similar increases, which could signal coordination."),
        ("How the system detected it",
         "The rule compares the notice period reported in platform data with the 30-day minimum. Complaints data "
         "corroborated the finding."),
        ("Possible outcomes",
         "Saffron Go re-issues the change with proper notice; DCCPFT enforcement; or, if several platforms raise "
         "commissions together, a wider review under Art. 5."),
    ],
    "R4": [
        ("What the finding means",
         f"Oasis Delivery passes {COMPLIANCE_DATA['Oasis Delivery']['tips']}% of customer tips to riders instead of 100%, "
         "and adds a service fee after payment that is not shown at checkout."),
        ("Why it matters for competition",
         "This is mainly a consumer and worker protection issue. It also matters for competition: when the full price "
         "is only visible after payment, consumers cannot compare platforms properly, and price competition weakens."),
        ("The legal basis, explained",
         "The Dubai Guidelines require all charges to be itemised before checkout and 100% of tips to go to riders. "
         "These are consumer-protection rules enforced by DCCPFT and consumer protection authorities, not federal "
         "competition provisions."),
        ("Why this action",
         "Referral sends the case to the bodies with the power to act, and avoids duplicated work. The system keeps the "
         "link so the department can see the outcome."),
        ("How the system detected it",
         "Two rules: tips paid to riders below 100%, and fees not itemised before checkout. Rider and consumer "
         "complaints about tips and hidden fees corroborate them."),
        ("Possible outcomes",
         "Corrective action by Oasis Delivery, refunds to riders or consumers, or penalties by the consumer protection "
         "authorities."),
    ],
    "R5": [
        ("What the finding means",
         f"Falcon Feast earns about AED {_rev('Falcon Feast'):.1f} per order: a 15% commission on an average AED {AOV:.0f} "
         f"order and no delivery fee. Its average variable cost (riders, payments, support) is AED "
         f"{COMPLIANCE_DATA['Falcon Feast']['avc']:.1f} per order. It is losing money on each additional order."),
        ("Why it matters for competition",
         "Pricing below cost can be predatory: a firm accepts losses to drive rivals out, then raises prices. But low "
         "prices are usually good for consumers, and new entrants often price low to win customers. Falcon Feast "
         "entered in 2024 and holds about 10% of orders, so penetration pricing is the more likely explanation."),
        ("The legal basis, explained",
         "Art. 8 prohibits prices excessively below cost when they aim to drive out competitors or prevent entry. The "
         "Executive Regulations (Cabinet Decision No. 59 of 2026) use cost tests such as average variable cost and "
         "average total cost. Unusually, Art. 8 applies regardless of dominance, but it requires an exclusionary aim."),
        ("Why this action",
         "Acting now could punish healthy competition. Monitoring for six more months, and requesting cost data if the "
         "pattern persists, balances the risk of predation against the risk of chilling a new competitor."),
        ("How the system detected it",
         "The rule compares revenue per order (commission on the average order plus delivery fee) with average variable "
         "cost. It is Low priority because the firm is small and new."),
        ("Possible outcomes",
         "Most likely no action as Falcon Feast grows and raises prices; a cost-data request if losses continue; an "
         "Art. 8 case only if evidence of an aim to exclude emerges."),
    ],
    "R6": [
        ("What the finding means",
         f"Nexa Eats handles 42% of all orders, and {COMPLIANCE_DATA['Nexa Eats']['dependent']}% of its restaurants earn more "
         "than 60% of their online sales through it. The market's HHI is above 2,500, a highly concentrated level."),
        ("Why it matters for competition",
         "A platform that many restaurants depend on can raise commissions or impose terms without losing them, because "
         "they have no realistic alternative. This is a market-wide issue rather than a single breach, so it calls for "
         "understanding the market before any case is opened."),
        ("The legal basis, explained",
         "Art. 6 prohibits abuse of a dominant position, and Art. 7 abuse of economic dependence (exploiting a customer's "
         "lack of alternatives). The 40% level is a screening level, not a legal presumption: dominance is assessed on "
         "the qualitative criteria in Cabinet Decision No. 59 of 2026, such as long-term or exclusive relationships, "
         "technological and business-model advantages, and independence from competitive pressure. Art. 18 gives the "
         "Ministry the power to carry out market studies."),
        ("Why this action",
         "A market study gathers evidence on commissions, switching, dependence and barriers to entry across all six "
         "platforms. It can lead to recommendations, guidelines or targeted cases, and it fits the ex-ante approach: "
         "understand the market first, then act."),
        ("How the system detected it",
         "Two indicators together: the leader's share above the 40% screening level, and a high share of dependent "
         "restaurants."),
        ("Possible outcomes",
         "A published market study; recommendations to government; guidance for platforms; or abuse-of-dominance or "
         "economic-dependence cases where the study finds evidence."),
    ],
}

# ============================================================================
# STATE
# ============================================================================
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def init_state():
    ss = st.session_state
    if "init" in ss:
        return
    ss.init = True
    ss.last_extract = "2026-10-21 06:00"
    ss.extract_runs = 0
    ss.cases = {cid: dict(stage=1, log=[(c["received"] + " 09:12", "E-filing portal", "Notification received")],
                          decision=None, officer=None, override=None)
                for cid, c in merger_cases().items()}
    ss.recs = {r["id"]: "Pending" for r in RECOMMENDATIONS}
    ss.batch_done = False
    ss.extracted = {s_["key"]: "2026-10-22 06:00" for s_ in SOURCES}   # overnight scheduled run
    ss.src_sel = []
    ss.src_preset = "Custom selection"
    ss.extract_log = None
    ss.merger_auto_done = False
    ss.mon_auto_done = False
    ss.cmp_auto_done = False
    ss.activity = [("2026-10-21 06:00", "Data", f"Scheduled extraction from {len(SOURCES)} sources completed"),
                   ("2026-10-21 06:02", "Monitoring", "Compliance checks run on 6 platforms: 6 recommendations generated"),
                   ("2026-09-24 10:05", "Merger", "M-2026-041 notification complete; 90-day clock started"),
                   ("2026-09-10 11:40", "Merger", "M-2026-044 notification complete; 90-day clock started")]


def act(area, text):
    st.session_state.activity.append((now(), area, text))


# ============================================================================
# UI HELPERS
# ============================================================================
def esc(x):
    return html.escape(str(x), quote=True)


def _ver():
    try:
        return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


_WIDE = {"width": "stretch"} if _ver() >= (1, 50) else {"use_container_width": True}


def show(fig):
    st.plotly_chart(fig, **_WIDE)


def table(df, **kw):
    st.dataframe(df, hide_index=True, **_WIDE, **kw)


def style(fig, h=300, legend=True):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=30, b=10), showlegend=legend,
                      font=dict(family="IBM Plex Sans, Segoe UI, sans-serif", size=12, color=INK),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font=dict(size=11)))
    fig.update_xaxes(showgrid=False, linecolor=BORDER); fig.update_yaxes(gridcolor=BORDER, zeroline=False)
    return fig


def kpi(label, value, sub="", color=INK):
    st.markdown(f"""<div style="background:#fff;border:1px solid {BORDER};border-top:3px solid {PRIMARY};border-radius:10px;
        padding:.7rem .9rem;min-height:88px"><div style="font-size:.68rem;color:{MUTED};text-transform:uppercase;
        letter-spacing:.04em;font-weight:600">{esc(label)}</div><div style="font-size:1.35rem;font-weight:700;color:{INK};
        margin-top:.1rem">{esc(value)}</div><div style="font-size:.75rem;color:{color};font-weight:600">{esc(sub)}</div></div>""",
                unsafe_allow_html=True)


def header(title, what, why):
    st.markdown(f"""<div style="background:{PRIMARY};color:#fff;border-radius:10px;padding:.9rem 1.1rem;margin-bottom:.6rem">
        <div style="font-size:1.25rem;font-weight:700">{esc(title)}</div>
        <div style="font-size:.86rem;opacity:.93;margin-top:.15rem">{esc(what)}</div></div>
        <div style="background:#FBF3E3;border:1px solid #EAD9B0;border-radius:8px;padding:.55rem .8rem;margin-bottom:.9rem;
        font-size:.85rem;color:#5c4a22"><b>Why this matters for the authority:</b> {esc(why)}</div>""", unsafe_allow_html=True)


def section(title, sub=""):
    st.markdown(f"<div style='font-weight:700;color:{INK};font-size:1.02rem;margin:.7rem 0 .1rem 0'>{esc(title)}</div>"
                + (f"<div style='color:{MUTED};font-size:.8rem;margin-bottom:.3rem'>{esc(sub)}</div>" if sub else ""),
                unsafe_allow_html=True)


def box(html_text, color=PRIMARY, bg="#fff"):
    st.markdown(f"""<div style="background:{bg};border:1px solid {BORDER};border-left:4px solid {color};border-radius:8px;
        padding:.6rem .85rem;margin:.3rem 0 .6rem 0;font-size:.86rem">{html_text}</div>""", unsafe_allow_html=True)


def stepper(steps, done):
    """Horizontal process tracker: done steps teal, current step gold, later steps grey."""
    cells = []
    for i, (label, actor, auto) in enumerate(steps):
        if i < done:
            bg, fg, bd = PRIMARY, "#fff", PRIMARY
        elif i == done:
            bg, fg, bd = GOLD, INK, "#B9862F"
        else:
            bg, fg, bd = "#fff", MUTED, BORDER
        tag = "⚙ automated" if auto else f"👤 {actor}"
        cells.append(f"""<div style="flex:1;min-width:110px;background:{bg};color:{fg};border:1px solid {bd};border-radius:8px;
            padding:.4rem .5rem;font-size:.72rem;line-height:1.25"><div style="font-weight:700">{i + 1}. {esc(label)}</div>
            <div style="opacity:.85;margin-top:.15rem">{esc(tag)}</div></div>""")
    st.markdown('<div style="display:flex;gap:.35rem;flex-wrap:wrap;margin:.3rem 0 .7rem 0">' + "".join(cells) + "</div>",
                unsafe_allow_html=True)


def run_steps(title, steps, pause=0.35):
    with st.status(title, expanded=True) as s:
        for line in steps:
            st.write("✓ " + line); time.sleep(pause)
        s.update(label=title.replace("…", "") + " — done", state="complete")



# ---------------------------------------------------------------- shared building blocks for the new modes
def source_strip(module):
    """Boxes at the top of a page showing the data sources this module uses and when each was last extracted."""
    items = MODULE_SOURCES[module]
    cells = []
    for key, use in items:
        src = SRC[key]; when = st.session_state.extracted.get(key)
        status = (f"<span style='color:{OK};font-weight:700'>● Extracted {esc(when)}</span>" if when
                  else f"<span style='color:{WARN};font-weight:700'>○ Not yet extracted</span>")
        cells.append(f"""<div style="flex:1;min-width:170px;background:#fff;border:1px solid {BORDER};border-top:3px solid {PRIMARY_MD};
            border-radius:9px;padding:.5rem .65rem"><div style="font-weight:700;font-size:.82rem;color:{INK}">{esc(src['name'])}</div>
            <div style="font-size:.74rem;color:{MUTED};margin:.1rem 0 .25rem 0">{esc(use)}</div>
            <div style="font-size:.7rem">{status} · {source_records(key):,} records</div></div>""")
    st.markdown(f"<div style='font-size:.72rem;font-weight:700;color:{MUTED};letter-spacing:.05em;margin:.1rem 0 .3rem 0'>"
                f"DATA SOURCES USED BY {esc(MODULE_NAMES[module].upper())} · {len(items)} API CONNECTIONS</div>"
                + '<div style="display:flex;gap:.45rem;flex-wrap:wrap;margin-bottom:.8rem">' + "".join(cells) + "</div>",
                unsafe_allow_html=True)


def extract_lines(keys):
    """Run the extraction for the given sources and return log rows."""
    rows = []
    for k in keys:
        st.write(f"✓ {SRC[k]['name']}: connected via API · {source_records(k):,} records pulled · validated"); time.sleep(0.25)
        st.session_state.extracted[k] = now()
        rows.append(dict(Source=SRC[k]["name"], Provider=SRC[k]["who"], Records=source_records(k), Status="✓ Validated",
                         Time=st.session_state.extracted[k]))
    return rows


def mode_selector(key):
    mode = st.radio("Working mode", ["Guided review", "Fully automated"], horizontal=True, key=key)
    if mode == "Guided review":
        st.caption("Guided review: the data is already extracted and calculated. You step through the review yourself.")
    else:
        st.caption("Fully automated: press one button and the system extracts the data, calculates everything and "
                   "generates the review. People then decide.")
    return mode


def mode_banner(title, steps):
    st.markdown(f"""<div style="background:#F3F8FA;border:1px dashed {PRIMARY};border-radius:12px;padding:1rem 1.1rem;margin:.4rem 0 .8rem 0">
        <div style="font-weight:800;color:{PRIMARY_DK};font-size:1.05rem">{esc(title)}</div>
        <div style="display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.55rem">""" + "".join(
        f"""<div style="background:#fff;border:1px solid {PRIMARY_LT};border-radius:999px;padding:.2rem .7rem;font-size:.76rem;
        color:{INK}">{i + 1}. {esc(x)}</div>""" for i, x in enumerate(steps)) + "</div></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- early-warning signs (ex-ante)
def warning_signs(use_study=True):
    """Return (study_signs, live_signs). Levels: red = further action needed, amber = watch / request information,
    green = checked, no concern."""
    m = market(); comp = complaints(); sh = latest_shares(); cd = COMPLIANCE_DATA
    end = comp["Date"].max(); r90 = comp[comp["Date"] > end - pd.Timedelta(days=90)]
    p90 = comp[(comp["Date"] <= end - pd.Timedelta(days=90)) & (comp["Date"] > end - pd.Timedelta(days=180))]

    def comm_at(platform, month):
        g = m[(m["Platform"] == platform) & (m["Month"] == month)]
        return float(g["Commission"].iloc[0]) if len(g) else float("nan")

    def share_at(platform, month):
        g = m[(m["Platform"] == platform) & (m["Month"] == month)]
        return float(g["Share"].iloc[0]) if len(g) else 0.0
    last_m = m["Month"].max(); lead = max(sh, key=sh.get)
    study = []
    if use_study:
        b = MARKET_STUDY["baselines"]; sm = MARKET_STUDY["month"]
        study = [
            dict(level="red", title="Exclusivity has grown past the cap", source="Market study + platform data",
                 evidence=f"Nexa Eats exclusive restaurants: {b['exclusivity']:.1f}% at the study → {cd['Nexa Eats']['excl']:.1f}% now (cap 10%).",
                 action="Further action: investigation (R1)"),
            dict(level="red", title="Restaurant dependence is rising", source="Market study + platform data",
                 evidence=f"Restaurants earning >60% of online sales on Nexa Eats: {b['dependence']}% at the study → {cd['Nexa Eats']['dependent']}% now.",
                 action="Further action: market study update (R6)"),
            dict(level="red", title="Self-preferencing risk has materialised", source="Market study + platform data",
                 evidence=f"Dunebite own brands in top-10 results: {b['own_top_dunebite']}% at the study → {cd['Dunebite']['own_top']}% now "
                          f"(listings {b['own_list_dunebite']}% → {cd['Dunebite']['own_list']}%).",
                 action="Further action: ranking-data request, referral to DCCPFT (R2)"),
            dict(level="amber", title="Leader's commission approaching the review level", source="Market study + platform data",
                 evidence=f"Nexa Eats commission: {comm_at('Nexa Eats', sm):.1f}% at the study → {comm_at('Nexa Eats', last_m):.1f}% now "
                          f"(study review level {b['commission_review']:.0f}%).",
                 action="Watch: monthly tracking"),
            dict(level="amber", title="Entry is working, but the entrant is being acquired", source="Market study + merger portal",
                 evidence=f"Nexa Eats share {share_at('Nexa Eats', sm):.1f}% → {sh['Nexa Eats']:.1f}% as Falcon Feast grew to "
                          f"{sh['Falcon Feast']:.0f}%. Pending notification M-2026-044: Nexa Eats to acquire Falcon Feast.",
                 action="Further action: in-depth merger review (M-2026-044)"),
        ]
    # live signals from current data
    sc = lambda df, plat, cat: int(((df["Platform"] == plat) & (df["Category"] == cat)).sum())
    change = pd.Timestamp("2026-06-01"); start = pd.Timestamp("2026-01-01")
    after = comp[comp["Date"] >= change]; before = comp[(comp["Date"] >= start) & (comp["Date"] < change)]
    m_after = max((end - change).days / 30.4, 1); m_before = (change - start).days / 30.4
    a = sc(after, "Saffron Go", "Commission terms") / m_after; b_ = sc(before, "Saffron Go", "Commission terms") / m_before
    excl_n = int((r90["Category"] == "Exclusivity").sum()); excl_nexa = sc(r90, "Nexa Eats", "Exclusivity")
    ret_n = int((r90["Category"] == "Retaliation for multi-homing").sum()); ret_nexa = sc(r90, "Nexa Eats", "Retaliation for multi-homing")
    six = str(MONTHS[-7])
    raised = [p for p in NAMES if comm_at(p, last_m) - comm_at(p, six) >= 1.0]
    ss_ = sentiment_series(); last_s = ss_[ss_["Date"] == ss_["Date"].max()].set_index("Platform")["Sentiment"]
    may = ss_[ss_["Date"] == pd.Timestamp("2026-05-01")].set_index("Platform")["Sentiment"]
    drops = {p: last_s[p] - may[p] for p in NAMES}; worst = min(drops, key=drops.get)
    below = [p for p in NAMES if last_s[p] < 50]
    fal_rev = revenue_per_order(cd["Falcon Feast"])
    live = [
        dict(level="amber", title="Spike in restaurant complaints on commissions", source="Consumer protection complaints",
             evidence=f"Saffron Go: {a:.0f} commission complaints a month since its June 2026 increase vs {b_:.0f} a month "
                      f"before (×{a / max(b_, 0.1):.1f}).",
             action="Watch + referral to DCCPFT (R3)"),
        dict(level="red", title="Restaurants report pressure to sign exclusivity", source="Consumer protection complaints",
             evidence=f"{excl_n} complaints in 90 days, {excl_nexa} about Nexa Eats; {ret_n} report lower ranking after joining "
                      f"another app ({ret_nexa} about Nexa Eats).",
             action="Further action: evidence for investigation (R1)"),
        dict(level="red" if len(raised) >= 2 else "green", title="Parallel commission increases",
             source="Food delivery platforms",
             evidence=(f"{len(raised)} platform(s) raised commissions by ≥1 pp in the last 6 months: {', '.join(raised) or 'none'}. "
                       + ("Possible coordination." if len(raised) >= 2 else "No parallel pattern.")),
             action="Further action: Art. 5 review" if len(raised) >= 2 else "Checked: no concern"),
        dict(level="red", title="Leader seeks to acquire the fastest-growing challenger", source="Merger e-filing portal",
             evidence=f"M-2026-044: {lead} ({sh[lead]:.0f}%) to acquire Falcon Feast ({sh['Falcon Feast']:.0f}%), the platform with "
                      "the lowest commission and most recent growth.",
             action="Further action: in-depth merger review"),
        dict(level="amber", title="Common shareholder between rivals", source="National Economic Register",
             evidence=OWNERSHIP_LINKS[0][2] + ". Minority links can soften competition between rivals.",
             action="Request information on governance rights"),
        dict(level="amber", title="Falling user sentiment", source="App reviews & complaints",
             evidence=f"Largest drop since May 2026: {worst} ({drops[worst]:+.0f} points). Below the watch level of 50: "
                      f"{', '.join(below) or 'none'}.",
             action="Watch; linked to R3 and R4"),
        dict(level="green", title="Below-cost pricing by an entrant", source="Food delivery platforms",
             evidence=f"Falcon Feast earns AED {fal_rev:.1f} per order vs AVC AED {cd['Falcon Feast']['avc']:.1f}; small, recent entrant.",
             action="Low risk: monitor (R5)"),
    ]
    if not use_study:   # without a study baseline, structural signals come from the live data instead
        live = [dict(level="red", title="Leader above the 40% screening level with high dependence", source="Food delivery platforms",
                     evidence=f"{lead} holds {sh[lead]:.0f}% of orders; {cd[lead]['dependent']}% of its restaurants earn >60% of online "
                              "sales on it. No earlier study to compare with.",
                     action="Further action: launch a market study (R6)"),
                dict(level="red", title="Exclusivity above the 10% cap", source="Food delivery platforms",
                     evidence=f"Nexa Eats: {cd['Nexa Eats']['excl']:.1f}% of restaurants on exclusive terms.",
                     action="Further action: investigation (R1)")] + live
    return study, live


def sign_cards(signs):
    col = {"red": ALERT, "amber": WARN, "green": OK}
    lab_ = {"red": "Further action needed", "amber": "Watch / request information", "green": "Checked: no concern"}
    cols = st.columns(2)
    for i, sgn in enumerate(signs):
        c = col[sgn["level"]]
        with cols[i % 2]:
            st.markdown(f"""<div style="background:#fff;border:1px solid {BORDER};border-left:5px solid {c};border-radius:10px;
                padding:.55rem .8rem;margin-bottom:.5rem"><div style="display:flex;justify-content:space-between;gap:.5rem">
                <div style="font-weight:700;color:{INK};font-size:.88rem">{esc(sgn['title'])}</div>
                <div style="font-size:.68rem;font-weight:700;color:{c};white-space:nowrap">● {esc(lab_[sgn['level']])}</div></div>
                <div style="font-size:.8rem;margin-top:.2rem">{esc(sgn['evidence'])}</div>
                <div style="display:flex;justify-content:space-between;margin-top:.3rem;font-size:.72rem;color:{MUTED}">
                <span>Source: {esc(sgn['source'])}</span><span style="font-weight:700;color:{INK}">{esc(sgn['action'])}</span></div></div>""",
                        unsafe_allow_html=True)


# ============================================================================
# PAGES
# ============================================================================

# ============================================================================
# DETAILED AUTOMATION FLOWCHART (Graphviz)
# ============================================================================
def _q(t):
    return t.replace('"', "'").replace("\n", "\\n")


def automation_dot():
    AUTO_FILL, HUMAN_FILL, OUT_FILL = "#DCEAF0", "#FBEBC8", "#FFFFFF"
    L = ["digraph G {",
         'rankdir=TB; bgcolor="transparent"; compound=true; nodesep=0.3; ranksep=0.38; pad=0.2;',
         'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, margin="0.14,0.07", penwidth=1.2, color="#9FCAD8"];',
         f'edge [color="{PRIMARY_MD}", penwidth=1.3, arrowsize=0.7, fontname="Helvetica", fontsize=9, fontcolor="{MUTED}"];']

    def node(nid, text, kind="auto", shape=None):
        fill = {"auto": AUTO_FILL, "human": HUMAN_FILL, "out": OUT_FILL, "src": "#FFFFFF"}[kind]
        col = {"auto": PRIMARY_LT, "human": "#D9A441", "out": "#64748B", "src": PRIMARY_LT}[kind]
        prefix = {"auto": "⚙ ", "human": "👤 ", "out": "", "src": ""}[kind]
        extra = f", shape={shape}" if shape else ""
        L.append(f'{nid} [label="{_q(prefix + text)}", fillcolor="{fill}", color="{col}"{extra}];')

    def cluster(name, label, body):
        L.append(f'subgraph cluster_{name} {{ label="{_q(label)}"; fontname="Helvetica"; fontsize=13; fontcolor="{INK}"; '
                 f'style="rounded,filled"; fillcolor="#F7FAFB"; color="{PRIMARY_LT}"; labeljust="l";')
        body(); L.append("}")

    # 1. sources
    def src():
        for i, s_ in enumerate(SOURCES):
            node(f"s{i}", s_["name"].replace(" & ", " &\n").replace("Federal Competitiveness and Statistics Centre",
                 "Federal Competitiveness\nand Statistics Centre").replace("Consumer protection complaints",
                 "Consumer protection\ncomplaints").replace("Emirate economic departments", "Emirate economic\ndepartments")
                 .replace("Food delivery platforms (6)", "Food delivery\nplatforms (6)").replace("National Economic Register",
                 "National Economic\nRegister").replace("Merger e-filing portal", "Merger e-filing\nportal")
                 .replace("Federal Tax Authority", "Federal Tax\nAuthority").replace("Public app reviews &\nsocial media",
                 "Public app reviews\n& social media"), "src")
        L.append("{rank=same; " + " ".join(f"s{i};" for i in range(len(SOURCES))) + "}")
    cluster("src", "1  DATA SOURCES — connected through APIs", src)

    # 2. pipeline
    def pipe():
        node("p1", "Extract via APIs\n(daily schedule or 'Extract data')")
        node("p2", "Validate & de-duplicate\n(missing fields, outliers)")
        node("p3", "Link records across sources\n(same firm, licence, owner)")
        node("p4", "Calculate shared indicators\nshares · HHI · commissions · revenue vs cost")
        L.append("{rank=same; p1; p2; p3; p4;}")
        L.append("p1 -> p2 -> p3 -> p4;")
    cluster("pipe", "2  AUTOMATED DATA PIPELINE", pipe)

    # 3a. mergers
    def merg():
        node("m1", "Notification filed on e-portal\ncompleteness check (≤10 business days)\n90-day clock starts")
        node("m3", "Thresholds & fee\nsales > AED 300m or share > 40% (FTA-verified)\nfee 0.02%, cap AED 150,000")
        node("m5", "Published for third-party\nobservations (15 working days)")
        node("m6", "Shares, HHI, ΔHHI · Art. 15 test\n→ recommendation +\nreasoned draft report")
        node("m8", "Case officer\naccept, or override\nwith justification", "human")
        node("m9", "Director of Competition\nreasoned report to Minister", "human")
        node("m10", "Minister's decision\n(Art. 15)", "human", "diamond")
        node("m11", "Decision letter sent,\nregister & statistics updated")
        L.append("m1 -> m3 -> m5 -> m6 -> m8 -> m9 -> m10;")
        L.append('m9 -> m8 [style=dashed, label="return", constraint=false];')
        L.append('m10 -> m11 [label="approve /\\nconditions /\\nreject"];')
    cluster("mer", "3A  MERGER CONTROL", merg)

    # 3b. monitoring
    def mon():
        node("o1", "Platform data refreshed\nshares · commissions · exclusivity\nrankings · fees · costs")
        node("o2", "Indicators recalculated\nHHI · CR3 · leader share\nrevenue per order vs AVC")
        node("o3", "Rules checked\nDecision 32/2026 · Dubai Guidelines\nArt. 8 · 40% screening level")
        node("o3b", "Early-warning scan\nearlier market studies · complaints\nacquisitions · ownership links")
        node("o4", "Breach or\nwarning sign?", "auto", "diamond")
        node("o5", "Recommendation\nwith legal basis & priority")
        node("o6", "Officer approves\nor dismisses", "human")
        node("o7", "Action executed\ninformation request · investigation\nmarket study · referral to DCCPFT")
        L.append("o1 -> o2 -> o3 -> o3b -> o4;")
        L.append('o4 -> o5 [label="yes"];')
        L.append('o4 -> o1 [label="no: keep\\nmonitoring", style=dashed, constraint=false];')
        L.append("o5 -> o6;")
        L.append('o6 -> o7 [label="approved"];')
    cluster("mon", "3B  MARKET MONITORING (EX-ANTE)", mon)

    # 3c. complaints
    def comp():
        node("c1", "Complaints & reviews pulled\nMoET · DCCPFT · app stores")
        node("c2", "Language detected (AR/EN)\npersonal data removed")
        node("c3", "Sentiment scored\n−1 to +1 → index 0–100")
        node("c4", "Topic classified\nfees · exclusivity · ranking · tips …")
        node("c5", "Competition\nissue?", "auto", "diamond")
        node("c6", "Routed to Competition Dept\nlinked to open recommendation")
        node("c7", "Routed to consumer protection\n(MoET / DCCPFT)")
        L.append("c1 -> c2 -> c3 -> c4 -> c5;")
        L.append("{rank=same; c6; c7;}")
        L.append('c5 -> c6 [label="yes"];')
        L.append('c5 -> c7 [label="no"];')
    cluster("cmp", "3C  COMPLAINTS & SENTIMENT", comp)

    # 4. outputs
    def out():
        node("x1", "Authority statistics\nupdated automatically", "out")
        node("x2", "Public register &\ndecisions published", "out")
        node("x3", "Investigations, market studies\n& referrals opened", "out")
        L.append("{rank=same; x1; x2; x3;}")
    cluster("out", "4  OUTPUTS", out)

    # connections between blocks
    mid = len(SOURCES) // 2
    L.append(f"s{mid} -> p2 [ltail=cluster_src, lhead=cluster_pipe];")
    L.append("p2 -> m1 [lhead=cluster_mer, ltail=cluster_pipe];")
    L.append("p3 -> o1 [lhead=cluster_mon, ltail=cluster_pipe];")
    L.append("p3 -> c1 [lhead=cluster_cmp, ltail=cluster_pipe];")
    L.append('c6 -> o5 [style=dashed, color="#CE4B48", label="evidence", constraint=false];')
    L.append("m11 -> x2;")
    L.append("m11 -> x1;")
    L.append("o7 -> x3;")
    L.append("o7 -> x1;")
    L.append("c6 -> x1;")
    L.append("c7 -> x1;")
    L.append("}")
    return "\n".join(L)


def show_dot(dot):
    try:
        st.graphviz_chart(dot, use_container_width=True)
    except TypeError:
        st.graphviz_chart(dot)


def page_overview():
    header("Competition Department — Automated Operations",
           "One system that collects market data through APIs, applies the competition law, recommends decisions and "
           "keeps the authority's statistics up to date.",
           "Staff time moves from collecting and calculating to judging and deciding. Decisions are faster, consistent "
           "with the law, and fully documented.")
    sh = latest_shares(); m = market(); comp = complaints()
    cc = st.columns(5)
    with cc[0]: kpi("Connected sources", f"{len(SOURCES)}", "all through APIs")
    with cc[1]: kpi("Platforms monitored", "6", "online food delivery")
    with cc[2]: kpi("Market HHI", f"{hhi(sh):,.0f}", "highly concentrated", ALERT)
    with cc[3]: kpi("Mergers under review", f"{sum(1 for c in st.session_state.cases.values() if c['decision'] is None)}", "statutory limit 90 days")
    with cc[4]: kpi("Open recommendations", f"{sum(v == 'Pending' for v in st.session_state.recs.values())}", "awaiting a decision", WARN)

    section("How the system works")
    flow = [("1. Extract", f"{len(SOURCES)} sources via API"), ("2. Analyse", "shares, HHI, compliance"), ("3. Apply the law", "UAE rules engine"),
            ("4. Recommend", "with reasons & articles"), ("5. Decide", "officer → Director → Minister"), ("6. Report", "statistics & register")]
    st.markdown('<div style="display:flex;gap:.4rem;flex-wrap:wrap;align-items:stretch">' + "".join(
        f"""<div style="flex:1;min-width:120px;background:{PRIMARY_XL if i % 2 == 0 else '#fff'};border:1px solid {PRIMARY_LT};
        border-radius:10px;padding:.6rem .7rem"><div style="font-weight:700;color:{INK}">{esc(a)}</div>
        <div style="font-size:.78rem;color:{MUTED}">{esc(b)}</div></div>""" + ("" if i == len(flow) - 1 else
        f"<div style='align-self:center;color:{PRIMARY};font-size:1.2rem'>→</div>")
        for i, (a, b) in enumerate(flow)) + "</div>", unsafe_allow_html=True)

    section("Detailed automation flow",
            "Every step behind the dashboard, from data extraction to decisions and statistics. "
            "⚙ blue = automated by the system · 👤 gold = decision by a person · white = output.")
    show_dot(automation_dot())
    st.markdown(f"""<div style="display:flex;flex-wrap:wrap;gap:1rem;font-size:.78rem;color:{MUTED};margin:-.2rem 0 .6rem 0">
        <span><span style="display:inline-block;width:12px;height:12px;background:#DCEAF0;border:1px solid {PRIMARY_LT};
        border-radius:3px;vertical-align:middle"></span> Automated step</span>
        <span><span style="display:inline-block;width:12px;height:12px;background:#FBEBC8;border:1px solid #D9A441;
        border-radius:3px;vertical-align:middle"></span> Human decision</span>
        <span>◇ Decision point</span><span>- - - Feedback, return or cross-link</span>
        <span style="color:#CE4B48">- - - Complaints feed monitoring as evidence</span></div>""", unsafe_allow_html=True)

    a, b = st.columns([1.25, 1])
    with a:
        section("What is automated in each tab")
        table(pd.DataFrame([
            ["Data sources", "Choose sources; pull their data through APIs", "One click instead of weeks of data requests"],
            ["Merger control", "Thresholds, fee, market shares, HHI, legal assessment, recommendation", "Officer starts from a reasoned draft"],
            ["Market monitoring", "Compliance checks against Decision 32/2026 and the Dubai Guidelines", "Problems found before complaints arrive"],
            ["Complaints & sentiment", "Classify, score and route every complaint", "Right authority, linked to open files"],
            ["Authority statistics", "Built from case records", "No manual reporting"],
        ], columns=["Tab", "Automated", "Benefit"]))
    with b:
        section("Latest activity")
        for t, area, text in sorted(st.session_state.activity, reverse=True)[:7]:
            st.markdown(f"<div style='font-size:.8rem;border-bottom:1px solid {BORDER};padding:.28rem 0'>"
                        f"<span style='color:{MUTED}'>{esc(t)} · {esc(area)}</span><br>{esc(text)}</div>", unsafe_allow_html=True)

    section("Legal framework applied by the system", "UAE instruments as of October 2026; the rules engine cites these provisions.")
    table(pd.DataFrame(LEGAL, columns=["Instrument", "Date", "What the system uses"]))


def _apply_preset():
    p = st.session_state.src_preset
    if p in PRESETS:
        st.session_state.src_sel = list(PRESETS[p])


def page_sources():
    header("Data sources",
           "Choose which authorities and data providers to connect, review what each one supplies, and extract the data "
           "through their APIs in one automated run.",
           "Each authority has different mandates, agreements and priorities, so it must decide which sources to connect. "
           "Automated extraction then replaces slow, case-by-case information requests and gives every tab the same "
           "up-to-date figures.")
    sel_all = st.session_state.src_sel
    cc = st.columns(4)
    with cc[0]: kpi("Sources available", f"{len(SOURCES)}", "in the catalogue")
    with cc[1]: kpi("Selected", f"{len(sel_all)}", "for this extraction", PRIMARY if sel_all else MUTED)
    with cc[2]: kpi("Records in selection", f"{sum(source_records(k) for k in sel_all):,}", "across selected APIs")
    with cc[3]: kpi("Last extraction", st.session_state.last_extract.split(" ")[-1], st.session_state.last_extract.split(" ")[0])

    section("1. Choose your data sources", "Start from a preset or pick sources one by one. Only selected sources are shown and extracted.")
    a, b = st.columns([1, 2.6])
    with a:
        st.selectbox("Quick select", ["Custom selection"] + list(PRESETS), key="src_preset", on_change=_apply_preset)
    with b:
        st.multiselect("Data sources to connect", [s_["key"] for s_ in SOURCES], key="src_sel",
                       format_func=lambda k: f"{SRC[k]['name']}  ·  {SRC[k]['cat']}",
                       placeholder="Select one or more sources")
    sel = st.session_state.src_sel
    with st.expander(f"Source catalogue ({len(SOURCES)} available)"):
        table(pd.DataFrame([{"Category": s_["cat"], "Source": s_["name"], "Provider": s_["who"], "Frequency": s_["freq"],
                             "Used by": ", ".join(MODULE_NAMES[m] for m, lst in MODULE_SOURCES.items() if s_["key"] in [k for k, _ in lst]),
                             "Selected": "✓" if s_["key"] in sel else ""} for s_ in SOURCES]))

    if not sel:
        box("<b>No source selected.</b> Choose one or more sources above, or use a quick-select preset, to see their "
            "details and extract their data.", PRIMARY)
        return

    section("2. What your selection supports", "The system checks whether each module has all the data it needs.")
    cols = st.columns(len(MODULE_SOURCES))
    for col, (mod, lst) in zip(cols, MODULE_SOURCES.items()):
        need = [k for k, _ in lst]; missing = [SRC[k]["name"] for k in need if k not in sel]
        have = len(need) - len(missing)
        color = OK if not missing else (WARN if have else ALERT)
        state = "Fully supported" if not missing else ("Partly supported" if have else "Not supported")
        with col:
            st.markdown(f"""<div style="background:#fff;border:1px solid {BORDER};border-top:4px solid {color};border-radius:10px;
                padding:.6rem .8rem;min-height:120px"><div style="font-weight:700;color:{INK}">{esc(MODULE_NAMES[mod])}</div>
                <div style="font-size:.85rem;font-weight:700;color:{color};margin:.15rem 0">{state} · {have}/{len(need)} sources</div>
                <div style="font-size:.76rem;color:{MUTED}">{'Missing: ' + esc(', '.join(missing)) if missing else 'All required sources selected.'}</div></div>""",
                        unsafe_allow_html=True)

    section("3. Selected sources", f"{len(sel)} source(s) ready to extract.")
    cols = st.columns(2)
    for i, k in enumerate(sel):
        s_ = SRC[k]; when = st.session_state.extracted.get(k, "never")
        with cols[i % 2]:
            st.markdown(f"""<div style="background:#fff;border:1px solid {BORDER};border-radius:10px;padding:.7rem .9rem;margin-bottom:.6rem">
                <div style="display:flex;justify-content:space-between;align-items:baseline">
                <div style="font-weight:700;color:{INK}">{esc(s_['name'])}</div>
                <div style="font-size:.68rem;font-weight:700;color:{PRIMARY};background:{PRIMARY_XL};border-radius:999px;padding:.05rem .5rem">{esc(s_['cat'])}</div></div>
                <div style="font-size:.76rem;color:{MUTED}">{esc(s_['who'])}</div>
                <div style="font-size:.8rem;margin-top:.35rem"><b>Data:</b> {esc(s_['data'])}</div>
                <div style="font-size:.8rem"><b>Used for:</b> {esc(s_['why'])}</div>
                <div style="font-family:monospace;font-size:.72rem;background:#F3F8FA;border-radius:6px;padding:.25rem .45rem;
                margin-top:.35rem;color:{PRIMARY_DK}">{esc(s_['api'])}</div>
                <div style="font-size:.72rem;color:{MUTED};margin-top:.3rem"><span style="color:{OK};font-weight:700">● API ready (simulated)</span>
                · REST/JSON · OAuth 2.0 · {esc(s_['freq'])} · {source_records(k):,} records · last extracted {esc(when)}</div></div>""",
                        unsafe_allow_html=True)

    section("4. Extract")
    if st.button(f"⟳  Extract data from {len(sel)} selected source{'s' if len(sel) > 1 else ''}", type="primary", key="extract"):
        with st.status("Extracting data…", expanded=True) as box_:
            rows = extract_lines(sel)
            st.write("✓ Records validated, de-duplicated and linked across sources (licence and register IDs)"); time.sleep(0.25)
            mods = [MODULE_NAMES[m] for m, lst in MODULE_SOURCES.items() if all(k in sel for k, _ in lst)]
            st.write(f"✓ Indicators refreshed for: {', '.join(mods) if mods else 'no complete module (partial update only)'}"); time.sleep(0.2)
            box_.update(label=f"Extraction complete: {len(sel)} source(s), {sum(r['Records'] for r in rows):,} records", state="complete")
        st.session_state.extract_log = rows; st.session_state.last_extract = now(); st.session_state.extract_runs += 1
        act("Data", f"Extraction from {len(sel)} selected source(s) completed")
    if st.session_state.extract_log:
        st.markdown("**Extraction log (last run)**")
        table(pd.DataFrame(st.session_state.extract_log))
    box("<b>Prototype note.</b> Connections are simulated. A live deployment needs a legal basis for each data flow "
        "(e.g. the Ministry's information powers under Art. 18 and the Executive Regulations), data-sharing agreements "
        "with each entity, and compliance with Federal Decree-Law No. 45 of 2021 on personal data protection. "
        "Continuous API reporting by platforms goes beyond today's case-by-case information requests: it would be a "
        "policy option requiring a specific regulatory requirement.", WARN)


# ---------------------------------------------------------------- merger control
def _fresh_case(c):
    return dict(stage=1, log=[(c["received"] + " 09:12", "E-filing portal", "Notification received")],
                decision=None, officer=None, override=None)


def merger_case_view(cid, c):
    s = st.session_state.cases[cid]; m = c["m"]
    deadline = pd.Timestamp(c["complete"]) + pd.Timedelta(days=MERGER_REVIEW_DAYS)
    elapsed = (pd.Timestamp(datetime.now()) - pd.Timestamp(c["complete"])).days
    cc = st.columns(5)
    with cc[0]: kpi("Combined share", f"{m['merged']:.1f}%", f"{m['sa']:.1f}% + {m['sb']:.1f}%", ALERT if m["merged"] > SHARE_THRESHOLD else INK)
    with cc[1]: kpi("UAE sales (AED)", f"{m['turnover']:,}m", "threshold AED 300m")
    with cc[2]: kpi("ΔHHI", f"{m['delta']:,.0f}", f"HHI {m['pre']:,.0f} → {m['post']:,.0f}")
    with cc[3]: kpi("Filing fee", f"AED {m['fee']:,.0f}", "0.02%, cap AED 150,000")
    with cc[4]: kpi("Review clock", f"Day {elapsed} of 90", f"deadline {deadline:%d %b %Y}", WARN if elapsed > 60 else OK)
    stepper(MERGER_STEPS, s["stage"])

    if s["stage"] < 5:
        box(f"<b>{esc(c['kind'])}.</b> Notified {esc(c['received'])}. Press the button to run the automated steps live.")
        if st.button("▶  Run automated review", type="primary", key=f"run_{cid}"):
            run_steps("Running automated review…", [
                "Notification registered on the e-filing portal",
                "Completeness check passed: economic report, 3 years of financial statements, transaction agreement",
                f"Turnover verified with the Federal Tax Authority: AED {m['turnover']:,}m",
                f"Filing fee calculated: AED {m['fee']:,.0f} — payment confirmed",
                "Transaction summary published on the Ministry website for third-party observations",
                f"Market shares pulled from platform APIs: {m['sa']:.1f}% + {m['sb']:.1f}%",
                f"HHI {m['pre']:,.0f} → {m['post']:,.0f}; notification thresholds and Art. 15 test applied",
                "Ownership links checked in the National Economic Register",
                "Recommendation and reasoned draft report generated"])
            _complete_review(cid, c)
            st.rerun()
        return

    color = OK if c["rec"] == "Approve" else ALERT
    st.markdown(f"""<div style="background:#fff;border:2px solid {color};border-radius:12px;padding:.8rem 1rem;margin:.2rem 0 .7rem 0">
        <div style="font-size:.7rem;color:{MUTED};font-weight:700;text-transform:uppercase;letter-spacing:.05em">Automated recommendation · {esc(c['confidence'])} confidence</div>
        <div style="font-size:1.35rem;font-weight:800;color:{color}">{'APPROVE' if c['rec'] == 'Approve' else 'DO NOT APPROVE (REJECT)'}</div>
        <div style="font-size:.9rem;color:{INK};margin-top:.2rem">{esc(c['headline'])}</div></div>""", unsafe_allow_html=True)

    section("Detailed assessment report", "Drafted automatically from the data and the UAE legal framework.")
    left, right = st.columns(2)
    for i, (title, bullets) in enumerate(c["sections"]):
        with (left if i % 2 == 0 else right):
            st.markdown(f"""<div style="background:#fff;border:1px solid {BORDER};border-radius:10px;padding:.6rem .85rem;margin-bottom:.55rem">
                <div style="font-weight:700;color:{PRIMARY_DK};font-size:.88rem">{esc(title)}</div>
                <ul style="margin:.25rem 0 0 1rem;font-size:.82rem">{''.join(f'<li>{esc(b)}</li>' for b in bullets)}</ul></div>""",
                        unsafe_allow_html=True)

    section("Decision workflow")
    if s["stage"] == 5:
        st.markdown("**Case officer:** review the draft report.")
        b1, b2 = st.columns([1, 1.4])
        if b1.button(f"Accept recommendation ({c['rec']})", type="primary", key=f"acc_{cid}"):
            s["officer"] = c["rec"]; s["stage"] = 6; s["log"].append((now(), "Case officer", f"Accepted recommendation: {c['rec']}"))
            act("Merger", f"{cid}: case officer accepted the recommendation"); st.rerun()
        with b2.expander("Override with justification"):
            alt = st.selectbox("Alternative", [x for x in ["Approve", "Approve with conditions", "Reject"] if x != c["rec"]], key=f"alt_{cid}")
            why = st.text_area("Justification (required)", key=f"why_{cid}")
            if st.button("Submit override", key=f"ovr_{cid}"):
                if not why.strip():
                    st.error("A justification is required.")
                else:
                    s["officer"] = alt; s["override"] = why.strip(); s["stage"] = 6
                    s["log"].append((now(), "Case officer", f"Override → {alt}: {why.strip()}"))
                    act("Merger", f"{cid}: case officer overrode the recommendation"); st.rerun()
    elif s["stage"] == 6:
        st.markdown(f"**Director of Competition Department:** officer's recommendation is **{esc(s['officer'])}**. "
                    "Approve the reasoned report and send it to the Minister?")
        if s["override"]:
            box(f"Officer overrode the system: {esc(s['override'])}", WARN)
        b1, b2 = st.columns(2)
        if b1.button("Approve report → send to Minister", type="primary", key=f"dir_{cid}"):
            s["stage"] = 7; s["log"].append((now(), "Director", "Reasoned report approved and sent to the Minister"))
            act("Merger", f"{cid}: Director sent report to the Minister"); st.rerun()
        if b2.button("Return to case officer", key=f"dret_{cid}"):
            s["stage"] = 5; s["log"].append((now(), "Director", "Returned to case officer")); st.rerun()
    elif s["stage"] == 7:
        st.markdown(f"**Minister of Economy and Tourism:** decision under Art. 15. Recommended: **{esc(s['officer'])}**.")
        opts = ["Approve", "Approve with conditions", "Reject"]
        dec = st.radio("Decision", opts, index=opts.index(s["officer"]), horizontal=True, key=f"dec_{cid}")
        if st.button("Issue decision", type="primary", key=f"min_{cid}"):
            run_steps("Publishing decision…", ["Decision letter generated and sent to the parties through the portal",
                                               "Decision published in the Ministry's register", "Authority statistics updated"], 0.3)
            s["decision"] = dec; s["stage"] = 9
            s["log"] += [(now(), "Minister", f"Decision: {dec}"), (now(), "System", "Published; statistics updated")]
            act("Merger", f"{cid}: Minister's decision — {dec}"); st.rerun()
    else:
        box(f"<b>Decision issued: {esc(s['decision'])}.</b> Published and counted in the authority statistics.",
            OK if s["decision"] != "Reject" else ALERT)

    with st.expander("Audit trail"):
        table(pd.DataFrame(s["log"], columns=["Time", "By", "Event"]))
    if st.button("Reset this case", key=f"reset_{cid}"):
        st.session_state.cases[cid] = _fresh_case(c); st.rerun()


def _complete_review(cid, c):
    s = st.session_state.cases[cid]; m = c["m"]
    if s["stage"] >= 5:
        return
    s["stage"] = 5
    s["log"] += [(now(), "System", t) for t in ["Completeness check passed", f"Fee AED {m['fee']:,.0f} paid",
                                                "Published for observations", f"Automated recommendation: {c['rec']}"]]
    act("Merger", f"{cid}: automated review completed — recommendation: {c['rec']}")


def merger_calc_sheet(cases):
    rows = {}
    for cid, c in cases.items():
        m = c["m"]; lc = local_check(c["acquirer"], c["target"])
        notif = []
        if m["turnover"] > TURNOVER_THRESHOLD: notif.append("sales")
        if m["merged"] > SHARE_THRESHOLD: notif.append("share")
        rows[f"{cid} · {c['acquirer']} / {c['target']}"] = [
            c["kind"], f"{m['sa']:.1f}% + {m['sb']:.1f}% = {m['merged']:.1f}%", f"AED {m['turnover']:,}m",
            ("Yes — " + " and ".join(notif) + " threshold") if notif else "No",
            f"AED {m['fee']:,.0f}" + (" (capped)" if m["fee"] >= FEE_CAP else ""),
            f"{m['pre']:,.0f} → {m['post']:,.0f}", f"{m['delta']:,.0f}",
            f"{min(r['merged'] for r in lc):.0f}%–{max(r['merged'] for r in lc):.0f}% by emirate",
            f"#{m['rank']} nationally",
            c["rec"], c["confidence"]]
    idx = ["Transaction type", "Market shares (orders)", "Combined UAE sales", "Notifiable (Cabinet Res. 3/2025)",
           "Filing fee (Cabinet Res. 105/2026)", "HHI pre → post", "ΔHHI", "Combined share, local check", "Rank of merged firm",
           "Recommendation (Art. 15)", "Confidence"]
    return pd.DataFrame(rows, index=idx).reset_index().rename(columns={"index": "Calculated item"})


def page_mergers():
    header("Merger control",
           "Each notification is checked, priced, published and assessed automatically against UAE law. The case officer "
           "receives a reasoned recommendation; the Director and the Minister decide.",
           "The law gives 90 days (extendable by 45) and treats silence as rejection (Art. 13). Automation lets the "
           "department decide well within the deadline, with every step recorded.")
    source_strip("merger")
    cases = merger_cases()
    mode = mode_selector("merger_mode")
    labels = {cid: f"{cid} · {c['title']}" for cid, c in cases.items()}

    if mode == "Fully automated":
        if not st.session_state.merger_auto_done:
            mode_banner("One click: from raw data to two reasoned recommendations",
                        ["Extract 4 sources", "Validate & link parties", "Market shares & HHI", "Thresholds & fees",
                         "Emirate check", "Art. 15 assessment", "Draft reports", "Assign to case officer"])
            if st.button("⚙  Calculate & generate reviews", type="primary", key="merger_auto"):
                sh = latest_shares(); pre = hhi(sh)
                with st.status("Calculating and generating…", expanded=True) as box_:
                    extract_lines([k for k, _ in MODULE_SOURCES["merger"]])
                    for line in ["Parties matched across e-filing portal, Federal Tax Authority and National Economic Register",
                                 f"Market shares calculated for 6 platforms, nationally and in 7 emirates; market HHI {pre:,.0f}"]:
                        st.write("✓ " + line); time.sleep(0.25)
                    for cid, c in cases.items():
                        m = c["m"]; lc = local_check(c["acquirer"], c["target"])
                        for line in [f"{cid}: UAE sales AED {m['turnover']:,}m, combined share {m['merged']:.1f}% → notifiable; fee AED {m['fee']:,.0f}",
                                     f"{cid}: ΔHHI {m['delta']:,.0f}, HHI {m['pre']:,.0f} → {m['post']:,.0f}; local shares "
                                     f"{min(r['merged'] for r in lc):.0f}–{max(r['merged'] for r in lc):.0f}%",
                                     f"{cid}: Art. 15 assessment → recommendation {c['rec'].upper()} ({c['confidence']} confidence)"]:
                            st.write("✓ " + line); time.sleep(0.25)
                        _complete_review(cid, c)
                    st.write("✓ Two reasoned draft reports generated and assigned to the case officer"); time.sleep(0.2)
                    box_.update(label="Done: data extracted, calculations completed, 2 reviews generated", state="complete")
                st.session_state.merger_auto_done = True
                act("Merger", "Fully automated run: 2 merger reviews generated")
                st.rerun()
            return
        section("Calculation results", "Everything below was calculated automatically from the extracted data.")
        table(merger_calc_sheet(cases))
        cols = st.columns(2)
        for col, (cid, c) in zip(cols, cases.items()):
            s = st.session_state.cases[cid]; color = OK if c["rec"] == "Approve" else ALERT
            status = f"Decision issued: {s['decision']}" if s["decision"] else f"Now at: {MERGER_STEPS[min(s['stage'], 8)][0]}"
            with col:
                st.markdown(f"""<div style="background:#fff;border:1px solid {BORDER};border-top:5px solid {color};border-radius:10px;
                    padding:.7rem .9rem;min-height:150px"><div style="font-size:.74rem;color:{MUTED};font-weight:700">{esc(cid)}</div>
                    <div style="font-weight:700;color:{INK}">{esc(c['title'])}</div>
                    <div style="font-size:1.1rem;font-weight:800;color:{color};margin:.2rem 0">{'APPROVE' if c['rec'] == 'Approve' else 'REJECT'}</div>
                    <div style="font-size:.8rem">{esc(c['headline'])}</div>
                    <div style="font-size:.74rem;color:{PRIMARY_DK};font-weight:700;margin-top:.35rem">{esc(status)}</div></div>""",
                            unsafe_allow_html=True)
        section("Review the cases", "Open a case to read the full report and take it through the decision workflow.")
        cid = st.radio("Case", list(cases), format_func=lambda x: labels[x], horizontal=True, key="mcase_auto")
        merger_case_view(cid, cases[cid])
        if st.button("↺  Run the fully automated mode again", key="merger_auto_reset"):
            st.session_state.merger_auto_done = False
            for k, c in cases.items():
                st.session_state.cases[k] = _fresh_case(c)
            st.rerun()
        return

    cid = st.radio("Case", list(cases), format_func=lambda x: labels[x], horizontal=True, key="mcase")
    merger_case_view(cid, cases[cid])


# ---------------------------------------------------------------- market monitoring
def monitoring_body(use_study):
    sh = latest_shares(); m = market()
    lead = max(sh, key=sh.get)
    cc = st.columns(5)
    with cc[0]: kpi("HHI", f"{hhi(sh):,.0f}", "above 1,800 = highly concentrated", ALERT)
    with cc[1]: kpi("Market leader", lead, f"{sh[lead]:.0f}% of orders (screening level 40%)", ALERT)
    with cc[2]: kpi("Top 3 share", f"{sum(sorted(sh.values())[-3:]):.0f}%", "CR3")
    with cc[3]: kpi("Avg commission", f"{m[m['Month'] == m['Month'].max()]['Commission'].mean():.1f}%", "charged to restaurants")
    with cc[4]: kpi("Rule breaches", f"{sum(not r[2](d) for d in COMPLIANCE_DATA.values() for r in RULES)}", "across 6 platforms", WARN)

    # ---- early-warning signs
    study, live = warning_signs(use_study)
    allsg = study + live
    n_red = sum(x["level"] == "red" for x in allsg); n_amb = sum(x["level"] == "amber" for x in allsg)
    n_grn = sum(x["level"] == "green" for x in allsg)
    section("Early-warning signs", "Signals that a market problem may be developing and whether the investigator should act now.")
    st.markdown(f"""<div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.6rem">
        <div style="background:#FBE9E8;border:1px solid {ALERT};border-radius:8px;padding:.35rem .8rem;font-weight:700;color:{ALERT}">● {n_red} need further action</div>
        <div style="background:#FDF3E1;border:1px solid {WARN};border-radius:8px;padding:.35rem .8rem;font-weight:700;color:#9A6B12">● {n_amb} to watch / request information</div>
        <div style="background:#E6F4EF;border:1px solid {OK};border-radius:8px;padding:.35rem .8rem;font-weight:700;color:{OK}">● {n_grn} checked, no concern</div></div>""",
                unsafe_allow_html=True)
    if use_study:
        ms = MARKET_STUDY
        box(f"<b>Earlier market study found: {esc(ms['id'])} · {esc(ms['title'])} ({esc(ms['completed'])}).</b> "
            "The system compares today's data with the study's baselines and checks whether its concerns have grown.<br>"
            + "<span style='font-size:.8rem;color:#5F707A'>Study findings: " + " · ".join(esc(f) for f in ms["findings"]) + "</span>",
            PRIMARY)
        st.markdown("**Compared with the earlier market study**")
        sign_cards(study)
        st.markdown("**Other live warning signs**")
    else:
        box("<b>No earlier market study found for this market.</b> The system applies its general early-warning "
            "indicators to live data: complaints, commission patterns, acquisitions, ownership links, sentiment and "
            "pricing. Recommendation: commission a market study to set baselines (see R6).", WARN)
    sign_cards(live)

    a, b = st.columns(2)
    with a:
        section("Market shares (orders)")
        fig = px.line(m, x="Date", y="Share", color="Platform", color_discrete_map=PCOL)
        fig.add_hline(y=40, line_dash="dot", line_color=ALERT, annotation_text="40% screening level (not a legal presumption)")
        fig.update_yaxes(title="% of orders"); show(style(fig, 300))
    with b:
        section("Commission charged to restaurants")
        fig = px.line(m, x="Date", y="Commission", color="Platform", color_discrete_map=PCOL)
        fig.update_yaxes(title="% of order value"); show(style(fig, 300))

    section("Where the platforms operate",
            "Market share by emirate (bubble size = emirate's share of UAE orders) and headquarters (dark markers). "
            "Delivery markets are local, so competition can differ between emirates.")
    sel = st.selectbox("Colour the map by", ["Leading platform"] + NAMES, key="map_sel")
    fig, piv = uae_map(sel)
    show(fig)
    st.caption("Map tiles need an internet connection. Hover over a bubble for every platform's share in that emirate.")
    with st.expander("Shares by emirate (table)"):
        t = piv.round(1).reset_index()
        t.insert(1, "Orders (% of UAE)", [EMIRATES[e][2] * 100 for e in t["Emirate"]])
        table(t)

    section("Automated compliance checks", "Platform data tested against all active rules. ✓ compliant · ✗ breach")
    rows = []
    for p, d in COMPLIANCE_DATA.items():
        row = {"Platform": p}
        for name, basis, test, val in RULES:
            row[name] = ("✓ " if test(d) else "✗ ") + val(d)
        rows.append(row)
    table(pd.DataFrame(rows))
    st.caption(" · ".join(f"{n}: {b}" for n, b, _, _ in RULES))
    st.caption("Dubai Guidelines items are enforced by the Dubai Corporation for Consumer Protection and Fair Trade; the "
               "department's role there is detection and referral, in cooperation with DCCPFT (Arts. 20–21).")

    section("Recommended actions", "Generated by the rules engine. Approve to execute the action automatically.")
    for r in RECOMMENDATIONS:
        status = st.session_state.recs[r["id"]]
        color = {"High": ALERT, "Medium": WARN, "Low": PRIMARY}[r["priority"]]
        with st.container():
            st.markdown(f"""<div style="background:#fff;border:1px solid {BORDER};border-left:5px solid {color};border-radius:10px;
                padding:.6rem .9rem;margin-top:.5rem"><div style="display:flex;justify-content:space-between">
                <div style="font-weight:700;color:{INK}">{esc(r['id'])} · {esc(r['platform'])}: {esc(r['title'])}</div>
                <div style="font-size:.72rem;font-weight:700;color:{color}">{esc(r['priority'])} priority · {esc(status)}</div></div>
                <div style="font-size:.83rem;margin-top:.2rem">{esc(r['finding'])}</div>
                <div style="font-size:.78rem;color:{MUTED};margin-top:.2rem"><b>Legal basis:</b> {esc(r['basis'])}</div>
                <div style="font-size:.83rem;margin-top:.2rem"><b>Recommended action:</b> {esc(r['action'])}</div></div>""",
                        unsafe_allow_html=True)
            with st.expander("Explain this recommendation"):
                for head, body in EXPLANATIONS.get(r["id"], []):
                    st.markdown(f"**{head}**  \n{body}")
            if status == "Pending":
                b1, b2, _ = st.columns([1, 1, 3])
                if b1.button("Approve action", key=f"ra_{r['id']}", type="primary"):
                    run_steps("Executing…", [r["result"]], 0.4)
                    st.session_state.recs[r["id"]] = "Approved"; act("Monitoring", f"{r['id']} approved: {r['result']}"); st.rerun()
                if b2.button("Dismiss", key=f"rd_{r['id']}"):
                    st.session_state.recs[r["id"]] = "Dismissed"; act("Monitoring", f"{r['id']} dismissed"); st.rerun()
            elif status == "Approved":
                st.caption(f"✓ Done: {r['result']}")


def page_monitoring():
    header("Market monitoring (ex-ante)",
           "The system watches the market continuously: concentration, commissions, early-warning signs and each "
           "platform's compliance with the food delivery rules. It turns every breach into a recommended action with its "
           "legal basis.",
           "Acting before harm occurs is cheaper and faster than a full investigation after the fact. Early-warning signs "
           "tell the investigator which issues need further action now, and continuous checks show whether the rules are working.")
    source_strip("monitoring")
    a, b = st.columns([2, 1.2])
    with a:
        mode = mode_selector("mon_mode")
    with b:
        no_study = st.toggle("Demo: assume no earlier market study exists", key="no_study",
                             help="Shows how the system switches to general warning signs when the archive has no study for this market.")
    use_study = not no_study

    if mode == "Fully automated":
        if not st.session_state.mon_auto_done:
            mode_banner("One click: from raw data to early-warning signs and recommended actions",
                        ["Extract 6 sources", "Validate & link", "Shares, HHI, margins", "Check 7 rules × 6 platforms",
                         "Scan market-study archive", "Early-warning signs", "Recommended actions"])
            if st.button("⚙  Calculate & generate", type="primary", key="mon_auto"):
                sh = latest_shares(); study, live = warning_signs(use_study)
                breaches = sum(not r[2](d) for d in COMPLIANCE_DATA.values() for r in RULES)
                with st.status("Calculating and generating…", expanded=True) as box_:
                    extract_lines([k for k, _ in MODULE_SOURCES["monitoring"]])
                    lines = [f"Indicators calculated: HHI {hhi(sh):,.0f}, leader {max(sh.values()):.0f}%, CR3 {sum(sorted(sh.values())[-3:]):.0f}%",
                             "Shares by emirate and revenue per order vs average variable cost calculated",
                             f"{len(RULES)} rules checked on 6 platforms: {breaches} breaches found",
                             (f"Market-study archive scanned: {MARKET_STUDY['id']} ({MARKET_STUDY['completed']}) found, "
                              f"{len(MARKET_STUDY['baselines'])} baselines loaded") if use_study else
                             "Market-study archive scanned: no study for this market → general early-warning indicators applied",
                             f"Early-warning signs: {sum(x['level'] == 'red' for x in study + live)} need further action, "
                             f"{sum(x['level'] == 'amber' for x in study + live)} to watch",
                             f"{len(RECOMMENDATIONS)} recommended actions generated with legal basis and priority"]
                    for line in lines:
                        st.write("✓ " + line); time.sleep(0.3)
                    box_.update(label="Done: monitoring results generated", state="complete")
                st.session_state.mon_auto_done = True
                act("Monitoring", "Fully automated monitoring run completed")
                st.rerun()
            return
        if st.button("↺  Run the fully automated mode again", key="mon_auto_reset"):
            st.session_state.mon_auto_done = False; st.rerun()
    else:
        if st.button("▶  Run monitoring cycle", type="primary", key="cycle"):
            run_steps("Running monitoring cycle…", ["Latest platform data pulled", "Market shares and HHI recalculated",
                                                    f"{len(RULES)} rules checked on 6 platforms",
                                                    "Early-warning signs updated",
                                                    f"{len(RECOMMENDATIONS)} recommendations generated with legal basis"])
            act("Monitoring", "Monitoring cycle completed")
    monitoring_body(use_study)


# ---------------------------------------------------------------- complaints
def page_complaints():
    header("Complaints & sentiment",
           "Complaints from consumer protection channels and public app reviews are collected automatically, separated by "
           "who is complaining — consumers, restaurants or riders — scored, classified and routed to the right authority.",
           "Consumers and restaurants experience different problems. Consumer complaints mostly concern service and fees "
           "(consumer protection); restaurant complaints often reveal competition issues such as exclusivity, "
           "retaliation and self-preferencing. Separating them sends each to the right team.")
    source_strip("complaints")
    mode = mode_selector("cmp_mode")
    if mode == "Fully automated":
        if not st.session_state.get("cmp_auto_done"):
            mode_banner("One click: from raw complaints and reviews to routed cases and insights",
                        ["Extract 3 sources", "Remove personal data", "Identify complainant", "Score sentiment",
                         "Classify issue", "Normalise rates", "Route & link", "Generate insights"])
            if st.button("⚙  Calculate & generate", type="primary", key="cmp_auto"):
                comp = complaints(); end = comp["Date"].max()
                r90 = comp[comp["Date"] > end - pd.Timedelta(days=90)]
                who = comp["Complainant"].value_counts()
                rest = comp[comp["Complainant"] == "Restaurant"]
                compet = rest["Category"].isin(COMPETITION_CATEGORIES)
                ss_ = sentiment_series(); lastm = ss_[ss_["Date"] == ss_["Date"].max()].set_index("Platform")["Sentiment"]
                below = [p for p in NAMES if lastm[p] < 50]
                linked = int(r90["Category"].map(REC_LINK).notna().sum())
                with st.status("Calculating and generating…", expanded=True) as box_:
                    extract_lines([k for k, _ in MODULE_SOURCES["complaints"]])
                    for line in [f"{len(comp):,} complaints and {SRC['reviews']['records']:,} reviews processed; personal data removed",
                                 f"Complainants identified: {who.get('Consumer', 0):,} consumers · {who.get('Restaurant', 0):,} restaurants · "
                                 f"{who.get('Rider', 0):,} riders",
                                 "Language detected (Arabic / English); sentiment scored from −1 to +1 and rescaled to a 0–100 index",
                                 f"Issues classified into {comp['Category'].nunique()} categories; {compet.mean() * 100:.0f}% of restaurant "
                                 "complaints are competition-related",
                                 "Rates normalised: consumer complaints per 100,000 orders, restaurant complaints per 1,000 listed restaurants",
                                 f"Routed: Competition Department · consumer protection (MoET / DCCPFT) · labour referral; "
                                 f"{linked} recent complaints linked to monitoring recommendations",
                                 f"Insights generated: sentiment below the watch level for {', '.join(below) or 'no platform'}; "
                                 "commission complaints at Saffron Go up almost fourfold since June 2026"]:
                        st.write("✓ " + line); time.sleep(0.3)
                    box_.update(label="Done: complaints separated, scored, routed and analysed", state="complete")
                st.session_state.cmp_auto_done = True
                act("Complaints", "Fully automated complaints run completed")
                st.rerun()
            return
        if st.button("↺  Run the fully automated mode again", key="cmp_auto_reset"):
            st.session_state.cmp_auto_done = False; st.rerun()
    comp = complaints(); end = comp["Date"].max()
    last90 = comp[comp["Date"] > end - pd.Timedelta(days=90)]
    m = market(); lm = m[m["Month"] == m["Month"].max()].set_index("Platform")
    who_counts = comp["Complainant"].value_counts()
    cc = st.columns(4)
    with cc[0]: kpi("All complaints (12 months)", f"{len(comp):,}", "all channels")
    with cc[1]: kpi("From consumers", f"{who_counts.get('Consumer', 0):,}", f"{who_counts.get('Consumer', 0) / len(comp) * 100:.0f}% of total")
    with cc[2]: kpi("From restaurants", f"{who_counts.get('Restaurant', 0):,}",
                    f"{(comp[comp['Complainant'] == 'Restaurant']['Category'].isin(COMPETITION_CATEGORIES)).mean() * 100:.0f}% competition-related", ALERT)
    with cc[3]: kpi("From riders", f"{who_counts.get('Rider', 0):,}", "pay and tips")

    t1, t2, t3, t4 = st.tabs(["👥  Consumers", "🍽  Restaurants", "🛵  Riders", "⚡  Live processing"])
    with t1:
        cons = comp[comp["Complainant"] == "Consumer"]; c90 = last90[last90["Complainant"] == "Consumer"]
        ss_ = sentiment_series(); lastm = ss_[ss_["Date"] == ss_["Date"].max()]
        neg = c90[c90["Category"] != "Positive feedback"]
        rate = {p: (neg["Platform"] == p).sum() / (lm.loc[p, "Orders"] * 3) * 100_000 for p in NAMES}
        top = neg["Category"].value_counts().idxmax() if len(neg) else "—"
        k = st.columns(4)
        with k[0]: kpi("Consumer complaints", f"{len(cons[cons['Category'] != 'Positive feedback']):,}", "12 months, excl. praise")
        with k[1]: kpi("Sentiment index", f"{lastm['Sentiment'].mean():.0f}/100", "market average (app reviews)")
        with k[2]: kpi("Top issue (90 days)", top, f"{(neg['Category'] == top).sum()} complaints")
        with k[3]: kpi("Closed within 7 working days", f"{(cons['Days'] <= 9).mean() * 100:.0f}%", "Dubai Guidelines target")
        a, b = st.columns(2)
        with a:
            section("Consumer sentiment by platform (0–100)")
            fig = px.line(ss_, x="Date", y="Sentiment", color="Platform", color_discrete_map=PCOL)
            fig.add_hline(y=50, line_dash="dot", line_color=ALERT, annotation_text="watch level")
            show(style(fig, 300))
            st.caption("0 = all negative · 50 = neutral · 100 = all positive; index = (average score + 1) ÷ 2 × 100.")
        with b:
            section("Complaints per 100,000 orders (last 90 days)", "Normalised by each platform's order volume.")
            r = pd.DataFrame({"Platform": list(rate), "Rate": list(rate.values())}).sort_values("Rate")
            fig = go.Figure(go.Bar(x=r["Rate"], y=r["Platform"], orientation="h", marker_color=[PCOL[p] for p in r["Platform"]],
                                   text=[f"{v:.1f}" for v in r["Rate"]], textposition="outside", cliponaxis=False))
            show(style(fig, 300, False))
        section("What consumers complain about (last 90 days)")
        g = neg.groupby(["Category", "Platform"]).size().reset_index(name="n")
        fig = px.bar(g, x="n", y="Category", color="Platform", orientation="h", color_discrete_map=PCOL)
        fig.update_xaxes(title="Complaints"); fig.update_yaxes(title=None); show(style(fig, 260))
        box("<b>Routing:</b> consumer complaints go to consumer protection (MoET / DCCPFT). Hidden-fee complaints about "
            "Oasis Delivery are linked to monitoring recommendation R4.", PRIMARY)
    with t2:
        rest = comp[comp["Complainant"] == "Restaurant"]; r90 = last90[last90["Complainant"] == "Restaurant"]
        compet = r90[r90["Category"].isin(COMPETITION_CATEGORIES)]
        per1k = {p: (r90["Platform"] == p).sum() / LISTED_RESTAURANTS[p] * 1000 for p in NAMES}
        worst = max(per1k, key=per1k.get)
        k = st.columns(4)
        with k[0]: kpi("Restaurant complaints", f"{len(rest):,}", "12 months")
        with k[1]: kpi("Competition-related", f"{len(compet) / max(len(r90), 1) * 100:.0f}%", "last 90 days → Competition Dept", ALERT)
        with k[2]: kpi("Highest rate", worst, f"{per1k[worst]:.1f} per 1,000 listed restaurants")
        with k[3]: kpi("Top competition issue", compet["Category"].value_counts().idxmax() if len(compet) else "—", "last 90 days")
        a, b = st.columns(2)
        with a:
            section("Restaurant complaints per month, by issue")
            g = rest.assign(Month=rest["Date"].dt.to_period("M").dt.to_timestamp()).groupby(["Month", "Category"]).size().reset_index(name="n")
            fig = px.bar(g, x="Month", y="n", color="Category",
                         color_discrete_sequence=["#B4553A", "#CE4B48", "#D9A441", "#1C7C9C", "#155E76", "#64748B", "#9FCAD8", "#7B6BB0"])
            fig.update_yaxes(title="Complaints"); show(style(fig, 320))
        with b:
            section("Complaints per 1,000 listed restaurants (last 90 days)", "Normalised by each platform's restaurant base.")
            r = pd.DataFrame({"Platform": list(per1k), "Rate": list(per1k.values())}).sort_values("Rate")
            fig = go.Figure(go.Bar(x=r["Rate"], y=r["Platform"], orientation="h", marker_color=[PCOL[p] for p in r["Platform"]],
                                   text=[f"{v:.1f}" for v in r["Rate"]], textposition="outside", cliponaxis=False))
            show(style(fig, 320, False))
        section("Competition-related restaurant complaints, last 90 days", "Each issue is linked to a monitoring recommendation.")
        g = compet.groupby(["Category", "Platform"]).size().reset_index(name="Complaints").sort_values("Complaints", ascending=False)
        g["Linked to"] = g["Category"].map(REC_LINK).fillna("—"); g["Routed to"] = "Competition Department"
        table(g)
        box("<b>Automated insights.</b> Saffron Go: commission complaints rose almost fourfold after June 2026 → R3. Nexa Eats: "
            "exclusivity pressure and lower ranking after multi-homing → R1. Dunebite: own kitchens ranked above "
            "restaurants → R2. Non-competition restaurant issues (late payments, unconsented fees, data access) are "
            "referred to DCCPFT.", PRIMARY)
    with t3:
        rid = comp[comp["Complainant"] == "Rider"]; rd90 = last90[last90["Complainant"] == "Rider"]
        k = st.columns(3)
        with k[0]: kpi("Rider complaints", f"{len(rid):,}", "12 months")
        with k[1]: kpi("About tips", f"{(rid['Category'] == 'Rider payments').mean() * 100:.0f}%", "Dubai Guidelines: 100% to riders")
        with k[2]: kpi("Most complaints", rd90["Platform"].value_counts().idxmax() if len(rd90) else "—", "last 90 days")
        g = rd90.groupby(["Category", "Platform"]).size().reset_index(name="n")
        fig = px.bar(g, x="n", y="Category", color="Platform", orientation="h", color_discrete_map=PCOL)
        fig.update_xaxes(title="Complaints (last 90 days)"); fig.update_yaxes(title=None); show(style(fig, 240))
        box("Tip complaints are linked to R4 (Oasis Delivery) and routed to consumer protection; pay cuts are referred "
            "to the labour authorities.", PRIMARY)
    with t4:
        section("Live processing", "Fetch the newest complaints and watch the system separate, classify and route them.")
        if st.button("▶  Fetch & analyse new complaints", type="primary", key="fetch"):
            run_steps("Analysing new complaints…", ["New items pulled from MoET, DCCPFT and app reviews",
                                                    "Complainant identified: consumer, restaurant or rider",
                                                    "Language detected (Arabic / English) and personal data removed",
                                                    "Sentiment scored", "Issue classified and routed", "Linked to open files"], 0.3)
            st.session_state.batch_done = True; act("Complaints", "New complaints separated, classified and routed")
        if st.session_state.batch_done:
            new = pd.concat([comp[comp["Complainant"] == w].sort_values("Date").tail(n) for w, n in
                             [("Consumer", 4), ("Restaurant", 4), ("Rider", 1)]])
            table(pd.DataFrame({"Received": new["Date"].dt.strftime("%Y-%m-%d"), "Complainant": new["Complainant"],
                                "Channel": new["Channel"], "Platform": new["Platform"], "Text": new["Text"],
                                "Sentiment": new["Sentiment"].round(2), "Issue": new["Category"], "Routed to": new["Route"],
                                "Linked to": new["Category"].map(REC_LINK).fillna("—")}))


def page_statistics():
    header("Authority statistics",
           "Produced automatically from case records and monitoring data. Decisions taken in this demo are added live.",
           "Shows the authority's workload, speed and results to management, government and the public, without "
           "manual reporting.")
    cases = merger_cases(); live = st.session_state.cases
    decided = [live[c]["decision"] for c in live if live[c]["decision"]]
    years = ["2023", "2024", "2025", "2026 YTD"]
    notified = [21, 34, 58, 69]; approved = [19, 30, 52, 57]; conditions = [1, 3, 4, 6]; rejected = [0, 1, 1, 2]
    approved[-1] += decided.count("Approve"); conditions[-1] += decided.count("Approve with conditions"); rejected[-1] += decided.count("Reject")
    avg_days = [74, 66, 51, 38]
    recs_done = sum(v == "Approved" for v in st.session_state.recs.values())
    cc = st.columns(5)
    with cc[0]: kpi("Mergers notified 2026", f"{notified[-1]}", "+ 2 live demo cases")
    with cc[1]: kpi("Average review time", f"{avg_days[-1]} days", "illustrative · statutory limit 90", OK)
    with cc[2]: kpi("Fees collected since July 2026", "AED 2.41m", "Cabinet Res. 105/2026")
    with cc[3]: kpi("Complaints handled", f"{len(complaints()):,}", "last 12 months")
    with cc[4]: kpi("Monitoring actions", f"{4 + recs_done}", f"{recs_done} approved in this session")

    a, b = st.columns(2)
    with a:
        section("Merger decisions per year")
        df = pd.DataFrame({"Year": years * 3, "Decision": ["Approved"] * 4 + ["With conditions"] * 4 + ["Rejected"] * 4,
                           "Cases": approved + conditions + rejected})
        fig = px.bar(df, x="Year", y="Cases", color="Decision", color_discrete_map={"Approved": OK, "With conditions": WARN, "Rejected": ALERT})
        show(style(fig, 300))
    with b:
        section("Average merger review time (days)")
        fig = go.Figure(go.Bar(x=years, y=avg_days, marker_color=PRIMARY, text=avg_days, textposition="outside"))
        fig.add_hline(y=90, line_dash="dot", line_color=ALERT, annotation_text="90-day limit (Art. 13)")
        fig.update_yaxes(range=[0, 110]); show(style(fig, 300, False))
    a, b = st.columns(2)
    with a:
        section("Enforcement and monitoring activity, 2026")
        act_df = pd.DataFrame({"Activity": ["Complaints assessed (Art. 34)", "Ex officio investigations", "Information requests via API",
                                            "Market studies (Art. 18)", "Exemption decisions", "Referrals to consumer protection"],
                               "Count": [412, 7 + (st.session_state.recs["R1"] == "Approved"), 64 + 2 * recs_done,
                                         2 + (st.session_state.recs["R6"] == "Approved"), 5,
                                         38 + (st.session_state.recs["R3"] == "Approved") + (st.session_state.recs["R4"] == "Approved")]})
        fig = go.Figure(go.Bar(x=act_df["Count"], y=act_df["Activity"], orientation="h", marker_color=PRIMARY,
                               text=act_df["Count"], textposition="outside", cliponaxis=False))
        fig.update_yaxes(autorange="reversed"); show(style(fig, 300, False))
    with b:
        section("Platform compliance with all active rules", f"Number of the {len(RULES)} monitoring rules each platform currently meets (federal law, Ministerial Decision 32/2026, Dubai Guidelines).")
        comp_rate = pd.DataFrame([{"Platform": p, "Rules met": sum(r[2](d) for r in RULES)} for p, d in COMPLIANCE_DATA.items()])
        fig = go.Figure(go.Bar(x=comp_rate["Platform"], y=comp_rate["Rules met"], marker_color=[PCOL[p] for p in comp_rate["Platform"]],
                               text=[f"{v}/{len(RULES)}" for v in comp_rate["Rules met"]], textposition="outside"))
        fig.update_yaxes(range=[0, len(RULES) + 1], title="Rules met"); show(style(fig, 300, False))
    box("<b>Illustrative figures.</b> Historical numbers are mock data. The review-time trend shows what the system "
        "would report; it is not a measured effect of automation.", WARN)

def method_block(title, purpose, steps, formulas=None, table_df=None, limits=None):
    with st.expander(title, expanded=False):
        st.markdown(f"**Purpose.** {purpose}")
        st.markdown("**How it is built**\n" + "\n".join(f"{i + 1}. {x}" for i, x in enumerate(steps)))
        for label, tex in (formulas or []):
            st.markdown(f"*{label}*")
            st.latex(tex)
        if table_df is not None:
            table(table_df)
        if limits:
            st.markdown("**Limitations / what changes in a live system**\n" + "\n".join(f"- {x}" for x in limits))


def page_methodology():
    header("Methodology",
           "How each part of the dashboard is built: the data, the calculations, the legal rules applied and the "
           "assumptions behind the demo.",
           "Transparency is what makes automated recommendations usable by an authority: every number and every "
           "recommendation can be traced back to its data, formula and legal provision.")

    box("<b>Status.</b> Illustrative prototype. The six platforms and all figures are synthetic and generated "
        "deterministically (the same numbers appear every time). The legal rules reflect the UAE framework as of "
        "October 2026. API connections are simulated.", WARN)

    section("1. Data")
    method_block(
        "1.1 Synthetic market data",
        "Provide a realistic but invented food delivery market to demonstrate the calculations.",
        [f"Six invented platforms ({', '.join(NAMES)}), monthly data from {MONTHS[0]} to {MONTHS[-1]} ({T} months).",
         "Each platform's share of orders follows a set path (e.g. Nexa Eats 44% → 47% → 42%; Falcon Feast enters in "
         "March 2024 and reaches 10%), plus small random noise; shares are rescaled to sum to 100% every month.",
         "Total orders start at about 13 million a month, grow 1% a month and have mild seasonality.",
         f"Average order value is AED {AOV:.0f}; GMV = orders × average order value.",
         "Commission rates follow set paths per platform (Saffron Go rises from 19% to 22% in June 2026).",
         "Compliance data (exclusivity, rankings, notice periods, tips, fees, costs, dependence) is a snapshot for the "
         "latest month, set per platform to create a realistic mix of compliant and non-compliant behaviour.",
         "2025 UAE revenue per platform (AED m) is set directly and used for thresholds and fees.",
         "Emirate breakdown: each emirate's share of UAE orders is fixed (Dubai 42%, Abu Dhabi 30%, Sharjah 14%, …); "
         "platform strengths by emirate are set (e.g. Palm Plate stronger in Abu Dhabi, Oasis Delivery in the northern "
         "emirates) and balanced iteratively so that the order-weighted average equals each platform's national share. "
         "Headquarters locations are invented."],
        table_df=pd.DataFrame([{"Platform": p, "2025 revenue (AED m)": c["rev"],
                                "Order share now (%)": round(latest_shares()[p], 1),
                                "Commission now (%)": COMPLIANCE_DATA[p]["comm"]} for p, c in PLATFORMS.items()]),
        limits=["Real data would come from platform reporting and government systems (see 1.2).",
                "Shares would be checked on several bases (orders, GMV, revenue, restaurants) and by emirate."])
    method_block(
        "1.2 Data sources and extraction",
        "Show which authorities and providers supply each input, and how the data reaches the system.",
        ["The authority chooses its sources from a catalogue (individually or with presets per module). The system then "
         "checks whether each module (merger control, monitoring, complaints) has all the sources it needs.",
         "Each source is modelled as an API connection (REST/JSON, OAuth 2.0) with an endpoint, frequency and record count.",
         "‘Extract data’ runs a simulated pipeline on the selected sources only: connect → pull → validate → link records across sources → recalculate "
         "all indicators → refresh merger cases, monitoring rules and complaint routing.",
         "Record linking uses common identifiers (trade licence number, National Economic Register ID) so that the "
         "same firm is recognised across sources."],
        table_df=pd.DataFrame([{"Source": s_["name"], "Provider": s_["who"], "Frequency": s_["freq"], "Used for": s_["why"]}
                               for s_ in SOURCES]),
        limits=["Each data flow needs a legal basis (e.g. Art. 18 information powers) and a data-sharing agreement.",
                "Continuous platform reporting would require a specific regulatory requirement.",
                "Personal data must be handled under Federal Decree-Law No. 45 of 2021."])

    section("2. Market indicators")
    method_block(
        "2.1 Market shares, concentration and margins",
        "Measure how concentrated the market is and how much pricing power each platform has.",
        ["Market share is each platform's share of orders in the latest month.",
         "HHI is the sum of squared shares (0 to 10,000). Above 1,800 is treated as highly concentrated, for reference only.",
         "CR3 is the combined share of the three largest platforms.",
         "The 40% level is used to screen for possible dominance; dominance itself is assessed on the qualitative "
         "criteria of Cabinet Decision No. 59 of 2026.",
         "Revenue per order is compared with average variable cost (AVC) for the predatory-pricing check (Art. 8)."],
        formulas=[("Herfindahl-Hirschman Index", r"HHI=\sum_{i} s_i^{2}\quad(s_i \text{ in } \%)"),
                  ("Concentration ratio", r"CR_3=s_1+s_2+s_3"),
                  ("Platform revenue per order", r"R=\text{commission rate}\times AOV+\text{delivery fee}"),
                  ("Predatory-pricing screen", r"\text{flag if } R < AVC")],
        limits=["Order shares capture the consumer side only; GMV, revenue and restaurant-side shares should be compared.",
                "AVC comes from platform cost data and would need verification."])

    section("3. Merger control")
    method_block(
        "3.1 Workflow and statutory timeline",
        "Follow each notification from filing to the Minister's decision within the legal deadlines.",
        [f"{lab_} ({'automated' if auto else actor})" for lab_, actor, auto in MERGER_STEPS],
        formulas=[("Review deadline (Art. 13)", r"\text{deadline}=\text{date complete}+90\text{ days }(+45\text{ if extended})")],
        limits=["No decision within the deadline means the application is deemed rejected (Art. 13).",
                "The clock pauses when information is requested or a technical opinion is sought (Art. 14)."])
    method_block(
        "3.2 Notifiability and filing fee",
        "Decide automatically whether a transaction must be notified and what fee is due.",
        ["Combined UAE sales of the parties (verified with Federal Tax Authority data) are compared with AED 300m.",
         "Combined market share is compared with 40%. Either threshold triggers notification (Cabinet Resolution No. 3 of 2025).",
         "The fee is 0.02% of aggregate annual turnover, capped at AED 150,000 (Cabinet Resolution No. 105 of 2026)."],
        formulas=[("Notification test", r"\text{notify if } \text{Sales}_{UAE} > 300\text{m AED} \;\text{ or }\; s_A+s_B > 40\%"),
                  ("Filing fee", r"\text{Fee}=\min(0.0002\times\text{Turnover},\;150{,}000\text{ AED})"),
                  ("Change in concentration", r"\Delta HHI = 2\,s_A\,s_B,\qquad HHI_{post}=HHI_{pre}+\Delta HHI")])
    method_block(
        "3.3 Assessment and recommendation",
        "Draft a reasoned recommendation that the case officer can accept or override.",
        ["Market definition follows the July 2026 Guidelines: demand-side substitution and a SSNIP (5–10%) check; "
         "two-sided nature and emirate-level shares are checked.",
         "Market structure: shares, rank of the merged firm, HHI and ΔHHI (for information; UAE law sets no HHI presumption).",
         "Competitive effects: closeness of competition (multi-homing), loss of a maverick, entry evidence, restaurant "
         "dependence (Art. 7), dominance criteria (Art. 6; Cabinet Decision No. 59 of 2026), existing compliance issues.",
         "Third-party observations and claimed economic benefits (merger-specific, verifiable, passed on).",
         "Art. 15 test: approve if the concentration does not adversely affect competition, or if its economic benefits "
         "outweigh the harm; otherwise approve with conditions or reject.",
         "Confidence is High when all factors point the same way and Medium when the result rests on qualitative evidence.",
         "The officer may override only with a written justification, recorded in the audit trail; the Director and the "
         "Minister see both the system's recommendation and the officer's view."],
        limits=["In the demo the report text for the two cases is pre-drafted around the calculated figures; a live "
                "system would assemble it from rule outputs and the officer would edit it."])

    section("4. Market monitoring (ex-ante)")
    method_block(
        "4.1 Compliance rules and recommendations",
        "Check every platform continuously against all active rules and turn breaches into recommended actions.",
        ["Each rule tests one platform data field against a legal threshold (table below).",
         "A breach produces a recommendation with finding, legal basis, priority and proposed action.",
         "Priority: High for breaches of federal competition provisions or by the market leader; Medium for "
         "Dubai Guidelines issues referred to DCCPFT; Low where the evidence is not yet conclusive.",
         "Approving a recommendation executes the action (information request, investigation, market study or referral) "
         "and logs it in the authority statistics."],
        table_df=pd.DataFrame([{"Rule": n, "Legal basis": b} for n, b, _, _ in RULES]),
        limits=["Dubai Guidelines are enforced by DCCPFT; the department detects and refers.",
                "Rule thresholds for self-preferencing (own brands' share of top results more than twice their share of "
                "listings) are an analytical choice, not a legal standard."])

    method_block(
        "4.2 Early-warning signs",
        "Tell the investigator which developing issues need further action, before a formal case exists.",
        ["The system first searches the market-study and case archive for an earlier study of the same market.",
         f"If one exists (here {MARKET_STUDY['id']}, {MARKET_STUDY['completed']}), today's data is compared with the study's "
         "baselines (exclusivity, restaurant dependence, self-preferencing, commission review level, entry) and with its findings.",
         "If none exists, the system relies on general early-warning indicators computed from live data.",
         "General indicators: complaint spikes (last 90 days vs previous 90), complaints reporting coercion or retaliation, "
         "parallel commission increases (≥1 pp by two or more platforms within 6 months), acquisitions of challengers by "
         "the leader, common shareholders between rivals, falling sentiment, below-cost pricing.",
         "Each sign is graded: red = further action needed, amber = watch or request information, green = checked, no concern; "
         "and linked to the recommended action or case it supports."],
        limits=["Thresholds for complaint spikes and parallel increases are analytical choices to trigger review.",
                "A warning sign is not evidence of an infringement; it tells the investigator where to look."])
    method_block(
        "4.3 Guided and fully automated modes",
        "Show the same analysis in two ways, depending on how much the user wants to step through.",
        ["Guided review: results are pre-calculated from the latest scheduled extraction; the user steps through each case or check.",
         "Fully automated: one button extracts the module's sources, recalculates every indicator, applies the legal rules and "
         "generates the reviews or recommendations, which then wait for a human decision.",
         "Both modes use the same data, rules and decision workflow, so the results are identical."])

    section("5. Complaints & sentiment")
    method_block(
        "5.1 Classification, routing and sentiment",
        "Use complaints and reviews as early warnings and send each one to the right authority.",
        ["Complaints and reviews are pulled from MoET consumer protection, DCCPFT and app stores (synthetic in the demo: "
         "daily counts drawn from Poisson distributions; commission complaints triple after June 2026).",
         "Language is detected and personal data removed before analysis.",
         "Complaints are separated by complainant: consumers (service, refunds, fees, mark-ups), restaurants (commissions, "
         "exclusivity, retaliation, self-preferencing, dependence, payments, fees, data) and riders (tips, pay).",
         "Rates are normalised for comparison: consumer complaints per 100,000 orders; restaurant complaints per 1,000 "
         "listed restaurants.",
         "Each item is scored from −1 (very negative) to +1 (very positive) and assigned a topic.",
         "Routing: competition topics (exclusivity, self-preferencing, commission terms, dependence) go to the Competition "
         "Department and are linked to open monitoring recommendations; consumer topics go to consumer protection.",
         "The monthly sentiment index per platform rescales the average score to 0–100; below 50 is the watch level."],
        formulas=[("Sentiment index", r"\text{Index}=\frac{\bar{x}+1}{2}\times 100,\quad \bar{x}\in[-1,1]")],
        table_df=pd.DataFrame([{"Topic": c, "From": w, "Routed to": r} for _, w, c, r, _, _ in COMPLAINT_TEMPLATES]),
        limits=["A live system needs Arabic-dialect text analysis; keyword rules are not enough.",
                "Sentiment is a weak signal of competition problems and is used only to support other evidence."])

    section("6. Authority statistics")
    method_block(
        "6.1 How the statistics are produced",
        "Report workload, speed and outcomes without manual compilation.",
        ["Merger figures combine illustrative history (2023–2026) with decisions taken live in the demo.",
         "Monitoring and enforcement counts increase when recommendations are approved in the demo.",
         "Platform compliance shows how many of the monitoring rules each platform currently meets."],
        limits=["Historical figures are mock data; the review-time trend is not a measured effect of automation."])

    section("7. Legal framework applied")
    table(pd.DataFrame(LEGAL, columns=["Instrument", "Date", "What the system uses"]))

    section("8. Sources for the legal framework")
    st.markdown(
        "- Federal Decree-Law No. 36 of 2023 (UAE Legislation portal)\n"
        "- Ministry of Economy and Tourism, Exemptions page (Ministerial Decisions No. 32 and No. 96 of 2026)\n"
        "- Law-firm summaries of Cabinet Decision No. 59 of 2026, Cabinet Resolutions No. 3 of 2025 and No. 105 of 2026 "
        "(Baker McKenzie, Covington, Gibson Dunn, PwC, Clifford Chance)\n"
        "- GLA & Company summary of the Dubai Guidelines for Online Food Delivery Platforms\n"
        "- Before deployment, all provisions should be checked against the official texts.")


# ============================================================================
# APP
# ============================================================================
def main():
    st.set_page_config(page_title="Competition Department — Automated Operations (prototype)", page_icon="⚖️", layout="wide")
    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700;800&display=swap');
    .stApp {{ font-family:'IBM Plex Sans',Segoe UI,sans-serif; background:{BG}; }}
    section[data-testid="stSidebar"] {{ background:#fff; border-right:1px solid {BORDER}; }}
    </style>""", unsafe_allow_html=True)
    init_state()
    with st.sidebar:
        st.markdown(f"""<div style="border-left:4px solid {PRIMARY};padding-left:.7rem;margin-bottom:.6rem">
            <div style="font-size:.68rem;color:{MUTED};font-weight:700;letter-spacing:.05em">COMPETITION DEPARTMENT</div>
            <div style="font-size:1.08rem;font-weight:800;color:{INK};line-height:1.25">Automated Operations</div>
            <div style="font-size:.74rem;color:{MUTED}">Online food delivery · UAE framework</div></div>""", unsafe_allow_html=True)
        page = st.radio("Navigate", PAGES, label_visibility="collapsed")
        st.divider()
        st.markdown("""<div style="background:#FBF3E3;border:1px solid #EAD9B0;border-radius:8px;padding:.5rem .65rem;
            font-size:.72rem;color:#8a6d3b"><b>Illustrative prototype.</b> Platforms, firms, cases and figures are invented;
            API connections are simulated. Not an official government system.</div>""", unsafe_allow_html=True)
        if st.button("Reset demo", key="reset_all"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        with st.expander("Demo script"):
            st.markdown("1. **Data sources** → quick select *All sources* (or pick some) → *Extract*.\n"
                        "2. **Merger control** → *Fully automated* → *Calculate & generate reviews* → open each case → "
                        "accept → Director → Minister.\n"
                        "3. **Market monitoring** → *Fully automated* → *Calculate & generate* → early-warning signs "
                        "(toggle *no earlier market study* to show the alternative) → approve R1 and R6.\n"
                        "4. **Complaints** → *Fully automated* → *Calculate & generate* → compare *Consumers* and *Restaurants* tabs → *Live processing*.\n"
                        "5. **Authority statistics** → numbers updated.")
    {"Overview": page_overview, "Data sources": page_sources, "Merger control": page_mergers,
     "Market monitoring (ex-ante)": page_monitoring, "Complaints & sentiment": page_complaints,
     "Authority statistics": page_statistics, "Methodology": page_methodology}[page]()


if __name__ == "__main__":
    main()
