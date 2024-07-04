import tailwindConfig from '@hypothesis/frontend-shared/lib/tailwind.preset.js';

export default {
  presets: [tailwindConfig],
  content: [
    './h/static/scripts/**/*.{js,ts,tsx}',
    './node_modules/@hypothesis/frontend-shared/lib/**/*.js',
  ],
  theme: {
    extend: {
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
    },
  },
};
