'use strict';

function SearchBucketController(element) {
  var header = element.querySelector('.js-header');
  var content = element.querySelector('.js-content');

  header.addEventListener('click', function () {
    element.classList.toggle('is-expanded');
    content.classList.toggle('is-expanded');
  });
}

module.exports = SearchBucketController;
