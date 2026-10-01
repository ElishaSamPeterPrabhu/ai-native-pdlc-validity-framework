/// <reference types="vite/client" />

declare namespace JSX {
  interface IntrinsicElements {
    'modus-wc-stepper': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
      steps?: unknown;
      orientation?: string;
    };
  }
}
