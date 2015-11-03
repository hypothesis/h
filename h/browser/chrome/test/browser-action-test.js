var assign = require('core-js/modules/$.object-assign');
var proxyquire = require('proxyquire');

describe('BrowserAction', function () {
  'use strict';

  var BrowserAction = require('../lib/browser-action');
  var TabState = require('../lib/tab-state');
  var action;
  var fakeChromeBrowserAction;

  beforeEach(function () {
    fakeChromeBrowserAction = {
      annotationCount: 0,
      title: '',
      badgeText: '',
      badgeColor: '',

      setIcon: function (options) {
        this.icon = options.path;
      },
      setTitle: function (options) {
        this.title = options.title;
      },
      setBadgeText: function (options) {
        this.badgeText = options.text;
      },
      setBadgeBackgroundColor: function (options) {
        this.badgeColor = options.color;
      }
    };
    action = new BrowserAction(fakeChromeBrowserAction);
  });

  describe('active state', function () {
    it('sets the active browser icon', function () {
      action.update(1, {state: TabState.states.ACTIVE});
      assert.equal(fakeChromeBrowserAction.icon, BrowserAction.icons[TabState.states.ACTIVE]);
    });

    it('sets the title of the browser icon', function () {
      action.update(1, {state: TabState.states.ACTIVE});
      assert.equal(fakeChromeBrowserAction.title, 'Hypothesis is active');
    });

    it('does not set the title if there is badge text showing', function () {
      var state = {
        state: TabState.states.INACTIVE,
        annotationCount: 9,
      };
      action.update(1, state);
      var prevTitle = fakeChromeBrowserAction.title;
      action.update(1, assign(state, {state: TabState.states.ACTIVE}));
      assert.equal(fakeChromeBrowserAction.title, prevTitle);
    });
  });

  describe('inactive state', function () {
    it('sets the inactive browser icon and title', function () {
      action.update(1, {state: TabState.states.INACTIVE});
      assert.equal(fakeChromeBrowserAction.icon, BrowserAction.icons[TabState.states.INACTIVE]);
      assert.equal(fakeChromeBrowserAction.title, 'Hypothesis is inactive');
    });
  });

  describe('error state', function () {
    it('sets the inactive browser icon', function () {
      action.update(1, {state: TabState.states.ERRORED});
      assert.equal(fakeChromeBrowserAction.icon, BrowserAction.icons[TabState.states.INACTIVE]);
    });

    it('sets the title of the browser icon', function () {
      action.update(1, {state: TabState.states.ERRORED});
      assert.equal(fakeChromeBrowserAction.title, 'Hypothesis failed to load');
    });

    it('still sets the title even there is badge text showing', function () {
      action.update(1, {
        state: TabState.states.ERRORED,
        annotationCount: 9,
      });
      assert.equal(fakeChromeBrowserAction.title, 'Hypothesis failed to load');
    });

    it('shows a badge', function () {
      action.update(1, {
        state: TabState.states.ERRORED,
      });
      assert.equal(fakeChromeBrowserAction.badgeText, '!');
    });
  });

  describe('annotation counts', function () {
    it("sets the badge text", function() {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 23,
      });
      assert.equal(fakeChromeBrowserAction.badgeText, '23');
    });

    it("sets the badge title when there's 1 annotation",
      function () {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 1,
      });
      assert.equal(fakeChromeBrowserAction.title,
        "There's 1 annotation on this page");
    });

    it("sets the badge title when there's >1 annotation",
        function() {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 23,
      });
      assert.equal(fakeChromeBrowserAction.title,
        "There are 23 annotations on this page");
    });

    it("does not set the badge text if there are 0 annotations", function() {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 0,
      });
      assert.equal(fakeChromeBrowserAction.badgeText, '');
    });

    it("does not set the badge title if there are 0 annotations", function() {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 0,
      });
      assert.equal(fakeChromeBrowserAction.title, 'Hypothesis is inactive');
    });

    it("truncates numbers greater than 999 to '999+'", function() {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 1001,
      });
      assert.equal(fakeChromeBrowserAction.badgeText, '999+');
      assert.equal(fakeChromeBrowserAction.title,
        'There are 999+ annotations on this page');
    });
  });

  describe('build type', function () {
    beforeEach(function () {
      var fakeSettings = Promise.resolve({
        buildType: 'staging',
        '@noCallThru': true,
      });
      var BrowserAction = proxyquire('../lib/browser-action', {
        './settings': fakeSettings,
      });
      action = new BrowserAction(fakeChromeBrowserAction);
      return fakeSettings;
    });

    it('sets the text to STG when there are no annotations', function () {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 0,
      });
      assert.equal(fakeChromeBrowserAction.badgeText, 'STG');
    });

    it('shows the annotation count when there are annotations', function () {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 3,
      });
      assert.equal(fakeChromeBrowserAction.badgeText, '3');
    });

    it('sets the background color', function () {
      action.update(1, {
        state: TabState.states.INACTIVE,
        annotationCount: 0,
      });
      assert.equal(fakeChromeBrowserAction.badgeColor, '#EDA061');
    });
  });
});
