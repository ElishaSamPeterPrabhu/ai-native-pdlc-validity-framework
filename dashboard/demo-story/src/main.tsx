import '@trimble-oss/moduswebcomponents/modus-wc-styles.css';
import { defineCustomElements } from '@trimble-oss/moduswebcomponents/loader';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

defineCustomElements();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
