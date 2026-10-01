import { ModusWcBadge, ModusWcButton, ModusWcCard } from '@trimble-oss/moduswebcomponents-react';
import { useMemo, useState } from 'react';
import {
  engineeringEdges,
  engineeringNodes,
  sheetPilotEdges,
  sheetPilotNodes,
  statusLabels,
  type WorkflowLink,
  type WorkflowNode,
} from '../data/workflow-nodes';

export type WorkflowGraphVariant = 'sheet' | 'engineering';

interface WorkflowGraphProps {
  variant?: WorkflowGraphVariant;
  progress?: number;
  initialSelectedId?: string;
  showDetail?: boolean;
}

const SUB_W = 52;
const SUB_H = 20;
const SUB_GAP = 4;

function nodeClass(node: WorkflowNode, selectedId: string) {
  return `workflow-node workflow-node-${node.status} ${node.id === selectedId ? 'is-selected' : ''}`;
}

function subLinkClass(kind: WorkflowLink['kind']) {
  return `workflow-subnode workflow-subnode-${kind}`;
}

function openLink(url: string) {
  window.open(url, '_blank', 'noopener,noreferrer');
}

function layoutSubLinks(links: WorkflowLink[], cx: number, baseY: number) {
  const columns = Math.min(links.length, 2);
  const startX = cx - ((columns * (SUB_W + SUB_GAP) - SUB_GAP) / 2);
  return links.map((link, index) => ({
    link,
    x: startX + (index % columns) * (SUB_W + SUB_GAP),
    y: baseY + Math.floor(index / columns) * (SUB_H + SUB_GAP),
  }));
}

