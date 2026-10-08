import { useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { useRequest, Field, Status, Stat } from "../ui.jsx";
import { pct, num } from "../api.js";

const C = { ink: "#12202F", teal: "#0A6B5B", amber: "#B7791F", grey: "#B9C2CB", red: "#B42318" };

function Weights({ title, p }) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      <div className="stats">
        <Stat label="Return" value={pct(p.return)} />
        <Stat label="Volatility" value={pct(p.vol)} />
        <Stat label="Sharpe" value={num(p.sharpe)} />
      </div>
      <table>
        <tbody>
          {Object.entries(p.weights)
            .sort((a, b) => b[1] - a[1])
            .map(([t, w]) => (
              <tr key={t}>
                <td>{t}</td>
                <td className="r">{pct(w)}</td>
                <td className="bar"><i style={{ width: `${w * 100}%` }} /></td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

function Correlation({ c }) {
  const shade = (v) => (v >= 0 ? `rgba(10,107,91,${Math.abs(v) * 0.55})` : `rgba(180,35,24,${Math.abs(v) * 0.55})`);
  return (
    <div className="scroll">
      <table className="corr">
        <thead>
          <tr><th />{c.labels.map((l) => <th key={l}>{l}</th>)}</tr>
        </thead>
        <tbody>
          {c.matrix.map((row, i) => (
            <tr key={c.labels[i]}>
              <th>{c.labels[i]}</th>
              {row.map((v, j) => <td key={j} style={{ background: shade(v) }}>{v.toFixed(2)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Portfolio() {
  const [tickers, setTickers] = useState("AAPL, MSFT, JPM, GS, XOM, JNJ");
  const [years, setYears] = useState(3);
  const [rf, setRf] = useState(0.03);
  const [{ data, error, loading }, run] = useRequest();

  const submit = (e) => {
    e.preventDefault();
    run("/portfolio", { tickers, years, rf });
  };
  const pctTick = (v) => (v * 100).toFixed(0) + "%";

  return (
    <div className="tool">
      <form className="inputs" onSubmit={submit}>
        <h2>Portfolio optimisation</h2>
        <p className="lede">Find the long-only portfolios with the best risk-return trade-off for a set of stocks.</p>
        <Field label="Tickers" hint="2 to 10, comma-separated, Yahoo Finance symbols">
          <input value={tickers} onChange={(e) => setTickers(e.target.value)} />
        </Field>
        <Field label="History (years)">
          <input type="number" min="1" max="10" value={years} onChange={(e) => setYears(e.target.value)} />
        </Field>
        <Field label="Risk-free rate" hint="Annual, as a decimal (0.03 = 3%)">
          <input type="number" step="0.005" min="0" max="0.2" value={rf} onChange={(e) => setRf(e.target.value)} />
        </Field>
        <button className="primary" disabled={loading}>Run analysis</button>
        <Status loading={loading} error={error} />
      </form>

      <div className="results">
        {!data && !loading && !error && <p className="empty">Choose your tickers and run the analysis to see the efficient frontier.</p>}
        {data && (
          <>
            <p className="meta">Data from {data.period.start} to {data.period.end}. Returns and volatility are annualised.</p>
            <div className="chart">
              <ResponsiveContainer width="100%" height={360}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 24, left: 4 }}>
                  <CartesianGrid stroke="#E4E9ED" />
                  <XAxis type="number" dataKey="vol" name="Volatility" tickFormatter={pctTick} domain={["auto", "auto"]}
                    label={{ value: "Volatility", position: "insideBottom", offset: -12, fill: "#5B6B7A" }} />
                  <YAxis type="number" dataKey="return" name="Return" tickFormatter={pctTick} domain={["auto", "auto"]}
                    label={{ value: "Return", angle: -90, position: "insideLeft", fill: "#5B6B7A" }} />
                  <Tooltip formatter={(v) => pct(v)} cursor={{ strokeDasharray: "3 3" }} />
                  <Legend verticalAlign="top" height={30} />
                  <Scatter name="Random portfolios" data={data.cloud} fill={C.grey} fillOpacity={0.55} shape="circle" legendType="circle" />
                  <Scatter name="Efficient frontier" data={data.frontier} line={{ stroke: C.teal, strokeWidth: 2.5 }} fill={C.teal} shape={() => null} legendType="line" />
                  <Scatter name="Individual stocks" data={data.assets} fill={C.ink} shape="diamond" />
                  <Scatter name="Max Sharpe" data={[data.max_sharpe]} fill={C.amber} shape="star" legendType="star" />
                  <Scatter name="Min volatility" data={[data.min_vol]} fill={C.red} shape="triangle" legendType="triangle" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <div className="grid2">
              <Weights title="Maximum Sharpe" p={data.max_sharpe} />
              <Weights title="Minimum volatility" p={data.min_vol} />
            </div>
            <h3>Individual stocks</h3>
            <div className="scroll">
              <table className="data">
                <thead><tr><th>Ticker</th><th className="r">Return</th><th className="r">Volatility</th><th className="r">Sharpe</th><th className="r">Max drawdown</th></tr></thead>
                <tbody>
                  {data.assets.map((a) => (
                    <tr key={a.ticker}>
                      <td>{a.ticker}</td><td className="r">{pct(a.return)}</td><td className="r">{pct(a.vol)}</td>
                      <td className="r">{num(a.sharpe)}</td><td className="r neg">{pct(a.max_drawdown)}</td>
                    </tr>
                  ))}
                  <tr className="sum">
                    <td>Equal weight</td><td className="r">{pct(data.equal_weight.return)}</td><td className="r">{pct(data.equal_weight.vol)}</td>
                    <td className="r">{num(data.equal_weight.sharpe)}</td><td />
                  </tr>
                </tbody>
              </table>
            </div>
            <h3>Correlation</h3>
            <Correlation c={data.correlation} />
          </>
        )}
      </div>
    </div>
  );
}
