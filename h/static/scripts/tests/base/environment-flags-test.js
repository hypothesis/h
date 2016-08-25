'use strict';

var EnvironmentFlags = require('../../base/environment-flags');

var TIMEOUT_DELAY = 10000;

describe('EnvironmentFlags', function () {
  var clock;
  var el;
  var flags;

  beforeEach(function () {
    el = document.createElement('div');
    flags = new EnvironmentFlags(el);
    clock = sinon.useFakeTimers();
  });

  afterEach(function () {
    clock.restore();
  });

  describe('#init', function () {
    it('should mark document as JS capable on load', function () {
      flags.init();
      assert.isTrue(el.classList.contains('env-js-capable'));
    });

    it('should mark JS load as failed after a timeout', function () {
      flags.init();
      clock.tick(TIMEOUT_DELAY);
      assert.isTrue(el.classList.contains('env-js-timeout'));
    });

    it('should not add "env-touch" flag if touch events are not supported', function () {
      flags.init();
      assert.isFalse(el.classList.contains('env-touch'));
    });

    it('should add "env-touch" flag if touch events are available', function () {
      el.ontouchstart = function () {};
      flags.init();
      assert.isTrue(el.classList.contains('env-touch'));
    });

    it('should add flags specified in the document URL', function () {
      flags.init('http://example.org/?__env__=touch;js-timeout');
      assert.isTrue(el.classList.contains('env-touch'));
      assert.isTrue(el.classList.contains('env-js-timeout'));
    });

    it('should remove flags with a "no-" prefix specified in the document URL', function () {
      flags.init('http://example.org/?__env__=no-js-capable');
      assert.isFalse(el.classList.contains('env-js-capable'));
    });

    it('should remove "js-capable" flag if "nojs=1" is present in URL', function () {
      flags.init('http://example.org/?nojs=1');
      assert.isFalse(el.classList.contains('env-js-capable'));
    });
  });

  describe('#ready', function () {
    it('should prevent JS load timeout flag from being set', function () {
      flags.init();
      flags.ready();
      clock.tick(TIMEOUT_DELAY);
      assert.isFalse(el.classList.contains('env-js-timeout'));
    });

    it('should not clear timeout flag if already set', function () {
      flags.init();
      clock.tick(TIMEOUT_DELAY);
      flags.ready();
      assert.isTrue(el.classList.contains('env-js-timeout'));
    });
  });

  describe('#set', function () {
    it('should add a flag if `on` is true', function () {
      flags.set('shiny-feature', true);
      assert.isTrue(el.classList.contains('env-shiny-feature'));
    });

    it('should remove a flag if `on` is false', function () {
      flags.set('shiny-feature', false);
      assert.isFalse(el.classList.contains('env-shiny-feature'));
    });
  });

  describe('#get', function () {
    it('should return true if the flag is set', function () {
      flags.set('shiny-feature', true);
      assert.isTrue(flags.get('shiny-feature'));
    });

    it('should return false if the flag is set', function () {
      assert.isFalse(flags.get('shiny-feature'));
    });
  });
});
