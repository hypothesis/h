import { babel } from '@rollup/plugin-babel';
import commonjs from '@rollup/plugin-commonjs';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import terser from '@rollup/plugin-terser';

const isProd = process.env.NODE_ENV === 'production';
const prodPlugins = [];
if (isProd) {
  prodPlugins.push(terser());
}

function bundleConfig(name, entryFile) {
  return {
    input: {
      [name]: entryFile,
    },
    output: {
      dir: 'build/scripts/',
      format: 'es',
      chunkFileNames: '[name].bundle.js',
      entryFileNames: '[name].bundle.js',
    },

    // Suppress a warning (https://rollupjs.org/guide/en/#error-this-is-undefined)
    // due to https://github.com/babel/babel/issues/9149.
    //
    // Any code string other than "undefined" which evaluates to `undefined` will work here.
    context: 'void(0)',

    plugins: [
      babel({
        babelHelpers: 'bundled',
        exclude: 'node_modules/**',
        extensions: ['.js', '.ts', '.tsx'],
      }),
      nodeResolve({
        extensions: ['.js', '.ts', '.tsx'],
      }),
      commonjs(),
      ...prodPlugins,
    ],
  };
}

export default [
  // Public-facing website
  bundleConfig('site', 'h/static/scripts/site.js'),
  // Preact app for creating new private groups.
  bundleConfig('group-forms', 'h/static/scripts/group-forms/index.tsx'),
  // Admin areas of the site
  bundleConfig('admin-site', 'h/static/scripts/admin-site.js'),
  // Header script inserted inline at the top of the page
  bundleConfig('header', 'h/static/scripts/header.js'),
  // Helper script for the OAuth post-authorization page.
  bundleConfig('post-auth', 'h/static/scripts/post-auth.js'),
];
