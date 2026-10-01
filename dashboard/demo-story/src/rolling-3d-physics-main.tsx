import '@trimble-oss/moduswebcomponents/modus-wc-styles.css';
import { defineCustomElements } from '@trimble-oss/moduswebcomponents/loader';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RollingTrack3DPhysicsPrototype } from './prototype/RollingTrack3DPhysicsPrototype';
import './prototype/prototype.css';

defineCustomElements();

createRoot(document.getElementById('rolling-3d-physics-root')!).render(
  <StrictMode>
    <RollingTrack3DPhysicsPrototype />
  </StrictMode>,
);
