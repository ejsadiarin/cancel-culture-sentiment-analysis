import { useCase } from "../../context/CaseContext";
import { fmtR, fmtSignedPct } from "../../lib/format";
import { Callout, StepCopy } from "../parts";

export function FindingsStep({ onRestart }: { onRestart: () => void }) {
  const { data } = useCase();
  const bodeoum = data.cases.bodeoum_tv;
  const mimiminu = data.cases.mimiminu;
  const inDegree = data.evaluation.pearson.find((metric) => metric.key === "in_degree_mean")!;

  return (
    <section className="step step--findings">
      <StepCopy
        number="10"
        label="Findings"
        title={
          <>
            What the pipeline can—and <em>cannot</em> say.
          </>
        }
        lede="The method supports a comparative description of two apologies, not a general law of cancel culture. These are the claims that survive the checks, followed by the limits that frame them."
      >
        <div className="findings-grid">
          <div className="finding">
            <span>01</span>
            <h3>The apology is not a fixed bottom.</h3>
            <p>
              Bodeoum drops {fmtSignedPct(bodeoum.recovery.pctCancelVsPre)} at the apology, then
              finishes {fmtSignedPct(bodeoum.recovery.pctPostVsPre)} above its before baseline.
              Mimiminu moves {fmtSignedPct(mimiminu.recovery.pctCancelVsPre)} and{" "}
              {fmtSignedPct(mimiminu.recovery.pctPostVsPre)}—no V-shaped collapse.
            </p>
          </div>
          <div className="finding">
            <span>02</span>
            <h3>Bigger is not denser.</h3>
            <p>
              Bodeoum's apology graph grows edges {bodeoum.network.amplification.edges.toFixed(2)}×
              while density falls to {bodeoum.network.amplification.density.toFixed(2)}×. Mimiminu
              shrinks to {mimiminu.network.amplification.edges.toFixed(2)}× the edges but becomes{" "}
              {mimiminu.network.amplification.density.toFixed(2)}× denser.
            </p>
          </div>
          <div className="finding">
            <span>03</span>
            <h3>Concentration tracks negativity.</h3>
            <p>
              Mean in-degree correlates at {fmtR(inDegree.bodeoum_tv.r)} for Bodeoum and{" "}
              {fmtR(inDegree.mimiminu.r)} for Mimiminu. Slots with more reply attention on fewer
              authors tend to have lower sentiment.
            </p>
          </div>
          <div className="finding">
            <span>04</span>
            <h3>Repair is visible, not isolable.</h3>
            <p>
              Post-apology sentiment rises alongside apologies, refunds, and renewed uploads. With
              two cases and a single scrape, the design cannot isolate which action moved it.
            </p>
          </div>
        </div>
      </StepCopy>

      <aside className="findings-panel">
        <Callout>
          The unit of analysis is a video slot. The model describes audience reaction in comments;
          it does not measure public opinion, revenue, or long-term reputation.
        </Callout>

        <p className="kicker">Read with limits</p>
        <ul className="limits">
          <li>
            <strong>Two cases.</strong> Both were selected for a discrete trigger, a formal apology,
            and at least 1,000 comments.
          </li>
          <li>
            <strong>Fixed slots, unequal time.</strong> The videos span different calendar windows,
            so fixed counts do not control elapsed time.
          </li>
          <li>
            <strong>One scrape.</strong> Comments were collected at a single point, not in real time;
            windows are video-content groups.
          </li>
          <li>
            <strong>Transcripts unanalyzed.</strong> Whisper ran, but the paper does not measure
            spoken content or apology delivery.
          </li>
          <li>
            <strong>Neutral is a band.</strong> Scores between 0.40 and 0.60 are flattened to NEUTRAL;
            this is a confidence guardrail.
          </li>
          <li>
            <strong>Correlation is ecological.</strong> Structure and sentiment move together across
            slots; the design does not identify a cause.
          </li>
        </ul>

        <div className="actions actions--wrap">
          <a className="deck-btn deck-btn--ghost" href={data.meta.paper} target="_blank" rel="noreferrer">
            Paper ↗
          </a>
          <a className="deck-btn deck-btn--ghost" href={data.meta.slides} target="_blank" rel="noreferrer">
            Slides ↗
          </a>
          <button type="button" className="deck-btn deck-btn--primary" onClick={onRestart}>
            Start over ↺
          </button>
        </div>

        <p className="viz__foot">
          Full pipeline and source:{" "}
          <a href={data.meta.repo} target="_blank" rel="noreferrer">
            GitHub repository ↗
          </a>
        </p>
      </aside>
    </section>
  );
}
