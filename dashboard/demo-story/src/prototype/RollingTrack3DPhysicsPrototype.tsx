import { ModusWcCard } from '@trimble-oss/moduswebcomponents-react';
import { RollingTrack3DPhysicsScene } from './RollingTrack3DPhysicsScene';

export function RollingTrack3DPhysicsPrototype() {
  return (
    <main className="prototype-shell">
      <header className="prototype-header">
        <div>
          <p className="prototype-eyebrow">Physics experiment · separate page</p>
          <h1>3D marble-run physics</h1>
          <p>Product starts the descending staircase, Design is tilted, and gravity drives the ball into the User bucket.</p>
        </div>
        <div className="prototype-links">
          <a href="./rolling-3d.html">Cinematic prototype</a>
          <a href="./index.html">Main demo story</a>
        </div>
      </header>
      <ModusWcCard className="prototype-card" bordered padding="comfortable">
        <span slot="title">Physics test</span>
        <span slot="subtitle">Real gravity, friction, restitution, and fixed ramp colliders</span>
        <div className="prototype-canvas">
          <RollingTrack3DPhysicsScene />
        </div>
        <p className="prototype-note">The ball resets after it reaches the bucket or falls off the track. Drag to inspect the ramp angles.</p>
      </ModusWcCard>
    </main>
  );
}
