import { useEffect, useState } from "react";
import { useCase } from "../../context/CaseContext";
import { fmtInt, slotShort } from "../../lib/format";
import { Callout, Point, StepCopy, Viz } from "../parts";

const EXAMPLE_LABELS = ["Positive", "Negative", "Neutral", "After"];

export function SentimentStep() {
  const { caseData } = useCase();
  const [exampleIndex, setExampleIndex] = useState(2);

  useEffect(() => setExampleIndex(2), [caseData.id]);

  const example = caseData.sentimentExamples[exampleIndex];
  const total = Object.values(caseData.labelCounts).reduce((sum, value) => sum + value, 0);
  const labels = [
    { key: "POSITIVE" as const, color: "#5d7654" },
    { key: "NEGATIVE" as const, color: "#b3452e" },
    { key: "NEUTRAL" as const, color: "#b28a45" },
  ];

  return (
    <section className="step">
      <StepCopy
        number="04"
        label="Sentiment"
        title={
          <>
            Score every comment, then <em>gate confidence.</em>
          </>
        }
        lede="A Korean KoELECTRA model reads each cleaned comment, truncates at 512 tokens, and returns the strongest polarity. If the winning score falls between 0.40 and 0.60, the pipeline records NEUTRAL."
      >
        <div className="points">
          <Point label="Model">
            <code>Copycats/koelectra-base-v3-generalized-sentiment-analysis</code>
          </Point>
          <Point label="Reading">512 tokens max; batch 32; deterministic argmax; CPU.</Point>
          <Point label="Neutral gate">Max confidence 0.40–0.60 is flattened to NEUTRAL.</Point>
        </div>

        <Callout>
          Neutral is a confidence guardrail, not a separate semantic class. A negative sentence can
          become neutral if the model is unsure.
        </Callout>

        <div className="label-stack">
          <div className="label-bar" aria-label="Sentiment label distribution">
            {labels.map((label) => (
              <span
                key={label.key}
                style={{
                  width: `${(caseData.labelCounts[label.key] / total) * 100}%`,
                  background: label.color,
                }}
              />
            ))}
          </div>
          <div className="label-stack__legend">
            {labels.map((label) => (
              <span key={label.key}>
                <i style={{ background: label.color }} />
                {label.key.toLowerCase()} {fmtInt(caseData.labelCounts[label.key])}
              </span>
            ))}
          </div>
        </div>
      </StepCopy>

      <Viz
        title="One comment through the classifier"
        meta={`${fmtInt(caseData.analyzed)} predictions`}
        foot="Scores are the model's max softmax confidence for the chosen polarity."
      >
        <div className="segmented segmented--four" role="tablist" aria-label="Sentiment examples">
          {caseData.sentimentExamples.map((item, index) => (
            <button
              key={`${item.text}-${index}`}
              type="button"
              role="tab"
              aria-selected={exampleIndex === index}
              className={`segment ${exampleIndex === index ? "is-active" : ""}`}
              onClick={() => setExampleIndex(index)}
            >
              {EXAMPLE_LABELS[index] ?? item.kind}
            </button>
          ))}
        </div>

        <div className="comment-card">
          <p className="comment-card__ko">{example.text}</p>
          <p className="comment-card__en">“{example.translation}”</p>
          <div className="comment-card__meta">
            <span>{slotShort(example.slot)}</span>
            <span>{fmtInt(example.likes)} likes</span>
            <span className={`sentiment-chip sentiment-chip--${example.sentiment.toLowerCase()}`}>
              {example.sentiment}
            </span>
          </div>
        </div>

        <div className="confidence">
          <div className="confidence__track">
            <span className="confidence__band" />
            <span className="confidence__marker" style={{ left: `${example.score * 100}%` }} />
          </div>
          <div className="confidence__scale">
            <span>0</span>
            <span>0.40</span>
            <span>0.60</span>
            <span>1</span>
          </div>
          <div className="confidence__readout">
            <span>confidence</span>
            <strong>{example.score.toFixed(3)}</strong>
            <span className="confidence__rule">neutral band 0.40–0.60</span>
          </div>
        </div>

        <p className="example-note">{example.note}</p>
      </Viz>
    </section>
  );
}
