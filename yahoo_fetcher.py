# ============================================================
# YAHOO FINANCE MAPPING → CHIAVI CALCOLATORE
# Fonte: yahooquery, colonne verificate su RACE (Ferrari N.V.)
# ============================================================
# Struttura:
#   "chiave_calcolatore": "NomeColonnaYahoo"
# Per le chiavi aggregate: lista di (colonna, segno)
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


# ── FETCHER ──────────────────────────────────────────────────

def fetch_financials(ticker_symbol: str, year: int = None) -> dict:
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
    stock = Ticker(ticker_symbol)

    # Scarica i tre statement annuali
    try:
        df_is = stock.income_statement(frequency="a", trailing=False)
        df_bs = stock.balance_sheet(frequency="a", trailing=False)
        df_cf = stock.cash_flow(frequency="a", trailing=False)
    except Exception as e:
        return {"_errors": [f"Errore download Yahoo Finance: {e}"]}

    statements = {
        "income_statement": df_is,
        "balance_sheet":    df_bs,
        "cash_flow":        df_cf,
    }

    # Filtra per anno se specificato, altrimenti usa il più recente
    def get_row(df: pd.DataFrame) -> pd.Series | None:
        if df is None or df.empty:
            return None
        df = df[df["periodType"] == "12M"].copy()
        if year:
            df = df[df["asOfDate"].dt.year == year]
        if df.empty:
            return None
        return df.sort_values("asOfDate").iloc[-1]

    rows = {k: get_row(v) for k, v in statements.items()}

    # ── Estrazione ───────────────────────────────────────────
    result  = {}
    missing = []
    errors  = []

    all_keys = set(YAHOO_DIRECT.keys()) | set(YAHOO_AGGREGATED.keys())

    for key in all_keys:
        statement = YAHOO_STATEMENT.get(key)
        row = rows.get(statement)

        if row is None:
            missing.append(key)
            result[key] = None
            continue

        # Chiave diretta
        if key in YAHOO_DIRECT:
            col = YAHOO_DIRECT[key]
            # Fallback per ric_op_mon
            if key == "ric_op_mon" and col not in row.index:
                col = "OperatingRevenue"
            if col in row.index and pd.notna(row[col]):
                value = float(row[col])
                if key in YAHOO_NEGATIVE_CONVENTIONS:
                    value = abs(value)
                result[key] = value
            else:
                missing.append(key)
                result[key] = None

        # Chiave aggregata
        elif key in YAHOO_AGGREGATED:
            total = 0.0
            all_found = True
            for col, sign in YAHOO_AGGREGATED[key]:
                if col in row.index and pd.notna(row[col]):
                    total += sign * float(row[col])
                else:
                    all_found = False
                    break
            if all_found:
                if key in YAHOO_NEGATIVE_CONVENTIONS:
                    total = abs(total)
                result[key] = total
            else:
                missing.append(key)
                result[key] = None

    # CIN calcolato se i tre componenti sono presenti
    if all(result.get(k) is not None for k in ["pat_net", "deb_f", "liq"]):
        result["cin"] = result["pat_net"] + result["deb_f"] - result["liq"]

    result["_missing"] = missing
    result["_errors"]  = errors
    result["_ticker"]  = ticker_symbol
    result["_year"]    = year

    return result


def fetch_report(result: dict) -> None:
    """Stampa un report leggibile del risultato."""
    print(f"\n{'='*55}")
    print(f"  {result.get('_ticker', '?')} — anno {result.get('_year', 'più recente')}")
    print(f"{'='*55}")

    keys = [k for k in result if not k.startswith("_")]
    found   = [k for k in keys if result[k] is not None]
    missing = result.get("_missing", [])

    print(f"\n  Trovate:  {len(found)}/{len(keys)} chiavi")
    print(f"  Mancanti: {len(missing)}")

    print("\n── Valori ──")
    for k in sorted(found):
        print(f"  {k:25s}: {result[k]:>20,.0f}")

    if missing:
        print("\n── Non trovate ──")
        for k in missing:
            print(f"  {k}")

    if result.get("_errors"):
        print("\n── Errori ──")
        for e in result["_errors"]:
            print(f"  {e}")


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    result = fetch_financials("RACE", year=2023)
    fetch_report(result)
