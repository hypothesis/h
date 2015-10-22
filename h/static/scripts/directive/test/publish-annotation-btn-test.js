'use strict';

var util = require('./util');

var fakeStorage = {};
var fakeLocalStorage = {
  setItem: function (key, value) {
    fakeStorage[key] = value;
  },
  getItem: function (key) {
    return fakeStorage[key];
  }
};

describe('publishAnnotationBtn', function () {
  before(function () {
    angular.module('app', [])
      .directive('dropdownMenuBtn', require('../dropdown-menu-btn'))
      .directive('publishAnnotationBtn', require('../publish-annotation-btn'))
      .factory('localStorage', function () {
        return fakeLocalStorage;
      });
  });

  var element;

  beforeEach(function () {
    angular.mock.module('app');
    angular.mock.module('h.templates');

    // create a new instance of the directive with default
    // attributes
    element = util.createDirective(document, 'publishAnnotationBtn', {
     group: {
       name: 'Public',
       type: 'public'
     },
     canPost: true,
     isShared: false,
     onSave: function () {},
     onSetPrivacy: function (level) {},
     onCancel: function () {}
   });
  });

  it('should display "Post to Only Me"', function () {
    var buttons = element.find('button');
    assert.equal(buttons.length, 3);
    assert.equal(buttons[0].innerHTML, 'Post to Only Me');
  });

  it('should display "Post to Research Lab"', function () {
    element.link({
      group: {
        name: 'Research Lab',
        type: 'group'
      },
      isShared: true
    })
    var buttons = element.find('button');
    assert.equal(buttons[0].innerHTML, 'Post to Research Lab');
  });

  it('should save when "Post..." is clicked', function () {
    var savedSpy = sinon.spy();
    element.link({
      onSave: savedSpy
    });
    assert.ok(!savedSpy.called);
    angular.element(element.find('button')[0]).click();
    assert.ok(savedSpy.calledOnce);
  });

  it('should change privacy when privacy option selected', function () {
    var privacyChangedSpy = sinon.spy();
    element.link({
      // for existing annotations, the privacy should not be changed
      // unless the user makes a choice from the list
      onSetPrivacy: privacyChangedSpy
    });

    assert.ok(!privacyChangedSpy.called);
    var privateOption = element.find('li')[1];
    var sharedOption = element.find('li')[0];
    angular.element(privateOption).click();
    assert.equal(privacyChangedSpy.callCount, 1);
    angular.element(sharedOption).click();
    assert.equal(privacyChangedSpy.callCount, 2);
  });

  it('should disable post buttons when posting is not possible', function () {
    element.link({
      canPost: false
    });
    var disabledBtns = element.find('button[disabled]');
    assert.equal(disabledBtns.length, 1);

    // check that buttons are enabled when posting is possible
    element.link({
      canPost: true
    });
    disabledBtns = element.find('button[disabled]');
    assert.equal(disabledBtns.length, 0);
  });

  it('should revert changes when cancel is clicked', function () {
    var cancelSpy = sinon.spy();
    element.link({
      onCancel: cancelSpy
    });
    var cancelBtn = element.find('.publish-annotation-cancel-btn');
    assert.equal(cancelBtn.length, 1);
    angular.element(cancelBtn).click();
    assert.equal(cancelSpy.callCount, 1);
  });

});
