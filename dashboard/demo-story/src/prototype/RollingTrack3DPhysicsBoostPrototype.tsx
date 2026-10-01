import { ModusWcCard } from '@trimble-oss/moduswebcomponents-react';
import { RollingTrack3DPhysicsBoostScene } from './RollingTrack3DPhysicsBoostScene';

export function RollingTrack3DPhysicsBoostPrototype() {
  return (
    <main className="prototype-shell physics-boost-shell">
      <header className="prototype-header">
        <div>
          <p className="prototype-eyebrow">Physics experiment · accelerator layer</p>
          <h1>3D marble-run boost</h1>
          <p>Slower handoffs make the Engineering accelerator layer visible before it launches the ball toward User.</p>
        </div>
        <div className="prototype-links">
          <a href="./rolling-3d-physics.html">Base physics prototype</a>
          <a href="./index.html">Main demo story</a>
        </div>
      </header>
      <ModusWcCard className="prototype-card" bordered padding="comfortable">
        <span slot="title">AI accelerator test</span>
          <span slot="subtitle">Slow Product → Design → Engineering, then end-marker impulse</span>
        <div className="prototype-canvas physics-boost-canvas">
          <RollingTrack3DPhysicsBoostScene />
        </div>
        <div className="boost-legend">
          <span>Lower layers: slow physics</span>
          <span>Engineering end: accelerator</span>
          <span>Impulse: Engineering → User</span>
        </div>
      </ModusWcCard>
    </main>
  );
}
