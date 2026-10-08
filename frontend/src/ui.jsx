import { useState } from "react";
import { api } from "./api.js";

// Runs an API call and tracks loading/error/data state.
export function useRequest() {
  const [state, setState] = useState({ data: null, error: null, loading: false });
  const run = async (path, params) => {
    setState({ data: null, error: null, loading: true });
    try {
      setState({ data: await api(path, params), error: null, loading: false });
    } catch (e) {
      setState({ data: null, error: e.message, loading: false });
    }
  };
  return [state, run];
}

export function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}

export function Status({ loading, error }) {
  if (loading)
    return (
      <p className="status" role="status">
        Running. If the server was idle, the first request can take up to a minute.
      </p>
    );
  if (error) return <p className="status error" role="alert">{error}</p>;
  return null;
}

export function Stat({ label, value, tone }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className={"stat-value " + (tone || "")}>{value}</div>
    </div>
  );
}
