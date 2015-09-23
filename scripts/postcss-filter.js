#!/usr/bin/env node

// post-process CSS using PostCSS
// (https://github.com/postcss/postcss)
//
// This adds vendor prefixes using autoprefixer
// https://github.com/postcss/autoprefixer

require('es6-promise').polyfill();

var autoprefixer = require('autoprefixer');
var postcss = require('postcss');

var inputCss = '';

process.stdin.on('data', function (chunk) {
  inputCss += chunk;
});

process.stdin.on('end', function () {
  postcss([autoprefixer])
    .process(inputCss)
    .then(function (result) {
      console.log(result.css);
    });
});

