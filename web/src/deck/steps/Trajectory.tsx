import { useEffect, useState } from "react";
import { useCase } from "../../context/CaseContext";
import { fmtDate, fmtDecimal, fmtInt, fmtSignedPct, slotShort } from "../../lib/format";
import { TrajectoryChart } from "../charts";
import { Callout, Point, StepCopy, Viz } from "../parts";

export function TrajectoryStep() {
  const { data, caseData, otherCase } = useCase();
  const [selected, setSelected] = useState(10);

  useEffect(() => setSelected(10), [caseData.id]);

  const slot = caseData.slots[selected];
  const recovery = caseData.recovery;
  const bodeoum = data.cases.bodeoum_tv.recovery;
  const mimiminu = data.cases.mimiminu.recovery;

  return (
    <section className="step">
      <StepCopy
        number="05"
        label="Trajectory"
        title={
          <>
            The apology is not automatically the <em>bottom.</em>
          </>
        }
        lede="The trajectory uses each video's mean sentiment, not the pooled comment average. That gives every upload one vote and keeps a single enormous comment section from deciding the shape of the story."
      >
        <div className="points">
          <Point label="Slot mean">One point per upload; ten before, the apology, ten after.</Point>
          <Point label="Bodeoum">
            {fmtSignedPct(bodeoum.pctCancelVsPre)} at the apology, then{" "}
            {fmtSignedPct(bodeoum.pctPostVsPre)} above the before baseline. Nadir:{" "}
            {slotShort(bodeoum.nadirSlot)}.
          </Point>
          <Point label="Mimiminu">
            {fmtSignedPct(mimiminu.pctCancelVsPre)} at the apology and{" "}
            {fmtSignedPct(mimiminu.pctPostVsPre)} after. Nadir: {slotShort(mimiminu.nadirSlot)}.
          </Point>
        </div>

        <Callout>
          {caseData.short}'s apology holds {fmtInt(caseData.windows.cancel.n)} of{" "}
          {fmtInt(caseData.analyzed)} comments. Pooling would let that one video dominate; the
          before slot mean is {fmtDecimal(recovery.slotMean.pre)}, not the pooled{" "}
          {fmtDecimal(caseData.windows.pre.mean)}.
        </Callout>
      </StepCopy>

      <Viz
        title="Slot-level sentiment across the apology"
        meta={`nadir ${slotShort(recovery.nadirSlot)} · ${fmtDecimal(recovery.nadirValue)}`}
        foot="Click a point to inspect the upload. The dashed line is the other case; both use the same slot grid."
      >
        <TrajectoryChart
          caseData={caseData}
          otherCase={otherCase}
          selected={selected}
          onSelect={setSelected}
        />

        <div className="legend legend--trajectory">
          <span>
            <i className="swatch swatch--pre" /> before
          </span>
          <span>
            <i className="swatch swatch--cancel" /> apology
          </span>
          <span>
            <i className="swatch swatch--post" /> after
          </span>
          <span className="legend__note">
            <i className="legend__line" /> {caseData.short}
          </span>
          <span className="legend__note">
            <i className="legend__dash" /> {otherCase.short}
          </span>
        </div>

        <div className="trajectory-detail">
          <div className="trajectory-detail__top">
            <span className={`slot-badge slot-badge--${slot.window}`}>{slotShort(slot.slot)}</span>
            <span>{fmtDate(slot.date)}</span>
            <span>{fmtInt(slot.n)} comments</span>
            <strong>mean {fmtDecimal(slot.sentiment)}</strong>
          </div>
          <p className="trajectory-detail__title">{slot.title}</p>
          <div className="trajectory-detail__stats">
            <span>
              positive <strong>{slot.pos.toFixed(1)}%</strong>
            </span>
            <span>
              negative <strong>{slot.neg.toFixed(1)}%</strong>
            </span>
            <span>
              authors <strong>{fmtInt(slot.network.nodes)}</strong>
            </span>
          </div>
        </div>
      </Viz>
    </section>
  );
}
