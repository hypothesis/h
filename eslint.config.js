import hypothesisBase from 'eslint-config-hypothesis/base';
import hypothesisJSX from 'eslint-config-hypothesis/jsx';
import hypothesisTS from 'eslint-config-hypothesis/ts';
import { defineConfig, globalIgnores } from 'eslint/config';
import globals from 'globals';

export default defineConfig(
  globalIgnores([
    '.tox/**/*',
    '.yalc/**/*',
    '.yarn/**/*',
    'build/**/*',
    '**/vendor/**/*.js',
    '**/coverage/**/*',
    'docs/_build/*',
  ]),

  hypothesisBase,
  hypothesisJSX,
  hypothesisTS,

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
