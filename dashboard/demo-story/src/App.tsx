import { ModusWcBadge, ModusWcButton, ModusWcCard } from '@trimble-oss/moduswebcomponents-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { DeliveryPipelineMap } from './components/DeliveryPipelineMap';
import { RollingTrack } from './components/RollingTrack';
import { LegendBar } from './components/LegendBar';
import { WorkflowGraph } from './components/WorkflowGraph';

const beatCount = 5;

export default function App() {
  const trackRef = useRef<HTMLDivElement>(null);
  const [progress, setProgress] = useState(0);
  const [activeBeat, setActiveBeat] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  const updateProgress = useCallback(() => {
    const track = trackRef.current;
    if (!track) return;
    const maxScroll = track.scrollWidth - track.clientWidth;
    const nextProgress = maxScroll > 0 ? track.scrollLeft / maxScroll : 0;
    setProgress(nextProgress);
    setActiveBeat(Math.min(beatCount - 1, Math.round(nextProgress * (beatCount - 1))));
  }, []);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    track.scrollLeft = 0;
    track.addEventListener('scroll', updateProgress, { passive: true });
    return () => track.removeEventListener('scroll', updateProgress);
  }, [updateProgress]);

  const jumpToBeat = (index: number) => {
    const track = trackRef.current;
    if (!track) return;
    track.children[index]?.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'nearest', inline: 'center' });
  };

  return (
    <main className="story-shell">
      <header className="story-header">
        <div>
          <div className="eyebrow">AI-native PDLC · demo story</div>
          <h1>When Engineering accelerates, the system has to move.</h1>
          <p className="story-lede">
            AI changes the relationship between Product, Design, and Engineering. Scroll left to right to see why throughput
            needs a workflow around it.
          </p>
        </div>

      </header>

      <div className="story-track" ref={trackRef} aria-label="Horizontal demo story">
        <section className="story-panel story-panel-engine" aria-labelledby="beat-one-title">
          <div className="panel-copy">
            <span className="beat-kicker">01 · Coupled system</span>
            <h2 id="beat-one-title">Three functions. One motion.</h2>
            <p>Product, Design, and Engineering only create momentum when each part depends on the others.</p>
          
          </div>
          <RollingTrack variant="coupled" reducedMotion={reducedMotion} />
        </section>

        <section className="story-panel story-panel-engine" aria-labelledby="beat-two-title">
          <div className="panel-copy">
            <span className="beat-kicker">02 · AI as a catalyst</span>
            <h2 id="beat-two-title">Engineering starts moving faster.</h2>
            <p>AI does not just make one function faster. It changes the relationship and puts pressure on the parts that have not adapted.</p>
          
          </div>
          <RollingTrack variant="aiBoost" reducedMotion={reducedMotion} />
        </section>

        <section className="story-panel story-panel-pressure" aria-labelledby="beat-three-title">
          <div className="pressure-layout">
            <div className="panel-copy">
              <span className="beat-kicker">03 · Engineering pressure</span>
              <h2 id="beat-three-title">Skills and rules help. They do not remove the work.</h2>
              <p>Developer skills and rules increase productivity, but people still have to implement changes and review millions of lines of code.</p>
            </div>
            <ModusWcCard className="pressure-card" bordered padding="compact">
              <span slot="title">The bottleneck moved</span>
              <span slot="subtitle">Faster generation creates a larger review surface.</span>
              <div className="pressure-metrics">
                <div><strong>↑</strong><span>More generated code</span></div>
                <div><strong>→</strong><span>Same human context</span></div>
                <div><strong>!</strong><span>More coordination pressure</span></div>
              </div>
            </ModusWcCard>
          </div>
          <DeliveryPipelineMap />
        </section>

        <section className="story-panel story-panel-graph" aria-labelledby="beat-four-title">
          <div className="graph-intro">
            <span className="beat-kicker">04 · Expand the loop</span>
            <h2 id="beat-four-title">The answer is not another faster part.</h2>
            <p>Expand the workflow across Product and Design, then connect every handoff to a repeatable automation.</p>
          </div>
          <WorkflowGraph variant="sheet" progress={1} initialSelectedId="intake" />
        </section>

        <section className="story-panel story-panel-graph" aria-labelledby="beat-five-title">
          <div className="graph-intro">
            <span className="beat-kicker">05 · Engineering loop</span>
            <h2 id="beat-five-title">Dev, QA, and PR runs you can open.</h2>
            <p>
              Click a sub-node (<strong>Automation</strong> or <strong>Run</strong>) to open Cursor in a new tab. Select the main
              node for context—the sheet pilot human gate stays on beat 04.
            </p>
          </div>
          <WorkflowGraph variant="engineering" progress={1} initialSelectedId="dev" />
        </section>
      </div>

      <LegendBar
        activeBeat={activeBeat}
        onJump={jumpToBeat}
        reducedMotion={reducedMotion}
        onToggleMotion={() => setReducedMotion((current) => !current)}
      />
    </main>
  );
}
