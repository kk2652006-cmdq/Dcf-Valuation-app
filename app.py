import streamlit as st
import yfinance as yf

def run_dcf(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    revenue = info.get('totalRevenue', 0)
    ebitda = info.get('ebitda', 0)
    current_price = info.get('currentPrice', 0)
    shares = info.get('sharesOutstanding', 1)
    total_debt = info.get('totalDebt', 0)
    cash = info.get('totalCash', 0)

    if revenue == 0 or ebitda == 0 or shares == 0:
        return None

    rev_growth = 0.05
    ebitda_margin = ebitda / revenue
    tax_rate = 0.21
    da_pct = 0.03
    capex_pct = 0.04
    nwc_pct = 0.01
    wacc = 0.08
    terminal_growth = 0.03
    years = 5

    fcfs = []
    rev = revenue
    for i in range(years):
        rev = rev * (1 + rev_growth)
        ebit = rev * ebitda_margin
        nopat = ebit * (1 - tax_rate)
        da = rev * da_pct
        capex = rev * capex_pct
        nwc = rev * nwc_pct
        fcf = nopat + da - capex - nwc
        fcfs.append(fcf)

    pv_fcfs = [fcf / (1 + wacc) ** (i + 1) for i, fcf in enumerate(fcfs)]
    tv = fcfs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_tv = tv / (1 + wacc) ** years

    ev = sum(pv_fcfs) + pv_tv
    net_debt = total_debt - cash
    equity_value = ev - net_debt
    value_per_share = equity_value / shares
    upside = (value_per_share / current_price - 1) * 100 if current_price else 0

    return {
        'company': info.get('longName', ticker),
        'current_price': round(current_price, 2),
        'value_per_share': round(value_per_share, 2),
        'upside': round(upside, 1),
        'enterprise_value': round(ev / 1e9, 2),
        'equity_value': round(equity_value / 1e9, 2),
    }


st.set_page_config(page_title="DCF Valuator", page_icon="📊", layout="wide")
st.title("📊 DCF Valuation App")
st.write("Enter any stock ticker to get an instant DCF valuation.")

ticker = st.text_input("Stock Ticker", value="KO",
                        help="Examples: KO, AAPL, MSFT, ASIANPAINT.NS")

if st.button("Run DCF Valuation", type="primary"):
    with st.spinner("Pulling data and running DCF..."):
        result = run_dcf(ticker)

    if result is None:
        st.error("Could not fetch data. Check the ticker.")
    else:
        st.success(f"✅ DCF complete for {result['company']}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${result['current_price']}")
        col2.metric("DCF Value", f"${result['value_per_share']}",
                    f"{result['upside']}%")
        col3.metric("Enterprise Value", f"${result['enterprise_value']}B")

        if result['upside'] > 15:
            st.success(f"🟢 **BUY** — {result['upside']}% upside")
        elif result['upside'] > 0:
            st.info(f"🟡 **HOLD** — {result['upside']}% upside")
        else:
            st.warning(f"🔴 **SELL** — {result['upside']}% downside")

        with st.expander("See assumptions"):
            st.write("WACC: 8.0%")
            st.write("Terminal Growth: 3.0%")
            st.write(f"Equity Value: ${result['equity_value']}B")
