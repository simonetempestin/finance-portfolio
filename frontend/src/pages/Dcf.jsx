import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import { useRequest, Field, Status, Stat } from "../ui.jsx";
import { pct, num, big } from "../api.js";

export default function Dcf() {
  const [f, setF] = useState({ ticker: "MSFT", growth: 0.08, wacc: 0.09, terminal_growth: 0.025, years: 5 });
  const [{ data, error, loading }, run] = useRequest();
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    const { ticker, ...rest } = f;
    run(`/dcf/${encodeURIComponent(ticker.trim())}`, rest);
  };

  const cur = data?.company.currency || "";
  const cell = (v, base, key) => {
    if (v == null) return <td key={key} className="r muted">n/a</td>;
    const cls = data.company.price ? (v >= data.company.price ? "pos" : "neg") : "";
    return <td key={key} className={"r " + cls + (base ? " base" : "")}>{num(v)}</td>;
  };

  return (
    <div className="tool">
      <form className="inputs" onSubmit={submit}>
        <h2>DCF valuation</h2>
        <p className="lede">Estimate intrinsic value per share from the latest reported free cash flow.</p>
        <Field label="Ticker"><input value={f.ticker} onChange={set("ticker")} /></Field>
        <Field label="FCF growth, explicit period" hint="Annual, decimal">
          <input type="number" step="0.01" value={f.growth} onChange={set("growth")} />
        </Field>
        <Field label="WACC" hint="Discount rate, decimal">
          <input type="number" step="0.005" value={f.wacc} onChange={set("wacc")} />
        </Field>
        <Field label="Terminal growth" hint="Must be below WACC">
          <input type="number" step="0.005" value={f.terminal_growth} onChange={set("terminal_growth")} />
        </Field>
        <Field label="Projection years">
          <input type="number" min="1" max="15" value={f.years} onChange={set("years")} />
        </Field>
        <button className="primary" disabled={loading}>Value the company</button>
        <Status loading={loading} error={error} />
      </form>

      <div className="results">
        {!data && !loading && !error && <p className="empty">Enter a ticker and your assumptions to build the valuation.</p>}
        {data && (
          <>
            <h3 className="company">{data.company.name} ({data.company.ticker})</h3>
            <div className="stats">
              <Stat label="Intrinsic value / share" value={`${num(data.value_per_share)} ${cur}`} />
              <Stat label="Market price" value={data.company.price ? `${num(data.company.price)} ${cur}` : "n/a"} />
              <Stat label="Upside" value={pct(data.upside)} tone={data.upside >= 0 ? "pos" : "neg"} />
            </div>
            <div className="stats">
              <Stat label="Enterprise value" value={big(data.enterprise_value)} />
              <Stat label="Net debt" value={big(data.inputs.net_debt)} />
              <Stat label="Equity value" value={big(data.equity_value)} />
              <Stat label="Terminal value share of EV" value={pct(data.terminal_share_of_ev, 0)} />
            </div>
            <h3>Projected free cash flow</h3>
            <div className="chart">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={data.projection} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
                  <CartesianGrid stroke="#E4E9ED" vertical={false} />
                  <XAxis dataKey="year" tickFormatter={(y) => `Y${y}`} />
                  <YAxis tickFormatter={big} width={64} />
                  <Tooltip formatter={(v) => big(v)} labelFormatter={(y) => `Year ${y}`} />
                  <Bar dataKey="fcf" name="Free cash flow" fill="#B9C2CB" />
                  <Bar dataKey="pv" name="Present value" fill="#0A6B5B" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <h3>Value per share: WACC vs terminal growth</h3>
            <p className="meta">Green cells are above the current price, red below.</p>
            <div className="scroll">
              <table className="data sens">
                <thead>
                  <tr><th>WACC \ g</th>{data.sensitivity.terminal_growth.map((g) => <th key={g} className="r">{pct(g)}</th>)}</tr>
                </thead>
                <tbody>
                  {data.sensitivity.values.map((row, i) => (
                    <tr key={i}>
                      <th>{pct(data.sensitivity.wacc[i])}</th>
                      {row.map((v, j) => cell(v, i === 2 && j === 2, j))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="note">Base-year FCF: {big(data.inputs.fcf0)} {cur}. FCF is operating cash flow minus capital expenditure as reported by Yahoo Finance.</p>
          </>
        )}
      </div>
    </div>
  );
}
