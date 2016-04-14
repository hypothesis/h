'use strict';

var angular = require('angular');

var util = require('./util');

describe('shareDialog', function () {
  var fakeCrossFrame;

  before(function () {
    angular.module('h', [])
      .directive('shareDialog', require('../share-dialog'));
  });

  beforeEach(angular.mock.module('h'));

  beforeEach(angular.mock.module(function ($provide) {
    fakeCrossFrame = { frames: [] };
    $provide.value('crossframe', fakeCrossFrame);
  }));

  it('generates new via link', function () {
    var element = util.createDirective(document, 'shareDialog', {});
    fakeCrossFrame.frames.push({ uri: 'http://example.com' });
    element.scope.$digest();
    assert.equal(element.ctrl.viaPageLink, 'https://via.hypothes.is/http://example.com');
  });

  it('does not generate new via link if already on via', function () {
    var element = util.createDirective(document, 'shareDialog', {});
    fakeCrossFrame.frames.push({ uri: 'https://via.hypothes.is/http://example.com' });
    element.scope.$digest();
    assert.equal(element.ctrl.viaPageLink, 'https://via.hypothes.is/http://example.com');
  });
});
