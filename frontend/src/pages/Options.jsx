import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend, ReferenceLine } from "recharts";
import { useRequest, Field, Status, Stat } from "../ui.jsx";
import { num } from "../api.js";

export default function Options() {
  const [f, setF] = useState({ spot: 100, strike: 100, maturity: 1, rate: 0.03, vol: 0.2, dividend: 0, kind: "call" });
  const [{ data, error, loading }, run] = useRequest();
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    run("/options", f);
  };

  return (
    <div className="tool">
      <form className="inputs" onSubmit={submit}>
        <h2>Option pricing</h2>
        <p className="lede">Price a European option with Black-Scholes and check it against Monte Carlo.</p>
        <Field label="Type">
          <select value={f.kind} onChange={set("kind")}><option value="call">Call</option><option value="put">Put</option></select>
        </Field>
        <Field label="Spot price"><input type="number" step="any" value={f.spot} onChange={set("spot")} /></Field>
        <Field label="Strike"><input type="number" step="any" value={f.strike} onChange={set("strike")} /></Field>
        <Field label="Maturity (years)"><input type="number" step="0.25" value={f.maturity} onChange={set("maturity")} /></Field>
        <Field label="Risk-free rate" hint="Decimal"><input type="number" step="0.005" value={f.rate} onChange={set("rate")} /></Field>
        <Field label="Volatility" hint="Decimal"><input type="number" step="0.01" value={f.vol} onChange={set("vol")} /></Field>
        <Field label="Dividend yield" hint="Decimal"><input type="number" step="0.005" value={f.dividend} onChange={set("dividend")} /></Field>
        <button className="primary" disabled={loading}>Price option</button>
        <Status loading={loading} error={error} />
      </form>

      <div className="results">
        {!data && !loading && !error && <p className="empty">Set the contract terms and price the option.</p>}
        {data && (
          <>
            <div className="stats">
              <Stat label="Black-Scholes price" value={num(data.black_scholes.price, 4)} />
              <Stat label="Monte Carlo price" value={num(data.monte_carlo.price, 4)} />
              <Stat label="Monte Carlo std. error" value={num(data.monte_carlo.std_error, 4)} />
            </div>
            <h3>Greeks</h3>
            <div className="stats">
              <Stat label="Delta" value={num(data.black_scholes.delta, 4)} />
              <Stat label="Gamma" value={num(data.black_scholes.gamma, 4)} />
              <Stat label="Vega (per vol point)" value={num(data.black_scholes.vega, 4)} />
              <Stat label="Theta (per day)" value={num(data.black_scholes.theta, 4)} />
              <Stat label="Rho (per 1%)" value={num(data.black_scholes.rho, 4)} />
            </div>
            <h3>Value today vs payoff at expiry</h3>
            <div className="chart">
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={data.payoff} margin={{ top: 8, right: 16, bottom: 20, left: 4 }}>
                  <CartesianGrid stroke="#E4E9ED" />
                  <XAxis dataKey="spot" tickFormatter={(v) => v.toFixed(0)} label={{ value: "Underlying price", position: "insideBottom", offset: -10, fill: "#5B6B7A" }} />
                  <YAxis tickFormatter={(v) => v.toFixed(0)} />
                  <Tooltip formatter={(v) => num(v)} labelFormatter={(v) => `Spot ${num(v, 1)}`} />
                  <Legend verticalAlign="top" height={30} />
                  <ReferenceLine x={Number(f.strike)} stroke="#B9C2CB" strokeDasharray="4 4" />
                  <Line type="monotone" dataKey="payoff" name="Payoff at expiry" stroke="#B9C2CB" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="value" name="Value today" stroke="#0A6B5B" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
