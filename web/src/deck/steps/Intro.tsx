import type { CaseKey } from "../../types";
import { useCase } from "../../context/CaseContext";
import { fmtCompact, fmtInt } from "../../lib/format";

export function IntroStep({ onNext }: { onNext: () => void }) {
  const { data, caseKey, caseData, setCaseKey } = useCase();
  const cases: CaseKey[] = ["bodeoum_tv", "mimiminu"];

  return (
    <section className="step step--intro">
      <div className="step-copy">
        <p className="kicker">
          FMLDS 2026 <span>·</span> methodology walkthrough
        </p>
        <h1 tabIndex={-1}>
          Anatomy of a <em>cancellation.</em>
        </h1>
        <p className="lede">
          Ten method decisions turn two Korean apology videos, 42 uploads, and 145,280 YouTube
          comments into a comparable before/after study.
        </p>

        <div className="intro-facts">
          <div>
            <strong>2</strong>
            <span>case studies</span>
          </div>
          <div>
            <strong>42</strong>
            <span>video slots</span>
          </div>
          <div>
            <strong>{fmtInt(data.meta.analyzed)}</strong>
            <span>comments analyzed</span>
          </div>
        </div>

        <div className="actions">
          <button type="button" className="deck-btn deck-btn--primary" onClick={onNext}>
            Start the walkthrough →
          </button>
          <a className="text-link" href={data.meta.paper} target="_blank" rel="noreferrer">
            Read the paper ↗
          </a>
        </div>
      </div>

      <aside className="intro-panel">
        <div className="intro-panel__head">
          <span>Choose a case</span>
          <span>same protocol</span>
        </div>

        <div className="case-picker">
          {cases.map((key, itemIndex) => {
            const item = data.cases[key];
            const active = key === caseKey;
            return (
              <button
                key={key}
                type="button"
                className={`case-option ${active ? "is-active" : ""}`}
                onClick={() => setCaseKey(key)}
                aria-pressed={active}
              >
                <span className="case-option__index">0{itemIndex + 1}</span>
                <span className="case-option__main">
                  <strong>{item.name}</strong>
                  <span>
                    {item.person} · {item.role}
                  </span>
                  <em>{item.trigger}</em>
                </span>
                <span className="case-option__count">{fmtCompact(item.analyzed)}</span>
              </button>
            );
          })}
        </div>

        <div className="intro-brief">
          <p className="intro-brief__label">Current case</p>
          <p className="intro-brief__detail">{caseData.triggerDetail}</p>
          <p className="intro-brief__outcome">{caseData.outcome}</p>
        </div>

        <p className="viz__foot">
          The case switch stays available in the header. Every step recalculates from the same
          pipeline outputs.
        </p>
      </aside>
    </section>
  );
}
