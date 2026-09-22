import { useEffect, useRef, useState } from 'react';

const PARTS = [
  { label: 'Product', color: '#62b0ff' },
  { label: 'Design', color: '#b494ff' },
  { label: 'Engineering', color: '#42d477' },
] as const;

export const ENG_SPEED_MULT = 4.2;

const BASE_SPEED = 110;

const VIEW_W = 880;
const VIEW_H = 300;
const FRAME = { x: 20, y: 18, w: VIEW_W - 40, h: VIEW_H - 36, rx: 20 };
const RAIL_Y = 132;
const RAIL_START = 56;
const RAIL_END = VIEW_W - 88;
const STEP_X = [140, 320, 500, 680];
const STEP_W = 132;
const STEP_H = 100;
const ENG_W = 168;
const ENG_H = 124;

const LEG_LENGTHS = [STEP_X[1] - STEP_X[0], STEP_X[2] - STEP_X[1], STEP_X[3] - STEP_X[2]];
const TOTAL_LENGTH = LEG_LENGTHS[0] + LEG_LENGTHS[1] + LEG_LENGTHS[2];

const SIDE_STEPS = [
  { stepIndex: 0, label: 'Product', className: 'rolling-step-product' },
  { stepIndex: 1, label: 'Design', className: 'rolling-step-design' },
  { stepIndex: 3, label: 'User', className: 'rolling-step-user' },
] as const;

type Variant = 'coupled' | 'aiBoost';

interface RollingTrackProps {
  variant: Variant;
  reducedMotion: boolean;
}

function legMultiplier(legIndex: number, variant: Variant): number {
  if (variant === 'coupled') return 1;
  return legIndex === 2 ? ENG_SPEED_MULT : 1;
}

function positionAtDistance(s: number): { x: number; y: number } {
  const d = Math.min(Math.max(s, 0), TOTAL_LENGTH);
  const [l0, l1, l2] = LEG_LENGTHS;

  if (d <= l0) {
    const t = l0 > 0 ? d / l0 : 0;
    return { x: STEP_X[0] + (STEP_X[1] - STEP_X[0]) * t, y: RAIL_Y };
  }
  if (d <= l0 + l1) {
    const t = (d - l0) / l1;
    return { x: STEP_X[1] + (STEP_X[2] - STEP_X[1]) * t, y: RAIL_Y };
  }
  const t = (d - l0 - l1) / l2;
  return { x: STEP_X[2] + (STEP_X[3] - STEP_X[2]) * t, y: RAIL_Y };
}

function legIndexAtDistance(s: number): number {
  const d = Math.min(Math.max(s, 0), TOTAL_LENGTH - 0.001);
  if (d < LEG_LENGTHS[0]) return 0;
  if (d < LEG_LENGTHS[0] + LEG_LENGTHS[1]) return 1;
  return 2;
}

function formatMult(n: number): string {
  if (Math.abs(n - 1) < 0.08) return '1';
  return n.toFixed(1);
}

function stepBox(index: number, isBoost: boolean) {
  const cx = STEP_X[index];
  const isEng = index === 2;
  const w = isEng && isBoost ? ENG_W : STEP_W;
  const h = isEng && isBoost ? ENG_H : STEP_H;
  return { cx, w, h, x: cx - w / 2, y: RAIL_Y - h / 2 };
}

function railSegments(isBoost: boolean) {
  const boxes = [0, 1, 2, 3].map((i) => stepBox(i, isBoost));
  const segments: { x1: number; x2: number; gap: boolean }[] = [
    { x1: RAIL_START, x2: boxes[0].x, gap: true },
  ];
  for (let i = 0; i < boxes.length - 1; i += 1) {
    segments.push({ x1: boxes[i].x + boxes[i].w, x2: boxes[i + 1].x, gap: false });
  }
  segments.push({ x1: boxes[3].x + boxes[3].w, x2: RAIL_END, gap: true });
  return segments;
}

