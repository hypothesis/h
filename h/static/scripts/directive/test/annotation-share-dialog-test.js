'use strict';

var angular = require('angular');

var util = require('./util');

describe('annotationShareDialog', function () {
  var element;

  function getCopyBtn() {
    return element.find('.annotation-share-dialog-link__btn');
  }

  before(function () {
    angular.module('app', [])
      .directive('annotationShareDialog',
        require('../annotation-share-dialog'));
  });

  beforeEach(function () {
    angular.mock.module('app');
  });

  describe('The annotation share dialog', function () {
    it('has class is-open set when it is open', function () {
      element = util.createDirective(document, 'annotationShareDialog', {
        isOpen: true
      });

      assert.isOk(element.find('.annotation-share-dialog').hasClass('is-open'));
    });

    it('does not have class is-open set when it is not open', function () {
      element = util.createDirective(document, 'annotationShareDialog', {
        isOpen: false
      });

      assert.isNotOk(element.find('.annotation-share-dialog').hasClass('is-open'));
    });
  });

  describe('vm.copyToClipboard()', function () {
    var stub;

    beforeEach(function () {
      stub = sinon.stub(document, 'execCommand');
      element = util.createDirective(document,
        'annotationShareDialog',
        {
          group: {
            name: 'Public',
            type: 'public',
            public: true
          },
          uri: 'fakeURI',
          isPrivate: false,
        }
      );
    });

    afterEach(function () {
      stub.restore();
    });

    it('sets success class on successful copy to clipboard', function () {
      var expectedMessage = 'Link copied to clipboard!';

      getCopyBtn().click();

      var actualMessage = element.find('.annotation-share-dialog-link__feedback').text();
      assert.isAbove(actualMessage.indexOf(expectedMessage), -1);
    });

    it('unsets success class after one second on successful copy to clipboard', function () {
      var clock = sinon.useFakeTimers();
      var expectedMessage = 'Link copied to clipboard!';

      getCopyBtn().click();

      clock.tick(1999);
      clock.restore();

      var actualMessage = element.find('.annotation-share-dialog-link__feedback').text();
      assert.isBelow(actualMessage.indexOf(expectedMessage), 0);
    });

    it('sets fail class on unsuccessful copy to clipboard', function () {
      stub.throws(new Error('An error'));
      var expectedMessage = 'Select and copy to share';

      getCopyBtn().click();

      var actualMessage = element.find('.annotation-share-dialog-link__feedback').text();
      assert.isAbove(actualMessage.indexOf(expectedMessage), -1);
    });
  });

  describe('The message when a user wants to share an annotation shows that the annotation', function () {

    it('is available to a group', function () {
      element = util.createDirective(document, 'annotationShareDialog', {
        group: {
          public: false
        },
        isPrivate: false
      });

      var actualMessage = element.find('.annotation-share-dialog-msg').text();
      var actualAudience = element.find('.annotation-share-dialog-msg__audience').text();
      var expectedMessage = 'Only group members will be able to view this annotation.';
      var expectedAudience = 'Group.';
      assert.isAbove(actualMessage.indexOf(expectedMessage), -1);
      assert.isAbove(actualAudience.indexOf(expectedAudience), -1);
    });

    it('is private', function () {
      element = util.createDirective(document, 'annotationShareDialog', {
        isPrivate: true
      });

      var actualMessage = element.find('.annotation-share-dialog-msg').text();
      var actualAudience = element.find('.annotation-share-dialog-msg__audience').text();
      var expectedMessage = 'No one else will be able to view this annotation.';
      var expectedAudience = 'Only me.';
      assert.isAbove(actualMessage.indexOf(expectedMessage), -1);
      assert.isAbove(actualAudience.indexOf(expectedAudience), -1);
    });
  });
});
