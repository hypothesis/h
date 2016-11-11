'use strict';

window.$ = window.jQuery = require('jquery');
require('bootstrap');

if (window.chrome !== undefined) {
  var elements = document.getElementsByClassName('unhide-in-chrome');
  var i;
  for (i = 0; i < elements.length; i++) {
    elements[i].classList.remove('hidden');
  }
  elements = document.getElementsByClassName('hide-in-chrome');
  for (i = 0; i < elements.length; i++) {
    elements[i].classList.add('hidden');
  }
}

var bookmarkletInstaller = document.getElementById('js-bookmarklet-install');
if (bookmarkletInstaller) {
  bookmarkletInstaller.addEventListener('click', (event) => {
    window.alert('Drag me to the bookmarks bar');
    event.preventDefault();
  });
}

var chromeextInstaller = document.getElementById('js-chrome-extension-install');
if (chromeextInstaller) {
  chromeextInstaller.addEventListener('click', (event) => {
    window.chrome.webstore.install();
    event.preventDefault();
  });
}
