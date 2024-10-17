import hypothesis from 'eslint-config-hypothesis';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: [
      '.tox/**/*',
      '.yalc/**/*',
      '.yarn/**/*',
      'build/**/*',
      '**/vendor/**/*.js',
      '**/coverage/**/*',
      'docs/_build/*',
    ],
  },
  ...hypothesis,
  ...tseslint.configs.recommended,
  jsxA11y.flatConfigs.recommended,
  {
    rules: {
      'prefer-arrow-callback': 'error',
      'prefer-const': ['error', { destructuring: 'all' }],
    },
  },

  {
    files: ['*.js'],
    ignores: ['h/**'],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },
);
