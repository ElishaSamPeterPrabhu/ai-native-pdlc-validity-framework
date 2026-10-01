import '@trimble-oss/moduswebcomponents/modus-wc-styles.css';
import { defineCustomElements } from '@trimble-oss/moduswebcomponents/loader';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RollingTrack3DPrototype } from './prototype/RollingTrack3DPrototype';
import './prototype/prototype.css';

defineCustomElements();

createRoot(document.getElementById('rolling-3d-root')!).render(
  <StrictMode>
    <RollingTrack3DPrototype />
  </StrictMode>,
);
