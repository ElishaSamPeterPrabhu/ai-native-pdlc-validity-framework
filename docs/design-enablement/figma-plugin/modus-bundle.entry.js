import styles from '@trimble-oss/moduswebcomponents/modus-wc-styles.css';
import { defineCustomElements } from '@trimble-oss/moduswebcomponents/loader';

const style = document.createElement('style');
style.textContent = styles;
document.head.append(style);

defineCustomElements()
  .then(() => {
    window.dispatchEvent(new Event('modus-capability-ui-ready'));
  })
  .catch((error) => {
    console.error('Modus custom-element bootstrap failed', error);
    window.dispatchEvent(
      new CustomEvent('modus-capability-ui-error', { detail: String(error) }),
    );
  });
