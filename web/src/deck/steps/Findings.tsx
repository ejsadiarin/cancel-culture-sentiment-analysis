import { useCase } from "../../context/CaseContext";
import { fmtSignedPct } from "../../lib/format";
import { StepCopy } from "../parts";

export function FindingsStep() {
  const { data } = useCase();
  const bodeoum = data.cases.bodeoum_tv;

  return (
    <section className="step step--findings">
      <StepCopy
        number="10"
        label="Findings"
        title={
          <>
            What the study can <em>say.</em>
          </>
        }
        lede="Two apologies. Two different paths."
      >
        <div className="findings-grid">
          <div className="finding">
            <span>01</span>
            <h3>The apology is not always the bottom.</h3>
            <p>
              At the apology, Bodeoum moves {fmtSignedPct(bodeoum.recovery.pctCancelVsPre)}; by the
              after window it is {fmtSignedPct(bodeoum.recovery.pctPostVsPre)} above before.
              Mimiminu barely moves.
            </p>
          </div>
          <div className="finding">
            <span>02</span>
            <h3>Bigger is not denser.</h3>
            <p>Bodeoum's apology gets bigger but sparser. Mimiminu's gets smaller but denser.</p>
          </div>
          <div className="finding">
            <span>03</span>
            <h3>Attention tracks negativity.</h3>
            <p>More concentrated replies track lower mood in both cases.</p>
          </div>
          <div className="finding">
            <span>04</span>
            <h3>Repair is visible, not isolable.</h3>
            <p>Mood rises after repair. Two cases and one scrape cannot isolate the cause.</p>
          </div>
        </div>
      </StepCopy>

      <aside className="findings-panel">
        <p className="kicker">Read with limits</p>
        <ul className="limits">
          <li>
            <strong>Two cases.</strong> Not a general law.
          </li>
          <li>
            <strong>One scrape.</strong> Not a live timeline.
          </li>
          <li>
            <strong>Association.</strong> Not causation.
          </li>
        </ul>

        <div className="actions actions--wrap">
          <a className="deck-btn deck-btn--ghost" href={data.meta.paper} target="_blank" rel="noreferrer">
            Paper ↗
          </a>
          <a className="deck-btn deck-btn--ghost" href={data.meta.slides} target="_blank" rel="noreferrer">
            Slides ↗
          </a>
        </div>
      </aside>
    </section>
  );
}
