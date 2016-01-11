'use strict';

var Controller = require('../sidebar-tutorial').Controller;

describe('SidebarTutorialController', function () {

  describe('showSidebarTutorial', function () {
    it('returns true if show_sidebar_tutorial is true', function () {
      var session = {
        state: {
          preferences: {
            show_sidebar_tutorial: true
          }
        }
      };
      var controller = new Controller(session);

      var result = controller.showSidebarTutorial();

      assert.equal(result, true);
    });

    it('returns false if show_sidebar_tutorial is false', function () {
      var session = {
        state: {
          preferences: {
            show_sidebar_tutorial: false
          }
        }
      };
      var controller = new Controller(session);

      var result = controller.showSidebarTutorial();

      assert.equal(result, false);
    });

    it('returns false if show_sidebar_tutorial is missing', function () {
      var session = {state: {preferences: {}}};
      var controller = new Controller(session);

      var result = controller.showSidebarTutorial();

      assert.equal(result, false);
    });

    it('returns false if session.state is {}', function () {
      var session = {state: {}};
      var controller = new Controller(session);

      var result = controller.showSidebarTutorial();

      assert.equal(result, false);
    });
  });
});
