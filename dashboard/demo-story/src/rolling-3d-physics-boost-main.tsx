import '@trimble-oss/moduswebcomponents/modus-wc-styles.css';
import { defineCustomElements } from '@trimble-oss/moduswebcomponents/loader';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RollingTrack3DPhysicsBoostPrototype } from './prototype/RollingTrack3DPhysicsBoostPrototype';
import './prototype/prototype.css';
import './prototype/physics-boost.css';

defineCustomElements();

createRoot(document.getElementById('rolling-3d-physics-boost-root')!).render(
  <StrictMode>
    <RollingTrack3DPhysicsBoostPrototype />
  </StrictMode>,
);
