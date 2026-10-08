const API = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export async function api(path, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== "" && v != null)
  ).toString();
  let res;
  try {
    res = await fetch(`${API}${path}${qs ? "?" + qs : ""}`);
  } catch {
    throw new Error("Cannot reach the server. It may be starting up: wait a few seconds and retry.");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status}).`);
  return body;
}

export const pct = (x, d = 1) => (x == null ? "n/a" : (x * 100).toFixed(d) + "%");
export const num = (x, d = 2) =>
  x == null ? "n/a" : Number(x).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
export const big = (x) => {
  const a = Math.abs(x);
  if (a >= 1e12) return (x / 1e12).toFixed(2) + "T";
  if (a >= 1e9) return (x / 1e9).toFixed(2) + "B";
  if (a >= 1e6) return (x / 1e6).toFixed(2) + "M";
  return num(x, 0);
};
