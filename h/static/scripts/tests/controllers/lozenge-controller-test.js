'use strict';

var LozengeController = require('../../controllers/lozenge-controller');

describe('LozengeController', function () {
  var el;
  var opts;
  var lozengeEl;
  var lozengeContentEl;
  var lozengeDeleteEl;

  beforeEach(function () {
    el = document.createElement('div');
    opts = {
      content: 'foo',
      deleteCallback: sinon.spy(),
    };

    new LozengeController(el, opts);
    lozengeEl = el.querySelector('.js-lozenge');
    lozengeContentEl = lozengeEl.querySelector('.js-lozenge__content');
    lozengeDeleteEl = lozengeEl.querySelector('.js-lozenge__close');
  });

  it('creates a new lozenge inside the container provided', function () {
    assert.equal(lozengeContentEl.textContent, opts.content);
  });

  it('removes the lozenge and executes the delete callback provided', function () {
    lozengeDeleteEl.dispatchEvent(new Event('mousedown'));
    assert(opts.deleteCallback.calledOnce);
    assert.isNull(el.querySelector('.js-lozenge'));
  });
});
