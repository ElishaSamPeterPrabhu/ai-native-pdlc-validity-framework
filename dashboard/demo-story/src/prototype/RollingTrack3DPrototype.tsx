import { ModusWcButton, ModusWcCard } from '@trimble-oss/moduswebcomponents-react';
import { useState } from 'react';
import { RollingTrack3DScene } from './RollingTrack3DScene';
import { rampConfigs, type MarbleRunVariant } from './rolling-track-3d';

export function RollingTrack3DPrototype() {
  const [variant, setVariant] = useState<MarbleRunVariant>('coupled');
  const [reducedMotion, setReducedMotion] = useState(false);

  return (
    <main className="prototype-shell">
      <header className="prototype-header">
        <div>
          <p className="prototype-eyebrow">Prototype · beats 01–02</p>
          <h1>3D marble-run</h1>
          <p>Three steps pass the work forward into the User bucket. AI boost tilts the track and accelerates Engineering.</p>
        </div>
        <a href="./index.html">Back to main demo story</a>
      </header>

      <div className="prototype-controls" aria-label="Prototype controls">
        <ModusWcButton color={variant === 'coupled' ? 'primary' : 'secondary'} variant="filled" onButtonClick={() => setVariant('coupled')}>
          Coupled
        </ModusWcButton>
        <ModusWcButton color={variant === 'aiBoost' ? 'primary' : 'secondary'} variant="filled" onButtonClick={() => setVariant('aiBoost')}>
          AI boost
        </ModusWcButton>
        <ModusWcButton color="secondary" variant="outlined" onButtonClick={() => setReducedMotion((current) => !current)}>
          {reducedMotion ? 'Enable motion' : 'Reduced motion'}
        </ModusWcButton>
      </div>

      <ModusWcCard className="prototype-card" bordered padding="comfortable">
        <span slot="title">{variant === 'coupled' ? '01 · Coupled system' : '02 · AI as a catalyst'}</span>
        <span slot="subtitle">
          {variant === 'coupled' ? 'Similar tilt · equal cadence' : 'Steeper tilt · Engineering booster'}
        </span>
        <div className="prototype-canvas">
          <RollingTrack3DScene variant={variant} reducedMotion={reducedMotion} />
        </div>
        <div className="prototype-caption">
          {rampConfigs[variant].map((ramp) => (
            <span key={ramp.name} style={{ borderColor: ramp.color }}>
              {ramp.name} · {ramp.tilt.toFixed(2)} tilt
            </span>
          ))}
          {variant === 'aiBoost' ? <span className="prototype-booster">BOOST → User</span> : null}
        </div>
      </ModusWcCard>
    </main>
  );
}
