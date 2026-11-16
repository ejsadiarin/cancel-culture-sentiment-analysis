import { useEffect, useState } from "react";
import { useCase } from "../../context/CaseContext";
import { fmtDate, fmtDecimal, fmtInt, slotShort } from "../../lib/format";
import { Callout, Point, StepCopy, Viz } from "../parts";

export function DesignStep() {
  const { caseData } = useCase();
  const [selected, setSelected] = useState(10);
  const slot = caseData.slots[selected];

  useEffect(() => setSelected(10), [caseData.id]);

  return (
    <section className="step">
      <StepCopy
        number="01"
        label="Design"
        title={
          <>
            Put the apology at the <em>center.</em>
          </>
        }
        lede="Each case is cut into 21 video slots: ten uploads before the apology, the apology itself, and the next ten uploads. Every later metric uses that same grid."
      >
        <div className="points points--two">
          <Point label="10 + 1 + 10">Fixed slot count, not fixed elapsed time.</Point>
          <Point label="Event-relative">Windows follow the uploads around the trigger.</Point>
          <Point label="Eligibility">A discrete trigger, an apology video, ≥1,000 comments.</Point>
          <Point label="Unit">One video slot; comments aggregate upward.</Point>
        </div>

        <Callout>
          The spans differ: Bodeoum covers {caseData.windows.pre.days} pre days and{" "}
          {caseData.windows.post.days} post days; Mimiminu covers 12 and 17. Fixed slots do not
          control for calendar time.
        </Callout>
      </StepCopy>

      <Viz
        title="The 21-slot design"
        meta={`${fmtInt(caseData.analyzed)} comments`}
        foot={
          <span>
            Click any slot. {caseData.slots[0].window === "pre" ? "P10 is the earliest upload; P1 is closest to the apology." : ""}
          </span>
        }
      >
        <div className="slot-strip" role="group" aria-label="Video slots">
          {caseData.slots.map((item, index) => (
            <button
              key={item.slot}
              type="button"
              className={`slot-cell slot-cell--${item.window} ${index === selected ? "is-selected" : ""}`}
              onClick={() => setSelected(index)}
              aria-pressed={index === selected}
              title={`${slotShort(item.slot)} · ${item.title}`}
            >
              <span className="slot-cell__bar" style={{ height: `${Math.max(12, (item.sentiment - 0.74) * 520)}%` }} />
              <span className="slot-cell__label">{slotShort(item.slot)}</span>
            </button>
          ))}
        </div>

        <div className="slot-detail">
          <div className="slot-detail__top">
            <span className={`slot-badge slot-badge--${slot.window}`}>{slotShort(slot.slot)}</span>
            <span className="slot-detail__date">{fmtDate(slot.date)}</span>
            <span className="slot-detail__n">{fmtInt(slot.n)} comments</span>
          </div>
          <h3>{slot.title}</h3>
          {slot.window === "cancel" ? (
            <p className="slot-detail__translation">“{caseData.apologyTitleEn}”</p>
          ) : null}
          <div className="slot-detail__stats">
            <span>
              mean <strong>{fmtDecimal(slot.sentiment)}</strong>
            </span>
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
