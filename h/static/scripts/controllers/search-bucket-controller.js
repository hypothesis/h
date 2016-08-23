'use strict';

var scrollIntoView = require('scroll-into-view');

function SearchBucketController(element) {
  this.scrollTo = scrollIntoView;

  var header = element.querySelector('.js-header');
  var content = element.querySelector('.js-content');
  var self = this;

  header.addEventListener('click', function () {
    element.classList.toggle('is-expanded');
    content.classList.toggle('is-expanded');

    if (element.classList.contains('is-expanded')) {
      self.scrollTo(element);
    }
  });
}

module.exports = SearchBucketController;
