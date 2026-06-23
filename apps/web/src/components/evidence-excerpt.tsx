"use client";

import { useState } from "react";

type EvidenceExcerptProps = {
  content: string;
  contentId: string;
};

export function EvidenceExcerpt({ content, contentId }: EvidenceExcerptProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`evidence-excerpt ${expanded ? "expanded" : "collapsed"}`}>
      <p className="evidence-content" id={contentId}>{content}</p>
      <button
        aria-controls={contentId}
        aria-expanded={expanded}
        className="evidence-toggle"
        onClick={() => setExpanded((current) => !current)}
        type="button"
      >
        {expanded ? "Show less" : "Show full excerpt"}
      </button>
    </div>
  );
}
