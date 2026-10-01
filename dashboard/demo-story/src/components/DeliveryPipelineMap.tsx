export function DeliveryPipelineMap() {
  return (
    <div className="delivery-pipeline" aria-label="Delivery path from issue to review">
      <svg className="delivery-pipeline-svg" viewBox="0 0 860 300" preserveAspectRatio="xMidYMid meet" role="img">
        <defs>
          <marker id="delivery-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0 0 L8 4 L0 8 Z" fill="#6b7a94" />
          </marker>
          <marker id="delivery-arrow-green" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0 0 L8 4 L0 8 Z" fill="#42d477" />
          </marker>
        </defs>

        <line className="delivery-edge" x1={158} y1={168} x2={218} y2={168} markerEnd="url(#delivery-arrow)" />
        <line className="delivery-edge" x1={578} y1={168} x2={628} y2={168} markerEnd="url(#delivery-arrow)" />

        <g className="delivery-node delivery-node-issue">
          <rect x={34} y={136} width={124} height={64} rx={12} />
          <text x={96} y={174}>Issue picked</text>
        </g>

        <g className="delivery-cycle" aria-label="Dev and QA cycle with AI PDLC skills and rules">
          <rect className="delivery-cycle-frame" x={218} y={84} width={360} height={168} rx={16} />
          <text className="delivery-cycle-title" x={398} y={110}>Dev · QA cycle</text>
          <text className="delivery-cycle-meta" x={398} y={128}>
            Skills &amp; rules · AI PDLC (Cursor skills, repo rules, validity layout)
          </text>

          <g className="delivery-inner delivery-inner-dev">
            <rect x={248} y={146} width={100} height={48} rx={10} />
            <text x={298} y={176}>Dev</text>
          </g>
          <g className="delivery-inner delivery-inner-qa">
            <rect x={448} y={146} width={100} height={48} rx={10} />
            <text x={498} y={176}>QA</text>
          </g>

          <path
            className="delivery-inner-edge"
            d="M 348 170 L 448 170"
            markerEnd="url(#delivery-arrow-green)"
          />
          <path
            className="delivery-inner-edge delivery-inner-edge-back"
            d="M 448 156 L 348 156"
            markerEnd="url(#delivery-arrow-green)"
          />
          <text className="delivery-loop-label" x={398} y={196}>back and forth</text>
        </g>

        <g className="delivery-node delivery-node-review">
          <g className="delivery-balloon delivery-balloon-review" aria-label="Large review backlog">
            <path d="M 588 8 L 808 8 L 808 108 L 728 108 L 704 128 L 708 108 L 588 108 Z" />
            <text className="delivery-balloon-title" x={698} y={32}>Loads of code to review</text>
            <g className="delivery-code-stack" aria-hidden="true">
              <rect x={688} y={48} width={100} height={5} rx={2} />
              <rect x={672} y={58} width={116} height={5} rx={2} />
              <rect x={676} y={68} width={112} height={5} rx={2} />
              <rect x={680} y={78} width={108} height={5} rx={2} />
            </g>
          </g>
          <rect x={628} y={136} width={124} height={64} rx={12} />
          <text className="delivery-review-label" x={690} y={174}>Review</text>
        </g>
      </svg>
      <p className="delivery-pipeline-caption">
        AI speeds the dev–QA loop, but review still absorbs the volume.
      </p>
    </div>
  );
}
