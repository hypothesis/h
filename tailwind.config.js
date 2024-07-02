import tailwindConfig from '@hypothesis/frontend-shared/lib/tailwind.preset.js';

export default {
  presets: [tailwindConfig],
  content: [
    './h/static/scripts/**/*.{js,ts,tsx}',
    './node_modules/@hypothesis/frontend-shared/lib/**/*.js',
  ],
  theme: {
    extend: {
      animation: {
        'fade-in': 'fade-in 0.3s forwards',
        'fade-out': 'fade-out 0.3s forwards',
        'slide-in-from-right': 'slide-in-from-right 0.3s forwards ease-in-out',
      },
      fontFamily: {
        sans: [
          '"Helvetica Neue"',
          'Helvetica',
          'Arial',
          '"Lucida Grande"',
          'sans-serif',
        ],
      },
      boxShadow: {
        // Similar to tailwind's default `shadow-inner` but coming from the
        // right edge instead of the left
        'r-inner': 'inset -2px 0 4px 0 rgb(0,0,0,.05)',
      },
      keyframes: {
        'fade-in': {
          '0%': {
            opacity: '0',
          },
          '100%': {
            opacity: '1',
          },
        },
        'fade-out': {
          '0%': {
            opacity: '1',
          },
          '100%': {
            opacity: '0',
          },
        },
        'slide-in-from-right': {
          '0%': {
            opacity: '0',
            left: '100%',
          },
          '80%': {
            left: '-10px',
          },
          '100%': {
            left: '0',
            opacity: '1',
          },
        },
      },
    },
  },
};
