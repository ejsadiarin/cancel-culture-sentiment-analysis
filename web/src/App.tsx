import { useEffect, useMemo, useState } from "react";
import dataJson from "./data/cases.json";
import type { CaseKey, SiteData } from "./types";
import { CaseContext } from "./context/CaseContext";
import { useRevealOnScroll } from "./hooks/useRevealOnScroll";
import { ScrollProgress } from "./components/SectionHead";
import { SiteNav } from "./components/SiteNav";
import { Hero } from "./components/Hero";
import { DesignSection } from "./components/DesignSection";
import { CollectSection } from "./components/CollectSection";
import { PreprocessSection } from "./components/PreprocessSection";
import { SentimentSection } from "./components/SentimentSection";
import { NetworkSection } from "./components/NetworkSection";
import { EvaluationSection } from "./components/EvaluationSection";
import { FindingsSection } from "./components/FindingsSection";
import { Footer } from "./components/Footer";

const data = dataJson as unknown as SiteData;

function initialCase(): CaseKey {
  if (typeof window === "undefined") return "bodeoum_tv";
  const param = new URLSearchParams(window.location.search).get("case");
  if (param === "mimiminu" || param === "bodeoum_tv") return param;
  return "bodeoum_tv";
}

export default function App() {
  const [caseKey, setCaseKey] = useState<CaseKey>(initialCase);
  useRevealOnScroll();

  useEffect(() => {
    document.documentElement.dataset.case = caseKey;
    const url = new URL(window.location.href);
    if (caseKey === "mimiminu") url.searchParams.set("case", "mimiminu");
    else url.searchParams.delete("case");
    window.history.replaceState({}, "", url);
  }, [caseKey]);

  const value = useMemo(() => {
    const otherKey: CaseKey = caseKey === "bodeoum_tv" ? "mimiminu" : "bodeoum_tv";
    return {
      data,
      caseKey,
      otherKey,
      caseData: data.cases[caseKey],
      otherCase: data.cases[otherKey],
      setCaseKey,
      toggleCase: () => setCaseKey(otherKey),
    };
  }, [caseKey]);

  return (
    <CaseContext.Provider value={value}>
      <div className="page">
        <ScrollProgress />
        <SiteNav />
        <main id="main">
          <Hero />
          <DesignSection />
          <CollectSection />
          <PreprocessSection />
          <SentimentSection />
          <NetworkSection />
          <EvaluationSection />
          <FindingsSection />
        </main>
        <Footer />
      </div>
    </CaseContext.Provider>
  );
}
