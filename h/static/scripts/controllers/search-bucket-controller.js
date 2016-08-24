'use strict';

var inherits = require('inherits');
var scrollIntoView = require('scroll-into-view');

var Controller = require('../base/controller');
var setElementState = require('../util/dom').setElementState;

function SearchBucketController(element) {
  Controller.call(this, element);

  this.scrollTo = scrollIntoView;
  var self = this;

  this.refs.header.addEventListener('click', function () {
    self.setState({expanded: !self.state.expanded});
  });
}
inherits(SearchBucketController, Controller);

SearchBucketController.prototype.update = function (state) {
  setElementState(this.refs.content, {expanded: state.expanded});
  setElementState(this.refs.header, {expanded: state.expanded});

  if (state.expanded) {
    this.scrollTo(this.element);
  }
};

module.exports = SearchBucketController;
