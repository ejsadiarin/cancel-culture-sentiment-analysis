import { useEffect, useState } from "react";
import { useCase } from "../../context/CaseContext";
import { fmtP, fmtR } from "../../lib/format";
import { CorrelationScatter } from "../charts";
import { Callout, Point, StepCopy, Viz } from "../parts";

const METRICS = ["in_degree_mean", "cascade_depth", "density", "modularity"] as const;

const INSIGHT: Record<string, string> = {
  in_degree_mean:
    "Both cases point the same way: slots where reply attention concentrates on fewer authors tend to have lower mean sentiment.",
  cascade_depth:
    "Longer reply chains also travel with lower sentiment, but the association is weaker than mean in-degree.",
  density:
    "The cases diverge. Bodeoum's association is not significant; Mimiminu's denser slots have higher sentiment.",
  modularity:
    "Community separation has no significant relationship with sentiment in either case. This is a useful non-finding.",
};

export function CorrelationStep() {
  const { data, caseData, otherCase } = useCase();
  const [metricKey, setMetricKey] = useState<string>("in_degree_mean");

  useEffect(() => setMetricKey("in_degree_mean"), [caseData.id]);

  const metric =
    data.evaluation.pearson.find((item) => item.key === metricKey) ??
    data.evaluation.pearson[0];
  const stats = metric[caseData.id];
  const otherStats = metric[otherCase.id];
  const inDegree = data.evaluation.pearson.find((item) => item.key === "in_degree_mean")!;

  return (
    <section className="step step--correlation">
      <StepCopy
        number="09"
        label="Correlation"
        title={
          <>
            Does the shape of conversation travel with its <em>mood?</em>
          </>
        }
        lede="Pearson correlation is computed across the 21 video slots. Each dot is one upload, not one comment, so this is an ecological association between graph structure and mean sentiment."
      >
        <div className="points">
          <Point label="21 dots">One dot per video slot; sentiment is the same slot mean as the trajectory.</Point>
          <Point label="Mean in-degree">
            {fmtR(inDegree.bodeoum_tv.r)} (Bodeoum) and {fmtR(inDegree.mimiminu.r)} (Mimiminu).
            More concentrated replies, lower sentiment.
          </Point>
          <Point label="Density">Significant for Mimiminu, not for Bodeoum. Direction is not universal.</Point>
          <Point label="Modularity">Not significant in either case; not every network metric moves with mood.</Point>
        </div>

        <Callout>
          Correlation across slots, not causation: a third factor, such as audience size or age,
          could move both.
        </Callout>
      </StepCopy>

      <Viz
        title={`${metric.label} vs. mean sentiment`}
        meta={`${caseData.name} · 21 video slots`}
        foot="Filled dots: selected case, coloured by window. Hollow dots: the other case. Line: least-squares fit."
      >
        <div className="metric-pills" role="group" aria-label="Choose a network metric">
          {METRICS.map((key) => {
            const item = data.evaluation.pearson.find((metricItem) => metricItem.key === key);
            if (!item) return null;
            const itemStats = item[caseData.id];
            return (
              <button
                key={key}
                type="button"
                className={`metric-pill ${metricKey === key ? "is-active" : ""} ${
                  itemStats.sig ? "is-sig" : ""
                }`}
                onClick={() => setMetricKey(key)}
                aria-pressed={metricKey === key}
              >
                <span>{item.label}</span>
                <b>{fmtR(itemStats.r)}</b>
                <i>{itemStats.sig ? "sig" : "ns"}</i>
              </button>
            );
          })}
        </div>

        <CorrelationScatter
          caseData={caseData}
          otherCase={otherCase}
          metricKey={metricKey}
          metricLabel={metric.label}
        />

        <div className="corr-stats">
          <div>
            <span>{caseData.short}</span>
            <strong>{fmtR(stats.r)}</strong>
            <small>
              r · p {fmtP(stats.p)} · {stats.sig ? "significant" : "not significant"}
            </small>
          </div>
          <div className="corr-stats__other">
            <span>{otherCase.short}</span>
            <strong>{fmtR(otherStats.r)}</strong>
            <small>reference · p {fmtP(otherStats.p)}</small>
          </div>
        </div>

        <p className="example-note">{INSIGHT[metricKey] ?? metric.description}</p>
      </Viz>
    </section>
  );
}
