'use strict';

function page(path, callback) {
  if (window.location.pathname === path) {
    document.addEventListener('DOMContentLoaded', callback, false);
  }
}

module.exports = page;
