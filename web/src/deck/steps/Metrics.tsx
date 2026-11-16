import { useCase } from "../../context/CaseContext";
import { fmtDensity, fmtInt } from "../../lib/format";
import { Point, StepCopy, Viz } from "../parts";

const WINDOWS = ["pre", "cancel", "post"] as const;

export function MetricsStep() {
  const { caseData } = useCase();
  const windows = caseData.network.windows;
  const amp = caseData.network.amplification;
  const topology =
    caseData.id === "bodeoum_tv"
      ? {
          title: "Expansion + fragmentation",
          text: "More authors and far more reply edges, but the graph becomes much sparser and splits into more communities.",
        }
      : {
          title: "Contraction + consolidation",
          text: "Fewer authors and fewer edges, but the remaining conversation is denser and its communities are more modular.",
        };

  const rows = [
    { label: "Authors", value: (w: typeof windows.pre) => fmtInt(w.nodes) },
    { label: "Reply edges", value: (w: typeof windows.pre) => fmtInt(w.edges) },
    { label: "Density ×10⁻⁴", value: (w: typeof windows.pre) => fmtDensity(w.density) },
    { label: "Modularity", value: (w: typeof windows.pre) => w.modularity.toFixed(3) },
    { label: "Communities", value: (w: typeof windows.pre) => fmtInt(w.communities) },
    { label: "Cascade depth", value: (w: typeof windows.pre) => String(w.cascade) },
  ];

  const amplification = [
    { label: "Edges", value: amp.edges, note: "reply volume" },
    { label: "Authors", value: amp.nodes, note: "people replying" },
    { label: "Density", value: amp.density, note: "connectedness" },
    { label: "Gini", value: amp.gini, note: "concentration" },
  ];

  return (
    <section className="step">
      <StepCopy
        number="07"
        label="Structure"
        title={
          <>
            Size is not the same as <em>shape.</em>
          </>
        }
        lede="Raw node and edge counts rise with turnout. Density, modularity, cascade depth, and Gini describe how the conversation is arranged, so structure is compared within a case rather than across cases."
      >
        <div className="points">
          <Point label="Density">Existing directed edges ÷ all possible directed edges.</Point>
          <Point label="Modularity">Louvain communities at resolution 1.0, seed 42.</Point>
          <Point label="Cascade">The longest reply-to-reply chain in the window.</Point>
          <Point label="Concentration">Gini and hub dominance track how much attention one author absorbs.</Point>
        </div>

      </StepCopy>

      <Viz
        title="Window by window, same case"
        meta={`${caseData.name} · apology ÷ before`}
        foot="Amplification compares the apology window with the ten-video baseline. Raw counts scale with turnout; density and modularity describe structure."
      >
        <p className="topology-note">
          <strong>{topology.title}</strong> {topology.text}
        </p>

        <table className="metric-table">
          <thead>
            <tr>
              <th>Metric</th>
              {WINDOWS.map((window) => (
                <th key={window} className={window === "cancel" ? "is-apology" : ""}>
                  {window === "pre" ? "Before" : window === "cancel" ? "Apology" : "After"}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th>{row.label}</th>
                {WINDOWS.map((window) => (
                  <td key={window} className={window === "cancel" ? "is-apology" : ""}>
                    {row.value(windows[window])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        <div className="amp-cards" aria-label="Apology-to-before amplification">
          {amplification.map((item) => (
            <div key={item.label} className="amp-card">
              <span>{item.label}</span>
              <strong>{item.value.toFixed(2)}×</strong>
              <small>{item.note}</small>
            </div>
          ))}
        </div>
      </Viz>
    </section>
  );
}
