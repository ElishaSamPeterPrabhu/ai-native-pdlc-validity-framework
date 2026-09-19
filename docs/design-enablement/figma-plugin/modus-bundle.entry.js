import styles from '@trimble-oss/moduswebcomponents/modus-wc-styles.css';
import { defineCustomElements } from '@trimble-oss/moduswebcomponents/loader';

const style = document.createElement('style');
style.textContent = styles;
document.head.append(style);

defineCustomElements();
