export type NodeStatus = 'demo' | 'specified' | 'partial' | 'planned';

export type WorkflowLinkKind = 'automation' | 'run' | 'asset';

export interface WorkflowLink {
  kind: WorkflowLinkKind;
  label: string;
  url: string;
}

export interface WorkflowNode {
  id: string;
  label: string;
  shortLabel: string;
  role: 'product' | 'design' | 'engineering' | 'shared';
  status: NodeStatus;
  summary: string;
  automation?: string;
  links: WorkflowLink[];
  x: number;
  y: number;
}

export const statusLabels: Record<NodeStatus, string> = {
  demo: 'Demo / wired',
  specified: 'Existing loop',
  partial: 'In progress',
  planned: 'Later',
};

const SHEET = 'https://docs.google.com/spreadsheets/d/1et7NnaPDzpLjZUitRYrRdIExQ6ay2iEmYtCONTSitZ4/edit';
const COORDINATOR_SRC =
  'https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/blob/main/docs/chat-bots/apps-script/cursor-gemini-meeting-intake-coordinator.gs';

export const sheetPilotNodes: WorkflowNode[] = [
  {
    id: 'coordinator',
    label: 'Gemini Coordinator',
    shortLabel: 'Coordinator',
    role: 'product',
    status: 'demo',
    summary: 'Watches Gmail and POSTs to Meeting Intake; relays intake JSON to the ledger.',
    links: [{ kind: 'asset', label: 'Source', url: COORDINATOR_SRC }],
    x: 80,
    y: 72,
  },
  {
    id: 'intake',
    label: 'Meeting Intake',
    shortLabel: 'Intake',
    role: 'product',
    status: 'demo',
    summary: 'Classifies meeting notes. It does not create issues.',
    automation: 'Pilot Meeting Intake',
    links: [
      {
        kind: 'automation',
        label: 'Automation',
        url: 'https://cursor.com/t/trimble/automations/b1b60664-b000-11f1-bf4b-42ffb4d10ea7',
      },
      {
        kind: 'run',
        label: 'Run',
        url: 'https://cursor.com/t/trimble/agents/bc-b4dfd363-93ce-48a9-a058-1ac2c4861dda',
      },
    ],
    x: 220,
    y: 72,
  },
  {
    id: 'orchestrator',
    label: 'Sheet Orchestrator',
    shortLabel: 'Orchestrator',
    role: 'shared',
    status: 'demo',
    summary: 'Routes Controls!B1=review|approve and applies Drive write-backs.',
    links: [{ kind: 'asset', label: 'Ledger', url: SHEET }],
    x: 360,
    y: 72,
  },
  {
    id: 'ledger',
    label: 'Review Ledger',
    shortLabel: 'Ledger',
    role: 'shared',
    status: 'demo',
    summary: 'ReviewItems is the human queue; ReviewItemsDetail holds intake JSON.',
    links: [{ kind: 'asset', label: 'Open sheet', url: SHEET }],
    x: 360,
    y: 168,
  },
  {
    id: 'figma',
    label: 'Figma Agents',
    shortLabel: 'Design',
    role: 'design',
    status: 'demo',
    summary: 'Parallel design track—not triggered by Controls!B1.',
    links: [
      {
        kind: 'asset',
        label: 'Skills doc',
        url: 'https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/blob/main/docs/design-enablement/figma-agent/README.md',
      },
    ],
    x: 500,
    y: 72,
  },
  {
    id: 'review',
    label: 'Pilot Review',
    shortLabel: 'Review',
    role: 'engineering',
    status: 'demo',
    summary: 'Writes cursorComment from repo evidence. Does not create GitHub issues.',
    automation: 'Pilot Review',
    links: [
      {
        kind: 'automation',
        label: 'Automation',
        url: 'https://cursor.com/t/trimble/automations/e3195783-b00b-11f1-bf4b-42ffb4d10ea7',
      },
      {
        kind: 'run',
        label: 'Run T2',
        url: 'https://cursor.com/t/trimble/agents/bc-ecd79503-1bf0-4a23-ac82-b9ab6e5b8bdc',
      },
      {
        kind: 'run',
        label: 'Run r3',
        url: 'https://cursor.com/t/trimble/agents/bc-b9524d5c-744b-4c71-962e-47f23a2881a2',
      },
    ],
    x: 500,
    y: 168,
  },
  {
    id: 'approve',
    label: 'Human Gate',
    shortLabel: 'Approve',
    role: 'engineering',
    status: 'demo',
    summary: 'Human types review or approve on Controls!B1.',
    automation: 'Pilot Approve',
    links: [
      {
        kind: 'automation',
        label: 'Automation',
        url: 'https://cursor.com/t/trimble/automations/8a65434d-b03e-11f1-bf4b-42ffb4d10ea7',
      },
      {
        kind: 'run',
        label: 'Run #49',
        url: 'https://cursor.com/t/trimble/agents/bc-52ce005e-b1de-49ea-a1b6-be6b0b11e5ad',
      },
      {
        kind: 'run',
        label: 'Run skip',
        url: 'https://cursor.com/t/trimble/agents/bc-d327b0b0-4991-4af5-9bf6-f16c2749beea',
      },
    ],
    x: 640,
    y: 168,
  },
  {
    id: 'scaffolding',
    label: 'Issue Scaffolding',
    shortLabel: 'Scaffold',
    role: 'engineering',
    status: 'demo',
    summary: 'Only step on this path that creates or updates the GitHub issue.',
    automation: 'PILOT Issue Scaffolding',
    links: [
      {
        kind: 'automation',
        label: 'Automation',
        url: 'https://cursor.com/t/trimble/automations/288c955b-aaad-11f1-b532-320a589b8025',
      },
      {
        kind: 'run',
        label: 'Run',
        url: 'https://cursor.com/t/trimble/agents/bc-69d7c979-f67d-40dc-8344-e1cb83130f52',
      },
    ],
    x: 780,
    y: 168,
  },
  {
    id: 'issue49',
    label: 'GitHub issue #49',
    shortLabel: 'Issue #49',
    role: 'engineering',
    status: 'demo',
    summary: 'Sheet-approved scaffold: disabled prop on modus-wc-button.',
    links: [
      {
        kind: 'asset',
        label: 'Issue #49',
        url: 'https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49',
      },
    ],
    x: 920,
    y: 168,
  },
];

