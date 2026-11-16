import { useEffect, useState } from "react";
import { useCase } from "../../context/CaseContext";
import { fmtInt, slotShort } from "../../lib/format";
import { ThreadDiagram } from "../charts";
import { Callout, Point, StepCopy, Viz } from "../parts";

export function NetworkStep() {
  const { caseData } = useCase();
  const thread = caseData.network.thread;
  const [selectedId, setSelectedId] = useState(thread.rootId);

  useEffect(() => setSelectedId(caseData.network.thread.rootId), [caseData.id]);

  const node = thread.nodes.find((item) => item.id === selectedId) ?? thread.nodes[0];
  const inDegree = thread.edges.filter((edge) => edge.target === node.id).length;

  return (
    <section className="step">
      <StepCopy
        number="06"
        label="Network"
        title={
          <>
            Turn replies into a <em>graph.</em>
          </>
        }
        lede="A node is a unique author. A directed edge runs from the replier to the author of the parent comment. Repeated replies add weight to the same edge; top-level comments create no edge."
      >
        <div className="points">
          <Point label="Node">One unique author, even if they wrote several comments.</Point>
          <Point label="Edge">Replier → parent author. The direction is preserved.</Point>
          <Point label="Why pointers matter">Without parent/root IDs, the conversation collapses into a flat comment list.</Point>
        </div>

        <Callout>
          This sample is one real thread: {thread.nodeCount} comments, {thread.authorCount} authors,
          depth {thread.maxDepth}. The next step aggregates every thread in each window, so its
          graphs are much larger.
        </Callout>
      </StepCopy>

      <Viz
        title="One thread, rebuilt as a reply graph"
        meta={`${thread.authorCount} authors · ${thread.edges.length} reply links`}
        foot="Nodes are numbered; color is the model's sentiment label. Click a node to read the comment and its translation."
      >
        <ThreadDiagram thread={thread} selectedId={selectedId} onSelect={setSelectedId} />

        <div className="thread-detail">
          <div className="thread-detail__top">
            <span className="thread-detail__label">
              {slotShort(node.slot)} · depth {node.depth}
            </span>
            <strong>@{node.handle}</strong>
            <span className={`sentiment-chip sentiment-chip--${node.sentiment.toLowerCase()}`}>
              {node.sentiment}
            </span>
            <span>{fmtInt(node.likes)} likes</span>
            <span>in-degree {inDegree}</span>
          </div>
          <p className="thread-detail__text">{node.text}</p>
          <p className="thread-detail__translation">“{node.translation}”</p>
        </div>
      </Viz>
    </section>
  );
}
