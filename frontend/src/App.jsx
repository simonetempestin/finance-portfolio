import { useState } from "react";
import Portfolio from "./pages/Portfolio.jsx";
import Dcf from "./pages/Dcf.jsx";
import Options from "./pages/Options.jsx";
import About from "./pages/About.jsx";
import { PROFILE } from "./profile.js";

const TABS = [
  { id: "portfolio", label: "Portfolio optimisation", Page: Portfolio },
  { id: "dcf", label: "DCF valuation", Page: Dcf },
  { id: "options", label: "Option pricing", Page: Options },
  { id: "about", label: "About", Page: About },
];

export default function App() {
  const [tab, setTab] = useState("portfolio");
  const { Page } = TABS.find((t) => t.id === tab);
  return (
    <div className="shell">
      <header className="masthead">
        <div>
          <h1>{PROFILE.name}</h1>
          <p>{PROFILE.tagline}</p>
        </div>
        <nav aria-label="Projects">
          {TABS.map((t) => (
            <button key={t.id} className={t.id === tab ? "active" : ""} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main>
        <Page />
      </main>
      <footer>
        <a href={PROFILE.github} target="_blank" rel="noreferrer">GitHub</a>
        <a href={PROFILE.linkedin} target="_blank" rel="noreferrer">LinkedIn</a>
        <a href={`mailto:${PROFILE.email}`}>{PROFILE.email}</a>
      </footer>
    </div>
  );
}
