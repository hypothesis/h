'use strict';

var angular = require('angular');

var annotationThread = require('../annotation-thread');
var util = require('./util');

describe('annotationThread', function () {
  before(function () {
    angular.module('app', [])
      .directive('annotationThread', annotationThread);
  });

  beforeEach(function () {
    angular.mock.module('app');
    angular.mock.module('h.templates');
  });

  it('renders the tree structure of parent and child annotations', function () {
    var directive = util.createDirective('annotationThread', {
      thread: {
        annotation: {
          id: '1',
          text: 'text',
        },
        children: [{
          annotation: {
            id: '2',
            text: 'areply',
          },
          children: [],
        }],
        visible: true,
      },
    });
    var annotations = directive[0].querySelector('annotation');
    assert.equal(annotations.length, 2);
  });

  // it('does not render threads that contain no visible children')
  // it('renders threads which contain a visible child')
  // it('passes the reply count to the annotation')
  // it('hides collapsed annotation threads')
  // it('shows expanded annotation threads')
  // it('invokes toggle function when replies are toggled')
});
