'use strict';

window.$ = window.jQuery = require('jquery');
require('bootstrap');

if (window.chrome !== undefined) {
  let elements = document.getElementsByClassName('unhide-in-chrome');
  let i;
  for (i = 0; i < elements.length; i++) {
    elements[i].classList.remove('hidden');
  }
  elements = document.getElementsByClassName('hide-in-chrome');
  for (i = 0; i < elements.length; i++) {
    elements[i].classList.add('hidden');
  }
}

const bookmarkletInstaller = document.getElementById('js-bookmarklet-install');
if (bookmarkletInstaller) {
  bookmarkletInstaller.addEventListener('click', (event) => {
    window.alert('Drag me to the bookmarks bar');
    event.preventDefault();
  });
}

const chromeextInstaller = document.getElementById('js-chrome-extension-install');
if (chromeextInstaller) {
  chromeextInstaller.addEventListener('click', (event) => {
    window.chrome.webstore.install();
    event.preventDefault();
  });
}

const viaForm = document.querySelector('.js-via-form');
if (viaForm) {
  viaForm.addEventListener('submit', (event) => {
    const url = event.target.elements.url.value;
    if (url !== '') {
      window.location.href = 'https://via.hypothes.is/' + url;
    }
    event.preventDefault();
  });
}