export const sheetPilotEdges: Array<[string, string]> = [
  ['coordinator', 'intake'],
  ['intake', 'orchestrator'],
  ['orchestrator', 'ledger'],
  ['figma', 'ledger'],
  ['ledger', 'review'],
  ['review', 'approve'],
  ['approve', 'scaffolding'],
  ['scaffolding', 'issue49'],
];

export const engineeringNodes: WorkflowNode[] = [
  {
    id: 'issue49',
    label: 'GitHub issue #49',
    shortLabel: 'Issue #49',
    role: 'engineering',
    status: 'demo',
    summary: 'Output of sheet pilot scaffolding—engineering picks up from here.',
    links: [
      {
        kind: 'asset',
        label: 'Issue #49',
        url: 'https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49',
      },
    ],
    x: 120,
    y: 120,
  },
  {
    id: 'dev',
    label: 'Dev Agent',
    shortLabel: 'Dev',
    role: 'engineering',
    status: 'specified',
    summary: 'Stop-boundary implementation on the pilot fork (PR #42).',
    automation: 'Dev Agent',
    links: [
      {
        kind: 'automation',
        label: 'Automation',
        url: 'https://cursor.com/t/trimble/automations/69f213ff-4748-4bed-a065-9ba8b97d6bfe',
      },
      {
        kind: 'run',
        label: 'Run',
        url: 'https://cursor.com/t/trimble/agents/bc-65dc91fc-b4a6-4657-b25d-e559ac558358',
      },
      {
        kind: 'asset',
        label: 'PR #42',
        url: 'https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42',
      },
    ],
    x: 320,
    y: 120,
  },
  {
    id: 'qa',
    label: 'QA Agent',
    shortLabel: 'QA',
    role: 'engineering',
    status: 'specified',
    summary: 'Verification agent—pass after repair or fail as baseline.',
    automation: 'QA Agent',
    links: [
      {
        kind: 'automation',
        label: 'Automation',
        url: 'https://cursor.com/t/trimble/automations/aac94e20-8523-48e4-a239-26daa40f1675',
      },
      {
        kind: 'run',
        label: 'Pass',
        url: 'https://cursor.com/t/trimble/agents/bc-8cd16c11-18cb-4d99-9148-30f45b2a124a',
      },
      {
        kind: 'run',
        label: 'Fail',
        url: 'https://cursor.com/t/trimble/agents/bc-fdcb9904-68dc-4abe-9671-2e94197ff1de',
      },
    ],
    x: 520,
    y: 120,
  },
  {
    id: 'pr42',
    label: 'PR #42 closed loop',
    shortLabel: 'PR #42',
    role: 'engineering',
    status: 'demo',
    summary: 'Dev → QA fail → repair → QA pass on exp/28-checkbox.',
    links: [
      {
        kind: 'asset',
        label: 'PR #42',
        url: 'https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42',
      },
    ],
    x: 720,
    y: 72,
  },
  {
    id: 'pr34',
    label: 'PR #34 baseline fail',
    shortLabel: 'PR #34',
    role: 'engineering',
    status: 'specified',
    summary: 'Intentional QA FAILED before picture (no repair).',
    links: [
      {
        kind: 'asset',
        label: 'PR #34',
        url: 'https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/34',
      },
      {
        kind: 'run',
        label: 'QA fail',
        url: 'https://cursor.com/t/trimble/agents/bc-fdcb9904-68dc-4abe-9671-2e94197ff1de',
      },
    ],
    x: 720,
    y: 168,
  },
];

export const engineeringEdges: Array<[string, string]> = [
  ['issue49', 'dev'],
  ['dev', 'qa'],
  ['qa', 'pr42'],
  ['qa', 'pr34'],
];

/** @deprecated use sheetPilotNodes */
export const workflowNodes = sheetPilotNodes;
export const workflowEdges = sheetPilotEdges;
