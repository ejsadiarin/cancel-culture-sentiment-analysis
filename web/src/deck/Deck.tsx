import { useEffect, useRef, useState, type ReactNode } from "react";
import type { CaseKey } from "../types";
import { useCase } from "../context/CaseContext";
import { fmtCompact } from "../lib/format";
import { IntroStep } from "./steps/Intro";
import { DesignStep } from "./steps/Design";
import { CollectStep } from "./steps/Collect";
import { CleanStep } from "./steps/Clean";
import { SentimentStep } from "./steps/Sentiment";
import { TrajectoryStep } from "./steps/Trajectory";
import { NetworkStep } from "./steps/Network";
import { MetricsStep } from "./steps/Metrics";
import { TestsStep } from "./steps/Tests";
import { CorrelationStep } from "./steps/Correlation";
import { FindingsStep } from "./steps/Findings";
import "./deck.css";

interface Nav {
  next: () => void;
  prev: () => void;
  restart: () => void;
  goTo: (index: number) => void;
}

interface StepDef {
  id: string;
  label: string;
  render: (nav: Nav) => ReactNode;
}

const STEPS: StepDef[] = [
  { id: "start", label: "Start", render: (nav) => <IntroStep onNext={nav.next} /> },
  { id: "design", label: "Design", render: () => <DesignStep /> },
  { id: "collect", label: "Collect", render: () => <CollectStep /> },
  { id: "clean", label: "Clean", render: () => <CleanStep /> },
  { id: "sentiment", label: "Sentiment", render: () => <SentimentStep /> },
  { id: "trajectory", label: "Trajectory", render: () => <TrajectoryStep /> },
  { id: "network", label: "Network", render: () => <NetworkStep /> },
  { id: "metrics", label: "Structure", render: () => <MetricsStep /> },
  { id: "tests", label: "Tests", render: () => <TestsStep /> },
  { id: "correlation", label: "Correlation", render: () => <CorrelationStep /> },
  { id: "findings", label: "Findings", render: (nav) => <FindingsStep onRestart={nav.restart} /> },
];

const CONTENT_STEPS = STEPS.slice(1);
const LAST = STEPS.length - 1;

export function Deck() {
  const { data, caseKey, setCaseKey } = useCase();
  const [index, setIndex] = useState(0);
  const stageRef = useRef<HTMLElement>(null);
  const step = STEPS[index];
  const contentIndex = Math.max(0, index - 1);
  const isLast = index === LAST;

  const next = () => setIndex((current) => Math.min(current + 1, LAST));
  const prev = () => setIndex((current) => Math.max(current - 1, 0));
  const restart = () => setIndex(0);
  const goTo = (target: number) => setIndex(Math.max(0, Math.min(target, LAST)));

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target;
      if (
        target instanceof HTMLElement &&
        target.closest("input, textarea, select, [contenteditable='true']")
      ) {
        return;
      }
      if (event.key === "ArrowRight" || event.key === "PageDown") {
        event.preventDefault();
        next();
      } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
        event.preventDefault();
        prev();
      } else if (event.key === "Home") {
        event.preventDefault();
        restart();
      } else if (event.key === "End") {
        event.preventDefault();
        goTo(LAST);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    const heading = stageRef.current?.querySelector<HTMLElement>("h1, h2");
    heading?.focus({ preventScroll: true });
  }, [index]);

  return (
    <div className="deck">
      <header className="deck-header">
        <button type="button" className="brand" onClick={restart} aria-label="Back to the start">
          <span className="brand__mark" aria-hidden="true" />
          <span className="brand__name">Anatomy of a Cancellation</span>
          <span className="brand__sub">methodology walkthrough</span>
        </button>

        <div className="case-switch" role="group" aria-label="Choose a case study">
          {(["bodeoum_tv", "mimiminu"] as CaseKey[]).map((key) => {
            const item = data.cases[key];
            return (
              <button
                key={key}
                type="button"
                className={`case-switch__button ${caseKey === key ? "is-active" : ""}`}
                aria-pressed={caseKey === key}
                onClick={() => setCaseKey(key)}
              >
                <span className="case-switch__dot" aria-hidden="true" />
                {item.short}
                <span className="case-switch__count">{fmtCompact(item.analyzed)}</span>
              </button>
            );
          })}
        </div>
      </header>

      <nav className="deck-progress" aria-label="Walkthrough steps">
        {CONTENT_STEPS.map((item, itemIndex) => {
          const active = itemIndex === contentIndex && index > 0;
          const done = index > 0 && itemIndex < contentIndex;
          return (
            <button
              key={item.id}
              type="button"
              className={`deck-progress__step ${active ? "is-active" : ""} ${done ? "is-done" : ""}`}
              onClick={() => goTo(itemIndex + 1)}
              aria-label={`Step ${itemIndex + 1}: ${item.label}`}
              aria-current={active ? "step" : undefined}
              title={item.label}
            >
              <span aria-hidden="true" />
            </button>
          );
        })}
      </nav>

      <main className="deck-stage" ref={stageRef} tabIndex={-1}>
        <div className="deck-slide" key={index}>
          {step.render({ next, prev, restart, goTo })}
        </div>
      </main>

      <p className="sr-only" aria-live="polite">
        {index === 0 ? "Introduction" : `Step ${contentIndex} of ${CONTENT_STEPS.length}: ${step.label}`}
      </p>

      <footer className="deck-footer">
        <div className="deck-footer__meta">
          <span>{index === 0 ? "00" : String(contentIndex).padStart(2, "0")} / 10</span>
          <strong>{step.label}</strong>
        </div>

        <div className="deck-footer__hint" aria-hidden="true">
          use <kbd>←</kbd> <kbd>→</kbd>
        </div>

        <div className="deck-footer__nav">
          <button type="button" className="deck-btn deck-btn--ghost" onClick={prev} disabled={index === 0}>
            ← Back
          </button>
          <button
            type="button"
            className="deck-btn deck-btn--primary"
            onClick={isLast ? restart : next}
          >
            {index === 0 ? "Begin" : isLast ? "Start over ↺" : "Next step →"}
          </button>
        </div>
      </footer>
    </div>
  );
}
