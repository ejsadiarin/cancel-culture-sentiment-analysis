import { useCase } from "../../context/CaseContext";
import { WINDOW_LABEL } from "../../lib/format";
import { Callout, Point, StepCopy, Viz } from "../parts";

const WINDOWS = ["pre", "cancel", "post"] as const;

export function TestsStep() {
  const { data, caseData } = useCase();
  const kruskal = data.evaluation.kruskal[caseData.id];
  const dunn = data.evaluation.dunn[caseData.id];

  const pair = (a: (typeof WINDOWS)[number], b: (typeof WINDOWS)[number]) =>
    dunn.find((item) => (item.a === a && item.b === b) || (item.a === b && item.b === a));

  return (
    <section className="step">
      <StepCopy
        number="08"
        label="Tests"
        title={
          <>
            Check the assumptions before the <em>claim.</em>
          </>
        }
        lede="Shapiro–Wilk finds non-normal sentiment distributions in both cases, so the pipeline uses a rank-based Kruskal–Wallis test instead of ANOVA. Dunn's post-hoc then asks which window pairs differ."
      >
        <div className="points">
          <Point label="Shapiro–Wilk">Both cases, all windows: non-normal at p &lt; 0.001.</Point>
          <Point label="Kruskal–Wallis">One test across before, apology, and after.</Point>
          <Point label="Dunn + Bonferroni">Pairwise comparisons with a multiple-test correction.</Point>
        </div>

        <Callout>
          {caseData.id === "bodeoum_tv"
            ? "Bodeoum separates every pair at p < 0.001: before, apology, and after all differ."
            : "Mimiminu separates before from both later windows, but apology and after are statistically indistinguishable (p = 1.000)."}
        </Callout>

        <p className="unit-check">
          Unit check: these tests use <b>comment-level</b> scores. The correlation step uses the{" "}
          <b>21 slot-level means</b>; mixing the units would inflate significance.
        </p>
      </StepCopy>

      <Viz
        title="Dunn pairwise matrix"
        meta={`${caseData.short} · comment-level scores`}
        foot="Cells show Bonferroni-adjusted p-values. The matrix is symmetric; the diagonal compares a window with itself."
      >
        <div className="kw-stat">
          <span>Kruskal–Wallis</span>
          <strong>H = {kruskal.H.toFixed(2)}</strong>
          <span>df {kruskal.df}</span>
          <span>p {kruskal.p}</span>
        </div>

        <table className="dunn">
          <thead>
            <tr>
              <th aria-label="Window" />
              {WINDOWS.map((window) => (
                <th key={window}>{WINDOW_LABEL[window]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {WINDOWS.map((row) => (
              <tr key={row}>
                <th>{WINDOW_LABEL[row]}</th>
                {WINDOWS.map((column) => {
                  if (row === column) {
                    return (
                      <td key={column} className="dunn__cell is-diag">
                        —
                      </td>
                    );
                  }
                  const result = pair(row, column);
                  return (
                    <td
                      key={column}
                      className={`dunn__cell ${result?.sig ? "is-sig" : "is-ns"}`}
                    >
                      {result?.p ?? "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>

        <p className="dunn__note">
          Significant cells mark a difference in the tested distribution. Significance is not an
          effect size, and it does not establish causation.
        </p>
      </Viz>
    </section>
  );
}
