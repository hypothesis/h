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
      stub = sinon.stub(document, 'execCommand').returns(true);
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

    it('displays message after successful copy', function () {
      var expectedMessage = 'Link copied to clipboard!';

      getCopyBtn().click();

      var actualMessage = element.find('.annotation-share-dialog-link__feedback').text();
      assert.include(actualMessage, expectedMessage);
    });

    it('hides message after a delay after a successful copy', function () {
      var clock = sinon.useFakeTimers();
      var expectedMessage = 'Link copied to clipboard!';

      getCopyBtn().click();

      clock.tick(1999);
      clock.restore();

      var actualMessage = element.find('.annotation-share-dialog-link__feedback').text();
      assert.notInclude(actualMessage, expectedMessage);
    });

    it('displays message after failed copy', function () {
      stub.returns(false);
      var expectedMessage = 'Select and copy to share';

      getCopyBtn().click();

      var actualMessage = element.find('.annotation-share-dialog-link__feedback').text();
      assert.include(actualMessage, expectedMessage);
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
      assert.include(actualMessage, expectedMessage);
      assert.include(actualAudience, expectedAudience);
    });

    it('is private', function () {
      element = util.createDirective(document, 'annotationShareDialog', {
        isPrivate: true
      });

      var actualMessage = element.find('.annotation-share-dialog-msg').text();
      var actualAudience = element.find('.annotation-share-dialog-msg__audience').text();
      var expectedMessage = 'No one else will be able to view this annotation.';
      var expectedAudience = 'Only me.';
      assert.include(actualMessage, expectedMessage);
      assert.include(actualAudience, expectedAudience);
    });
  });
});
