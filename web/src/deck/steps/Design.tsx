import { useEffect, useState } from "react";
import { useCase } from "../../context/CaseContext";
import { fmtDate, fmtDecimal, fmtInt, slotLabel, slotShort } from "../../lib/format";
import { StepCopy, Viz } from "../parts";

export function DesignStep() {
  const { caseData } = useCase();
  const [selected, setSelected] = useState(10);
  const slot = caseData.slots[selected];

  useEffect(() => setSelected(10), [caseData.id]);

  return (
    <section className="step">
      <StepCopy
        number="01"
        label="Setup"
        title={
          <>
            The apology is the <em>center.</em>
          </>
        }
        lede="Each case is 21 videos: ten before the apology, the apology, ten after."
      />

      <Viz
        title="The 21-video design"
        meta={`${caseData.windows.pre.days} days before · ${caseData.windows.post.days} after`}
        foot="Tap a video to inspect it."
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
            <span className={`slot-badge slot-badge--${slot.window}`}>{slotLabel(slot.slot)}</span>
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
