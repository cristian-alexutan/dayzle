import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

/** PrimeVue's Aura theme using the app's colors, which are defined in styles/theme.css. */
export const DayzlePreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#f3f9f3',
      100: '#e2f1e1',
      200: '#c6e3c5',
      300: '#9ed39c',
      400: '#84c282',
      500: '#6fa96e',
      600: '#5a8e5a',
      700: '#487148',
      800: '#3a5a3a',
      900: '#2f4a30',
      950: '#192a1a',
      color: 'var(--dz-primary)',
      contrastColor: 'var(--dz-on-primary)',
      hoverColor: 'var(--dz-primary-hover)',
      activeColor: 'var(--dz-primary-active)',
    },
    content: {
      background: 'var(--dz-surface)',
      borderColor: 'var(--dz-border)',
      color: 'var(--dz-text)',
    },
    text: {
      color: 'var(--dz-text)',
      mutedColor: 'var(--dz-text-muted)',
    },
    overlay: {
      modal: {
        background: 'var(--dz-surface)',
        borderColor: 'var(--dz-border)',
        color: 'var(--dz-text)',
      },
    },
  },
})
