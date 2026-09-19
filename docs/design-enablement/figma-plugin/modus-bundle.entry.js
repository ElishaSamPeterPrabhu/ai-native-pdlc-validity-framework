import styles from '@trimble-oss/moduswebcomponents/modus-wc-styles.css';
import { defineCustomElement as defineAlert } from '@trimble-oss/moduswebcomponents/components/modus-wc-alert.js';
import { defineCustomElement as defineButton } from '@trimble-oss/moduswebcomponents/components/modus-wc-button.js';
import { defineCustomElement as defineCard } from '@trimble-oss/moduswebcomponents/components/modus-wc-card.js';
import { defineCustomElement as defineTextInput } from '@trimble-oss/moduswebcomponents/components/modus-wc-text-input.js';
import { defineCustomElement as defineTypography } from '@trimble-oss/moduswebcomponents/components/modus-wc-typography.js';

const style = document.createElement('style');
style.textContent = styles;
document.head.append(style);

try {
  [
    defineAlert,
    defineButton,
    defineCard,
    defineTextInput,
    defineTypography,
  ].forEach((defineCustomElement) => {
    defineCustomElement();
  });
  window.dispatchEvent(new Event('modus-capability-ui-ready'));
} catch (error) {
    console.error('Modus custom-element bootstrap failed', error);
    window.dispatchEvent(
      new CustomEvent('modus-capability-ui-error', { detail: String(error) }),
    );
}
