'use strict';

function saveOptions() {
  chrome.storage.sync.set({
    badge: document.getElementById('badge').checked,
  });
}

function loadOptions() {
  chrome.storage.sync.get({
    badge: true,
  }, function(items) {
    document.getElementById('badge').checked = items.badge;
  });
}

document.addEventListener('DOMContentLoaded', loadOptions);
document.getElementById('badge').addEventListener('click', saveOptions);
