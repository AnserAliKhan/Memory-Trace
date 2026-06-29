/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas:  'var(--color-canvas)',
        surface: 'var(--color-surface)',
        raised:  'var(--color-raised)',
        border:  'var(--color-border)',
        'border-dim': 'var(--color-border-dim)',
        cream:   'var(--color-cream)',
        muted:   'var(--color-muted)',
        dim:     'var(--color-dim)',
        amber:   'var(--color-amber)',
        'amber-glow': 'var(--color-amber-glow)',
        'amber-dim': 'var(--color-amber-dim)',
        success: 'var(--color-success)',
        error:   'var(--color-error)',
      },
      fontFamily: {
        display: ['Inter', 'system-ui', 'sans-serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
        mono:    ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      spacing: {
        1: '4px',
        2: '8px',
        3: '12px',
        4: '16px',
        5: '20px',
        6: '24px',
        8: '32px',
        10: '40px',
        12: '48px',
        16: '64px',
        20: '80px',
        24: '96px',
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
        pill: '9999px',
      },
      maxWidth: {
        layout: '1100px',
      },
    },
  },
  plugins: [],
}