export function WorkflowGraph({
  variant = 'sheet',
  progress = 1,
  initialSelectedId,
  showDetail = true,
}: WorkflowGraphProps) {
  const nodes = variant === 'engineering' ? engineeringNodes : sheetPilotNodes;
  const edges = variant === 'engineering' ? engineeringEdges : sheetPilotEdges;
  const markerId = variant === 'engineering' ? 'workflow-arrow-eng' : 'workflow-arrow-sheet';
  const defaultId = initialSelectedId ?? (variant === 'engineering' ? 'dev' : 'intake');

  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const [selectedId, setSelectedId] = useState(defaultId);
  const selected = nodeById.get(selectedId) ?? nodes[0];
  const graphOpacity = Math.min(1, Math.max(0.35, (progress - 0.55) * 3.5));

  const viewBox = variant === 'engineering' ? '0 0 1040 340' : '0 0 1080 470';

  const renderLink = (node: WorkflowNode, link: WorkflowLink, x: number, y: number) => (
    <g
      key={`${node.id}-${link.label}-${link.url}`}
      className={subLinkClass(link.kind)}
      role="link"
      tabIndex={0}
      aria-label={`Open ${link.label} for ${node.label}`}
      onClick={(event) => {
        event.stopPropagation();
        openLink(link.url);
      }}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openLink(link.url);
        }
      }}
    >
      <rect x={x} y={y} width={SUB_W} height={SUB_H} rx="6" />
      <text x={x + SUB_W / 2} y={y + 14}>{link.label}</text>
    </g>
  );

  const renderNode = (node: WorkflowNode, x = node.x, y = node.y) => {
    const subLayout = layoutSubLinks(node.links, x, y + 38);
    return (
      <g key={node.id} className={nodeClass(node, selected.id)}>
        <g
          role="button"
          tabIndex={0}
          aria-label={`Select ${node.label}`}
          className="workflow-node-main"
          onClick={() => setSelectedId(node.id)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              setSelectedId(node.id);
            }
          }}
        >
          <rect x={x - 64} y={y - 26} width="128" height="48" rx="12" />
          <circle className="workflow-status-dot" cx={x + 50} cy={y - 14} r="4" />
          <text x={x} y={y + 4}>{node.label}</text>
        </g>
        {subLayout.map(({ link, x: linkX, y: linkY }) => renderLink(node, link, linkX, linkY))}
      </g>
    );
  };

  return (
    <div className={`workflow-layout${showDetail ? '' : ' workflow-layout-graph-only'}`} style={{ opacity: graphOpacity }}>
      <div className="workflow-graph-frame">
        <svg
          className="workflow-graph"
          viewBox={viewBox}
          role="img"
          aria-label={variant === 'engineering' ? 'Engineering Dev QA workflow' : 'Sheet pilot workflow'}
        >
          <defs>
            <marker id={markerId} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M0 0 L8 4 L0 8 Z" fill="#8aa4bc" />
            </marker>
            <marker id="delivery-arrow-green" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M0 0 L8 4 L0 8 Z" fill="#42d477" />
            </marker>
          </defs>
          {variant === 'engineering' ? (
            <g className="workflow-engineering-cycle" aria-label="Dev and QA cycle">
              <line className="workflow-edge" x1="184" y1="125" x2="200" y2="125" markerEnd={`url(#${markerId})`} />
              <line className="workflow-edge" x1="600" y1="125" x2="656" y2="125" markerEnd={`url(#${markerId})`} />
              <path
                className="workflow-edge workflow-edge-feedback"
                d="M 720 155 L 720 272 L 400 272 L 400 244"
                markerEnd={`url(#${markerId})`}
              />
              <text className="workflow-edge-label" x="560" y="288">
                PR comments
              </text>
              <line className="workflow-edge" x1="784" y1="125" x2="980" y2="125" markerEnd={`url(#${markerId})`} />
              <text className="workflow-edge-label" x="880" y="115">
                Ticket completed
              </text>
              <rect className="delivery-cycle-frame" x="200" y="24" width="400" height="220" rx="16" />
              <text className="delivery-cycle-title" x="400" y="54">Dev · QA cycle</text>
              <text className="delivery-cycle-meta" x="400" y="76">
                Skills &amp; rules · AI PDLC (Cursor skills, repo rules, validity layout)
              </text>
              {(['dev', 'qa'] as const).map((id, index) => {
                const node = nodeById.get(id);
                if (!node) return null;
                const x = index === 0 ? 300 : 500;
                const y = 130;
                return (
                  <g key={id} className={nodeClass(node, selected.id)}>
                    <g
                      role="button"
                      tabIndex={0}
                      aria-label={`Select ${node.label}`}
                      className="workflow-node-main delivery-inner"
                      onClick={() => setSelectedId(id)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          setSelectedId(id);
                        }
                      }}
                    >
                      <rect x={x - 50} y={y - 24} width="100" height="48" rx="10" />
                      <text x={x} y={y + 5}>{node.label}</text>
                    </g>
                    {layoutSubLinks(node.links, x, y + 40).map(({ link, x: linkX, y: linkY }) =>
                      renderLink(node, link, linkX, linkY),
                    )}
                  </g>
                );
              })}
              <path className="delivery-inner-edge" d="M350 130 L450 130" markerEnd="url(#delivery-arrow-green)" />
              <path className="delivery-inner-edge delivery-inner-edge-back" d="M450 116 L350 116" markerEnd="url(#delivery-arrow-green)" />
              <text className="delivery-loop-label" x="400" y="174">back and forth</text>
            </g>
          ) : edges.map(([fromId, toId]) => {
            const from = nodeById.get(fromId);
            const to = nodeById.get(toId);
            if (!from || !to) return null;
            if (
              (fromId === 'ledger' && toId === 'review') ||
              (fromId === 'review' && toId === 'approve')
            ) {
              const isLedgerReview = fromId === 'ledger';
              const startX = isLedgerReview ? 400 : 540;
              const startY = isLedgerReview ? 274 : 176;
              const endX = isLedgerReview ? 460 : 600;
              const endY = isLedgerReview ? 176 : 274;
              return (
                <g key={`${fromId}-${toId}`}>
                  <path
                    className="workflow-edge"
                    d={`M ${startX} ${startY} L ${endX} ${endY}`}
                    markerEnd={`url(#${markerId})`}
                  />
                  <path
                    className="workflow-edge workflow-edge-return"
                    d={`M ${endX} ${endY + 10} L ${startX} ${startY + 10}`}
                    markerEnd={`url(#${markerId})`}
                  />
                </g>
              );
            }

            if (fromId === 'orchestrator' && toId === 'ledger') {
              return (
                <path
                  key={`${fromId}-${toId}`}
                  className="workflow-edge"
                  d={`M ${from.x} ${from.y + 26} L ${from.x} ${to.y - 26}`}
                  markerEnd={`url(#${markerId})`}
                />
              );
            }

            if (fromId === 'figma' && toId === 'ledger') {
              return (
                <path
                  key={`${fromId}-${toId}`}
                  className="workflow-edge"
                  d={`M ${from.x} ${from.y - 26} L ${to.x} ${to.y + 26}`}
                  markerEnd={`url(#${markerId})`}
                />
              );
            }

            return (
              <line
                key={`${fromId}-${toId}`}
                className="workflow-edge"
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                markerEnd={`url(#${markerId})`}
              />
            );
          })}
          {variant === 'engineering'
            ? nodes
                .filter((node) => !['dev', 'qa'].includes(node.id))
                .map((node) => renderNode(node, node.id === 'issue28' ? 120 : 720, 125))
            : nodes.map((node) => renderNode(node))}
        </svg>
        <div className="graph-legend" aria-label="Workflow legend">
          {Object.entries(statusLabels)
            .filter(([status]) => status !== 'planned')
            .map(([status, label]) => (
            <span key={status}>
              <i className={`legend-dot legend-dot-${status}`} />
              {label}
            </span>
            ))}
        </div>
      </div>
      {showDetail ? <ModusWcCard className="workflow-detail" bordered padding="comfortable">
        <span slot="title">{selected.label}</span>
        <span slot="subtitle">
          {selected.role} · {statusLabels[selected.status]}
        </span>
        <p>{selected.summary}</p>
        {selected.automation ? (
          <ModusWcBadge color="success" size="sm">
            Custom automation
          </ModusWcBadge>
        ) : null}
        {selected.automation ? <strong>{selected.automation}</strong> : null}
        {selected.links.length > 0 ? (
          <div className="detail-actions">
            {selected.links.map((link) => (
              <ModusWcButton
                key={`${link.kind}-${link.url}`}
                color={link.kind === 'run' ? 'primary' : 'secondary'}
                variant={link.kind === 'run' ? 'filled' : 'outlined'}
                size="sm"
                onButtonClick={() => openLink(link.url)}
              >
                {link.kind === 'automation' ? 'Automation' : link.label}
              </ModusWcButton>
            ))}
          </div>
        ) : (
          <p className="muted-detail">No live links on this step.</p>
        )}
      </ModusWcCard> : null}
    </div>
  );
}
