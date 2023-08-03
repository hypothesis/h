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
    plugins: [
      babel({
        babelHelpers: 'bundled',
        exclude: 'node_modules/**',
      }),
      nodeResolve(),
      commonjs(),
      ...prodPlugins,
    ],
  };
}

export default [
  // Public-facing website
  bundleConfig('site', 'h/static/scripts/site.js'),
  // Admin areas of the site
  bundleConfig('admin-site', 'h/static/scripts/admin-site.js'),
  // Header script inserted inline at the top of the page
  bundleConfig('header', 'h/static/scripts/header.js'),
  // Helper script for the OAuth post-authorization page.
  bundleConfig('post-auth', 'h/static/scripts/post-auth.js'),
];
