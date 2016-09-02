'use strict';

var scrollIntoView = require('scroll-into-view');

var Controller = require('../base/controller');
var setElementState = require('../util/dom').setElementState;

class SearchBucketController extends Controller {
  constructor(element) {
    super(element);

    this.scrollTo = scrollIntoView;

    this.refs.header.addEventListener('click', () => {
      this.setState({expanded: !this.state.expanded});
    });
  }

  update(state) {
    setElementState(this.refs.content, {expanded: state.expanded});
    setElementState(this.refs.header, {expanded: state.expanded});

    if (state.expanded) {
      this.scrollTo(this.element);
    }
  }
}

module.exports = SearchBucketController;
