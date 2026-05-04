#In questa sezione cash flow, il resolver avrà la logica del file formulas

#MOL
def calc_mol(ric_op_mon, cost_op_mon):
  mol = ric_op_mon - cost_op_mon
  return mol

#RO-L
def calc_rol_from_mol(mol, amortisat):
  rol = mol - amortisat
  return rol

#FCCNOGC: flusso di cassa del capitale circolante netto operativo della gestione caratteristica
def calc_fccnogc_from_revenue(ric_op_mon, cost_op_mon, tax):
  fccnogc_from_revenue = ric_op_mon - cost_op_mon - tax
  return fccnogc_from_revenue

def calc_fccnogc_from_mol(mol, tax):
  fccnogc_from_mol = mol - tax
  return fccnogc_from_mol

def calc_fccnogc_from_rol(rol, tax, amortisat):
  fccnogc_from_rol = rol - tax + amortisat
  return fccnogc_from_rol

#ROS
def calc_ros_from_rol(rol, ric_op_mon):
  ros = rol / ric_op_mon
  return ros
  
#NET FINANCIAL POSITION, CIN & ROI:
def calc_cin(patrimonio_netto, debiti_finanz, liquidity):
  cin = patrimonio_netto + debiti_finanz - liquidity
  return cin

def calc_roi_from_rol(rol, cin):
  roi = rol / cin
  return roi

#ROE
def calc_net_profit(rol, oneri_finanz, tax):
  utile_netto = rol - oneri_finanz - tax
  return utile_netto

def calc_roe(utile_netto, patrimonio_netto):
  roe = utile_netto / patrimonio_netto
  return roe

#FCGC: flusso di cassa della gestione caratteristica
def calc_var_ccno(ccno1, ccno2):
  var_ccno = ccno2 - ccno1
  return var_ccno
  
def calc_fcgc(fccnogc, var_ccno):
  fcgc = fccnogc - var_ccno
  return fcgc

#FCID: flusso di cassa area investimenti e disinvestimenti
def calc_inv(acquisition_1, acquisition_2):
  inv = acquisition_2 - acquisition_1
  return inv

def calc_vnc(valore_stor, ammo_ti, n_ammo_ti):
  vnc = valore_stor - (ammo_ti * n_ammo_ti)
  return vnc

def calc_dis_from_vnc(vnc, plus, minus):
  dis_from_vnc = vnc + plus - minus
  return dis_from_vnc

def calc_fcid_from_inv_dis(inv, dis):
  fcid_from_inv_dis = dis - inv
  return fcid_from_inv_dis

#FCFR: flusso di cassa finanziamenti e rimborsi
def calc_fcfr(patrimonio_netto, debiti_finanz, quota_rimbors_capital):
  fcfr = patrimonio_netto + debiti_finanz - quota_rimbors_capital
  return fcfr

#FCRf: flusso di cassa remunerazione finanziaria
def calc_fcrf(oneri_finanziari, dividendi):
  fcrf = - oneri_finanziari - dividendi
  return fcrf
  
#Variazione di liquidità
def calc_var_liquidity(fcgc, fcid, fcfr, fcrf):
  var_liquidity = fcgc + fcid + fcfr + fcrf
  return var_liquidity

#FCU: flussi di cassa Unlevered
def calc_fcu(fcgc, fcid):
  fcu = fcgc + fcid
  return fcu

#FCE: flussi di cassa Equity
def calc_fce(fcu, fcfr, quota_rimbors_capital, fcrf, dividendi):
  fce = fcu + fcfr - quota_rimbors_capital + fcrf - dividendi
  return fce

#NPV con flussi di cassa variabili e costi fissi sui flussi per periodo, multiperiodo.

#tasso equivalente 

def calc_r_monthly_equivalent(r_annual):
  r_monthly = (1 + r_annual) ** (1/12) - 1
  return r_monthly

# Progettare il resolver che trasforma FCU/FCE in FC[t] coerente con WACC/Ke senza ambiguità (già scritto nel financial schema)

def calc_fc_net(fc, cost):
  fc_net = fc - cost
  return fc_net
  
#time value, discount factor  
def calc_df_constant(k, t):
  df = (1 + k) ** t
  return df

def calc_df_variable(k_t, t):
  df = (1 + k_t) ** t
  return df

def calc_pv(fc_net, df):
  pv = fc_net / df
  return pv

#pv_list è prodotto del resolver non del DAG
def calc_total_pv(pv_list):
  total_pv = sum(pv_list)
  return total_pv

def calc_npv(total_pv, i_0):
  npv = total_pv - i_0
  return npv


#BOND ZERO COUPON VA
def calc_bond_zero_discount_factor(k, t):
  df = (1 + k) ** t
  return df

def calc_bond_zero_va(vn, df):
  va = vn / df
  return va

#BOND ZERO COUPON YIELD TO MATURITY
def calc_bond_zero_mont(vn, va):
  mont = vn / va
  return mont

def calc_bond_zero_factor(t):
  factor = (1/t)
  return factor

def calc_bond_zero_yield_to_maturity(mont, factor):
  bond_zero_yield_to_maturity = mont ** factor - 1
  return bond_zero_yield_to_maturity

#BOND CEDOLARE VA

def calc_cedola(vn_ced, k_ced):
  cedola = vn_ced * k_ced
  return cedola

def calc_n_periods(t_ced):
  n = int(t_ced)
  return n

def calc_fractional_period(t_ced, n):
  f = t_ced - n
  return f

def calc_df(k_merk, t):
  df = (1 + k_merk) ** t
  return df
