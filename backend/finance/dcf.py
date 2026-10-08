"""Discounted cash flow valuation with sensitivity analysis."""


def dcf_value(fcf0, growth, terminal_growth, wacc, years, net_debt, shares) -> dict:
    if wacc <= terminal_growth:
        raise ValueError("WACC must be greater than terminal growth.")
    if years < 1:
        raise ValueError("Projection horizon must be at least 1 year.")
    if shares <= 0:
        raise ValueError("Share count must be positive.")

    rows, pv_sum = [], 0.0
    for t in range(1, years + 1):
        fcf = fcf0 * (1 + growth) ** t
        pv = fcf / (1 + wacc) ** t
        pv_sum += pv
        rows.append({"year": t, "fcf": fcf, "pv": pv})

    terminal_value = rows[-1]["fcf"] * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_terminal = terminal_value / (1 + wacc) ** years
    enterprise_value = pv_sum + pv_terminal
    equity_value = enterprise_value - net_debt
    return {
        "projection": rows,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "pv_explicit": pv_sum,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "value_per_share": equity_value / shares,
        "terminal_share_of_ev": pv_terminal / enterprise_value,
    }


def sensitivity(fcf0, growth, terminal_growth, wacc, years, net_debt, shares,
                wacc_step=0.005, g_step=0.005, size=2) -> dict:
    waccs = [wacc + wacc_step * k for k in range(-size, size + 1)]
    gs = [terminal_growth + g_step * k for k in range(-size, size + 1)]
    grid = []
    for w in waccs:
        row = []
        for g in gs:
            try:
                row.append(dcf_value(fcf0, growth, g, w, years, net_debt, shares)["value_per_share"])
            except ValueError:
                row.append(None)
        grid.append(row)
    return {"wacc": waccs, "terminal_growth": gs, "values": grid}
