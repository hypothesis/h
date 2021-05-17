'use strict';

const EnvironmentFlags = require('../../base/environment-flags');

const TIMEOUT_DELAY = 10000;

describe('EnvironmentFlags', () => {
  let clock;
  let el;
  let flags;

  beforeEach(() => {
    el = document.createElement('div');
    flags = new EnvironmentFlags(el);
    clock = sinon.useFakeTimers();
  });

  afterEach(() => {
    clock.restore();
  });

  describe('#init', () => {
    it('should mark document as JS capable on load', () => {
      flags.init();
      assert.isTrue(el.classList.contains('env-js-capable'));
    });

    it('should mark JS load as failed after a timeout', () => {
      flags.init();
      clock.tick(TIMEOUT_DELAY);
      assert.isTrue(el.classList.contains('env-js-timeout'));
    });

    it('should not add "env-touch" flag if touch events are not supported', () => {
      flags.init();
      assert.isFalse(el.classList.contains('env-touch'));
    });

    it('should add "env-touch" flag if touch events are available', () => {
      el.ontouchstart = function () {};
      flags.init();
      assert.isTrue(el.classList.contains('env-touch'));
    });

    it('should add flags specified in the document URL', () => {
      flags.init('http://example.org/?__env__=touch;js-timeout');
      assert.isTrue(el.classList.contains('env-touch'));
      assert.isTrue(el.classList.contains('env-js-timeout'));
    });

    it('should remove flags with a "no-" prefix specified in the document URL', () => {
      flags.init('http://example.org/?__env__=no-js-capable');
      assert.isFalse(el.classList.contains('env-js-capable'));
    });

    it('should remove "js-capable" flag if "nojs=1" is present in URL', () => {
      flags.init('http://example.org/?nojs=1');
      assert.isFalse(el.classList.contains('env-js-capable'));
    });
  });

  describe('#ready', () => {
    it('should prevent JS load timeout flag from being set', () => {
      flags.init();
      flags.ready();
      clock.tick(TIMEOUT_DELAY);
      assert.isFalse(el.classList.contains('env-js-timeout'));
    });

    it('should not clear timeout flag if already set', () => {
      flags.init();
      clock.tick(TIMEOUT_DELAY);
      flags.ready();
      assert.isTrue(el.classList.contains('env-js-timeout'));
    });
  });

  describe('#set', () => {
    it('should add a flag if `on` is true', () => {
      flags.set('shiny-feature', true);
      assert.isTrue(el.classList.contains('env-shiny-feature'));
    });

    it('should remove a flag if `on` is false', () => {
      flags.set('shiny-feature', false);
      assert.isFalse(el.classList.contains('env-shiny-feature'));
    });
  });

  describe('#get', () => {
    it('should return true if the flag is set', () => {
      flags.set('shiny-feature', true);
      assert.isTrue(flags.get('shiny-feature'));
    });

    it('should return false if the flag is set', () => {
      assert.isFalse(flags.get('shiny-feature'));
    });
  });
});