export function RollingTrack({ variant, reducedMotion }: RollingTrackProps) {
  const [ball, setBall] = useState({ x: STEP_X[0], y: RAIL_Y });
  const [mults, setMults] = useState<[number, number, number]>([1, 1, 1]);
  const arcRef = useRef(0);
  const legStartRef = useRef(performance.now() / 1000);
  const legTimesRef = useRef<[number, number, number]>([1, 1, 1]);
  const currentLegRef = useRef(0);
  const rafRef = useRef(0);

  const isBoost = variant === 'aiBoost';

  const commitLegTime = (legIndex: number, elapsed: number, v: Variant) => {
    legTimesRef.current[legIndex] = elapsed;
    const avg =
      (legTimesRef.current[0] + legTimesRef.current[1] + legTimesRef.current[2]) / 3;
    const nextMults: [number, number, number] = [
      avg / legTimesRef.current[0],
      avg / legTimesRef.current[1],
      avg / legTimesRef.current[2],
    ];
    if (v === 'coupled') {
      setMults([1, 1, 1]);
    } else {
      setMults(nextMults);
    }
  };

  useEffect(() => {
    if (reducedMotion) {
      setBall({ x: STEP_X[0], y: RAIL_Y });
      setMults([1, 1, variant === 'aiBoost' ? ENG_SPEED_MULT : 1]);
      return;
    }

    arcRef.current = 0;
    currentLegRef.current = 0;
    legStartRef.current = performance.now() / 1000;

    let last = performance.now();
    const tick = (now: number) => {
      const delta = Math.min((now - last) / 1000, 0.05);
      last = now;

      const leg = legIndexAtDistance(arcRef.current);
      if (leg !== currentLegRef.current) {
        const elapsed = now / 1000 - legStartRef.current;
        commitLegTime(currentLegRef.current, elapsed, variant);
        currentLegRef.current = leg;
        legStartRef.current = now / 1000;
      }

      const speed = BASE_SPEED * legMultiplier(leg, variant);
      arcRef.current += speed * delta;

      if (arcRef.current >= TOTAL_LENGTH) {
        const elapsed = now / 1000 - legStartRef.current;
        commitLegTime(2, elapsed, variant);
        arcRef.current = 0;
        currentLegRef.current = 0;
        legStartRef.current = now / 1000;
      }

      setBall(positionAtDistance(arcRef.current));
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [variant, reducedMotion]);

  const eng = stepBox(2, isBoost);
  const rails = railSegments(isBoost);

  return (
    <div className="rolling-widget" aria-label="Product, Design, Engineering, then User">
      <svg
        className="rolling-track-svg"
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
      >
        <defs>
          <filter id="rolling-ball-shadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="2" stdDeviation="4" floodOpacity="0.5" />
          </filter>
        </defs>

        <rect className="rolling-frame" x={FRAME.x} y={FRAME.y} width={FRAME.w} height={FRAME.h} rx={FRAME.rx} />

        {rails.map((seg, i) => (
          <line
            key={i}
            className={seg.gap ? 'rolling-rail rolling-rail-gap' : 'rolling-rail'}
            x1={seg.x1}
            y1={RAIL_Y}
            x2={seg.x2}
            y2={RAIL_Y}
          />
        ))}

        {SIDE_STEPS.map(({ stepIndex, label, className }) => {
          const box = stepBox(stepIndex, isBoost);
          return (
            <g key={label} className={`rolling-step ${className}`}>
              <rect x={box.x} y={box.y} width={box.w} height={box.h} rx={14} />
              <text
                className={stepIndex === 3 ? 'rolling-step-user-label' : undefined}
                x={box.cx}
                y={RAIL_Y + 6}
              >
                {label}
              </text>
            </g>
          );
        })}

        <g className={`rolling-step rolling-step-engineering${isBoost ? ' rolling-step-engineering-boost' : ''}`}>
          <rect x={eng.x} y={eng.y} width={eng.w} height={eng.h} rx={14} />
          <text x={eng.cx} y={RAIL_Y - (isBoost ? 14 : 0)}>Engineering</text>
          {isBoost ? (
            <>
              <text className="rolling-step-sub" x={eng.cx} y={RAIL_Y + 10}>AI catalyst</text>
              <g className="rolling-ai-inside" transform={`translate(${eng.cx}, ${RAIL_Y + 38})`}>
                <rect x={-52} y={-14} width={104} height={28} rx={8} />
                <text x={30} y={2}>AI</text>
                <path className="rolling-boost-arrow" d="M -34 2 L -14 2 L -18 -4 M -14 2 L -18 8" />
                <path className="rolling-boost-arrow rolling-boost-arrow-2" d="M -6 2 L 14 2 L 10 -4 M 14 2 L 10 8" />
              </g>
            </>
          ) : null}
        </g>

        <circle
          className="rolling-ball"
          cx={ball.x}
          cy={ball.y}
          r={14}
          filter="url(#rolling-ball-shadow)"
        />
      </svg>

      <div className="engine-sync-hud" aria-live="polite">
        <div className="engine-sync-row">
          <span className="engine-sync-label">Speed multiplier</span>
          {!isBoost ? (
            <span className="engine-sync-note">three steps · same cadence · handoff to user</span>
          ) : null}
          {isBoost ? (
            <span className="engine-sync-note engine-sync-note-warn">AI boost on Engineering → User</span>
          ) : null}
        </div>
        <div className="engine-sync-grid">
          {PARTS.map((part, i) => (
            <div
              key={part.label}
              className="engine-sync-cell"
              style={{ '--label-color': part.color } as React.CSSProperties}
            >
              <span>{part.label}</span>
              <strong>{isBoost ? formatMult(mults[i]) : '1'}</strong>
              {isBoost ? (
                <small>(capable of {formatMult(ENG_SPEED_MULT)})</small>
              ) : (
                <small>relative pace</small>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
