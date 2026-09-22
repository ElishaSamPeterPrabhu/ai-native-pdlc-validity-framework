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
  const startX = cx - ((links.length * (SUB_W + SUB_GAP) - SUB_GAP) / 2);
  return links.map((link, index) => ({
    link,
    x: startX + index * (SUB_W + SUB_GAP),
    y: baseY,
  }));
}

export function WorkflowGraph({
  variant = 'sheet',
  progress = 1,
  initialSelectedId,
}: WorkflowGraphProps) {
  const nodes = variant === 'engineering' ? engineeringNodes : sheetPilotNodes;
  const edges = variant === 'engineering' ? engineeringEdges : sheetPilotEdges;
  const markerId = variant === 'engineering' ? 'workflow-arrow-eng' : 'workflow-arrow-sheet';
  const defaultId = initialSelectedId ?? (variant === 'engineering' ? 'dev' : 'intake');

  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const [selectedId, setSelectedId] = useState(defaultId);
  const selected = nodeById.get(selectedId) ?? nodes[0];
  const graphOpacity = Math.min(1, Math.max(0.35, (progress - 0.55) * 3.5));

  const viewBox = variant === 'engineering' ? '0 0 900 260' : '0 0 1020 260';

  return (
    <div className="workflow-layout" style={{ opacity: graphOpacity }}>
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
          </defs>
          {edges.map(([fromId, toId]) => {
            const from = nodeById.get(fromId);
            const to = nodeById.get(toId);
            if (!from || !to) return null;
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
          {nodes.map((node) => {
            const subLayout = layoutSubLinks(node.links, node.x, node.y + 38);
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
                  <rect x={node.x - 58} y={node.y - 26} width="116" height="48" rx="12" />
                  <circle className="workflow-status-dot" cx={node.x + 44} cy={node.y - 14} r="4" />
                  <text x={node.x} y={node.y - 4}>
                    {node.shortLabel}
                  </text>
                  <text className="workflow-role" x={node.x} y={node.y + 12}>
                    {node.role}
                  </text>
                </g>
                {subLayout.map(({ link, x, y }) => (
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
                    <text x={x + SUB_W / 2} y={y + 14}>
                      {link.label}
                    </text>
                  </g>
                ))}
              </g>
            );
          })}
        </svg>
        <div className="graph-legend" aria-label="Workflow legend">
          {Object.entries(statusLabels).map(([status, label]) => (
            <span key={status}>
              <i className={`legend-dot legend-dot-${status}`} />
              {label}
            </span>
          ))}
        </div>
      </div>
      <ModusWcCard className="workflow-detail" bordered padding="comfortable">
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
      </ModusWcCard>
    </div>
  );
}