#inserire il loop nel resolver Σ [ced / (1+k)^t]
#è il resolver che fa pv_bond_list -> sum
def calc_pv_bond_va(ced, df):
  pv_bond_va = ced / df
  return pv_bond_va
def calc_pv_bond_va_fractional(ced, f, df):
  pv_bond_va_fractional = ced * f /df
  return pv_bond_va_fractional

def calc_pv_bond_principal(vn_ced, df):
  pv_bond_principal = vn_ced / df
  return pv_bond_principal

def calc_pv_bond_total(pv_bond_sum, pv_bond_va_fractional, 
                       pv_bond_principal):
  va_bond_total = pv_bond_sum + pv_bond_va_fractional + pv_bond_principal
  return va_bond_total

#BOND CEDOLARE YIELD TO MATURITY
#richiama def calc_cedola(vn_ced, k_ced) sul resolver

def calc_bond_mont(cedola, k_mark):
  bond_mont = cedola / k_mark
  return bond_mont

def calc_bond_factor(k_mark, t):
  bond_factor = 1 - (1 / ((1 + k_mark) ** t))
  return bond_factor

def calc_bond_va_principal(vn, k_mark, t):
  bond_va_principal = vn / ((1 + k_mark) ** t)
  return bond_va_principal

def calc_bond_price(bond_mont, bond_factor, bond_va_principal):
  bond_price = bond_mont * bond_factor + bond_va_principal
  return bond_price  # è il resolver a calcolare YTM

#no grow STOCK price
def calc_stock_price_no_growth(dividend, k):
  stock_price_no_grow = dividend / k
  return stock_price_no_grow

#return
def calc_required_return(dividend_1, price, g):
  required_return = (dividend_1 / price) + g
  return required_return

#earnings -> dividend
def calc_earnings_t1(earnings_t0, g):
  earnings_t1 = earnings_t0 * (1 + g)
  return earnings_t1

def calc_dividend_t1(earnings_t1, payout_ratio):
  dividend_t1 = earnings_t1 * payout_ratio
  return dividend_t1

#Gordon Price
def calc_stock_price_gordon(dividend_1, k, g):
  stock_price_grow = dividend_1 / (k - g)
  return stock_price_grow

#G ratio calculation
def calc_g(retention_ratio, roe):
  g = retention_ratio * roe
  return g

#VAOC
def calc_vaoc(stock_price_grow, stock_price_no_grow):
  vaoc = stock_price_grow - stock_price_no_grow
  return vaoc

#Mortgage Italiano: quota capitale costante

def calc_capital_share(mortgage, years):
  capital_share = mortgage / years
  return capital_share

def calc_interest_t(debt, n, t, k):
  interest_t = (debt * (1 - (t - 1) / n)) * k
  return interest_t

def calc_residual_debt(mortgage, n, t):
  residual_debt = mortgage * (1 - t / n)
  return residual_debt

def calc_paid_off_debt(mortgage, n, t):
  paid_off_debt = mortgage - (t * (mortgage / n))
  return paid_off_debt

def calc_mortgage_payment(capital_share, interests_share):
  mortgage_payment = capital_share + interests_share

#Mortgage Francese: rata costante

def calc_mortgage_payment_fr(debt, k, n):
  mortgage_payment = debt * (k * (1 + k) ** n) / ((1 + k) ** n - 1)
  return mortgage_payment

def calc_residual_debt_fr(debt, k, n, t):
  residual_debt = debt * ((1 + k) ** n - (1 + k) ** t) / ((1 + k) ** n - 1)
  return residual_debt

def calc_interest_fr_closed(debt, k, n, t):
  residual_prev = debt * ((1 + k) ** n - (1 + k) ** (t - 1)) / ((1 + k) ** n - 1)
  interest = residual_prev * k
  return interest

def calc_capital_share_fr(mortgage_payment, interest):
  capital_share = mortgage_payment - interest
  return capital_share

def calc_paid_off_debt_fr(debt, residual_debt):
  paid_off_debt = debt - residual_debt
  return paid_off_debt

#WACC
def calc_wacc(re, rd, tc, equity, debt):
  w = equity + debt
  wacc = re * (equity / w) + rd * (1 - tc) * (debt / w)
  return wacc

#VAN logica del capitale investito(fcu)
def calc_fc_net_fcu(fcu, cost):
  fc_net_fcu = fcu - cost
  return fc_net_fcu
#discount factor
def calc_df_wacc_fcu(wacc, t):
  df_wacc = (1 + wacc) ** t
  return df_wacc
#pv fcu
def calc_pv_fcu(fc_net_fcu, df_wacc):
  pv_fcu = fc_net_fcu / df_wacc
  return pv_fcu
def calc_total_pv_fcu(pv_list_fcu):
  total_pv_fcu = sum(pv_list_fcu)
  return total_pv_fcu

def calc_npv_fcu(total_pv_fcu, i0_fcu):
  npv_fcu= total_pv_fcu - i0_fcu
  return npv_fcu

#VAN logica dell'azionista(fce)
def calc_fc_net_fce(fce, cost):
  fc_net_fce = fce - cost
  return fc_net_fce

def calc_df_ke_fce(ke, t):
  df_ke = (1 + ke) ** t
  return df_ke

def calc_pv_fce(fc_net_fce, df_ke):
  pv_fce = fc_net_fce / df_ke
  return pv_fce

def calc_total_pv_fce(pv_list_fce):
  total_pv_fce = sum(pv_list_fce)
  return total_pv_fce

def calc_npv_fce(total_pv_fce, equity0):
  npv_fce = total_pv_fce - equity0
  return npv_fce
