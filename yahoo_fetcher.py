# ============================================================
# YAHOO FINANCE MAPPING → CHIAVI CALCOLATORE
# Fonte: yahooquery, colonne verificate su RACE (Ferrari N.V.)
# ============================================================

from yahooquery import Ticker
import pandas as pd


# ── MAPPING DIRETTO ──────────────────────────────────────────
# Chiavi che esistono come colonna singola in Yahoo Finance

YAHOO_DIRECT = {

    # INCOME STATEMENT
    "ric_op_mon":   "TotalRevenue",           # o "OperatingRevenue" se TotalRevenue è assente
    "rol":          "EBIT",                   # Operating profit
    "of":           "InterestExpense",        # Oneri finanziari lordi
    "imp":          "TaxProvision",           # Income tax expense
    "ut_net":       "NetIncome",              # Net profit

    # BALANCE SHEET
    "pat_net":      "CommonStockEquity",      # Equity (esclude minority interest)
    "deb_f":        "TotalDebt",              # Long-term + short-term debt
    "liq":          "CashAndCashEquivalents", # Liquidità

    # CASH FLOW
    "ammort":       "DepreciationAndAmortization",
    "ccno":         "ChangeInWorkingCapital",
    "div":          "CashDividendsPaid",      # negativo in Yahoo → prendere abs()
    "rimb_cap":     "LongTermDebtPayments",   # negativo in Yahoo → prendere abs()
    "fcid":         "InvestingCashFlow",      # totale investing activities
}

# ── MAPPING AGGREGATO ────────────────────────────────────────
# Chiavi che vanno calcolate combinando più colonne Yahoo
# Formato: lista di (colonna, segno)  +1 somma, -1 sottrae

YAHOO_AGGREGATED = {

    # cost_op_mon: Yahoo ha CostOfRevenue ma non include SG&A.
    # Per avere i costi operativi totali sommare le componenti.
    "cost_op_mon": [
        ("CostOfRevenue",                   +1),
        ("SellingGeneralAndAdministration", +1),
        ("ResearchAndDevelopment",          +1),
    ],

    # inv: Yahoo separa acquisti di PPE e intangibili
    "inv": [
        ("PurchaseOfPPE",        +1),   # negativo in Yahoo
        ("PurchaseOfIntangibles",+1),   # negativo in Yahoo
    ],

    # dis: proventi da vendita asset
    "dis": [
        ("SaleOfPPE",            +1),
    ],

    # delta_inventories, receivables, payables: scomposte
    "delta_inventories": [("ChangeInInventory",    +1)],
    "delta_receivables":  [("ChangeInReceivables",  +1)],
    "delta_payables":     [("ChangeInPayable",      +1)],
}

# ── STATEMENT DI APPARTENENZA ────────────────────────────────
# Dice al fetcher in quale DataFrame cercare ogni colonna

YAHOO_STATEMENT = {
    "ric_op_mon":        "income_statement",
    "cost_op_mon":       "income_statement",
    "rol":               "income_statement",
    "of":                "income_statement",
    "imp":               "income_statement",
    "ut_net":            "income_statement",
    "pat_net":           "balance_sheet",
    "deb_f":             "balance_sheet",
    "liq":               "balance_sheet",
    "ammort":            "cash_flow",
    "ccno":              "cash_flow",
    "div":               "cash_flow",
    "rimb_cap":          "cash_flow",
    "fcid":              "cash_flow",
    "inv":               "cash_flow",
    "dis":               "cash_flow",
    "delta_inventories": "cash_flow",
    "delta_receivables": "cash_flow",
    "delta_payables":    "cash_flow",
}

# Colonne il cui valore in Yahoo è negativo per convenzione
# → il fetcher applica abs() automaticamente
YAHOO_NEGATIVE_CONVENTIONS = [
    "div",
    "rimb_cap",
    "inv",          # PurchaseOfPPE e PurchaseOfIntangibles sono negative
]

def _get_latest(df, year=None):
    if df is None or df.empty:
        return None

    df = df.copy()

    if "asOfDate" in df.columns:
        df = df.sort_values("asOfDate")

    if year:
        df = df[df["asOfDate"].dt.year == year]

    return df.iloc[-1] if not df.empty else None



# ── MAIN FETCHER ──────────────────────────────────────────────────

def fetch_financials(ticker_symbol: str, year: int = None) -> dict:

    stock = Ticker(ticker_symbol)

    # ❗ FIX: rimosso trailing=False (causa errore nella tua versione)
    df_is = stock.income_statement(frequency="a")
    df_bs = stock.balance_sheet(frequency="a")
    df_cf = stock.cash_flow(frequency="a")

    statements = {
        "income_statement": _get_latest(df_is, year),
        "balance_sheet": _get_latest(df_bs, year),
        "cash_flow": _get_latest(df_cf, year),
    }

    result = {}
    missing = []

    all_keys = set(YAHOO_DIRECT) | set(YAHOO_AGGREGATED)

    for key in all_keys:

        stmt = YAHOO_STATEMENT.get(key)
        row = statements.get(stmt)

        if row is None:
            result[key] = None
            missing.append(key)
            continue

        # ── DIRECT ──
        if key in YAHOO_DIRECT:

            col = YAHOO_DIRECT[key]

            if col not in row.index or pd.isna(row[col]):
                result[key] = None
                missing.append(key)
                continue

            val = float(row[col])

            if key in YAHOO_NEGATIVE:
                val = abs(val)

            result[key] = val

        # ── AGGREGATED ──
        else:
            total = 0.0
            ok = True

            for col, sign in YAHOO_AGGREGATED[key]:
                if col not in row.index or pd.isna(row[col]):
                    ok = False
                    break
                total += sign * float(row[col])

            result[key] = total if ok else None

            if not ok:
                missing.append(key)

    # ── CIN derivato ──
    if all(result.get(k) is not None for k in ["pat_net", "deb_f", "liq"]):
        result["cin"] = result["pat_net"] + result["deb_f"] - result["liq"]

    result["_missing"] = missing
    result["_ticker"] = ticker_symbol
    result["_year"] = year

    return result
    """
    Scarica i dati finanziari da Yahoo Finance e li restituisce
    come dizionario {chiave_calcolatore: valore} pronto per
    essere passato alle funzioni di formulas.py.

    Args:
        ticker_symbol: es. "RACE", "STLAM.MI", "BC.MI"
        year:          anno fiscale desiderato (es. 2023).
                       Se None, usa il più recente disponibile.

    Returns:
        {
            "ric_op_mon": 5970146000.0,
            "rol": 1617369000.0,
            ...
            "_missing":    ["cost_op_mon"],
            "_errors":     []
        }
    """
