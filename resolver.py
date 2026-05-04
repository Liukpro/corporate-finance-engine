def resolve_inputs(raw):
    """
    Trasforma output Yahoo in input pulito per il DAG.
    - converte None in errori controllati
    - separa dati obbligatori vs opzionali
    """

    def req(key):
        val = raw.get(key)
        if val is None:
            raise ValueError(f"[RESOLVER ERROR] Missing required field: {key}")
        return val

    def opt(key, default=0.0):
        val = raw.get(key)
        if val is None:
            return default
        return val
    return {
        # FCCNOGC
        "ric_op_mon": req["ric_op_mon"],
        "cost_op_mon": req["cost_op_mon"],
        "ammort": req["ammort"],
        "tax": opt["imp"],

        #FCFR
        "patrimonio_netto": req["pat_net"],
        "debiti_finanz": req["deb_f"],
        "quota_rimbors_capital": opt("rimb_cap", 0),

        #CCNO PER VARIAZIONE
        "ccno1": opt("ccno", 0),  # se non hai serie storica
        "ccno2": opt("ccno", 0),

        #FCRf
        "dividendi": opt("div", 0)
        "oneri_finanz": opt["of"],

        #EXTRA
        "liquidity": req["liq"],
    }# da completare I cash flow con FCGC FCID, FCU, FCE, VARIAZIONE LIQUIDITà
