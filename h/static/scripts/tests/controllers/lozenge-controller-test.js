'use strict';

const LozengeController = require('../../controllers/lozenge-controller');

describe('LozengeController', () => {
  let el;
  let opts;
  let lozengeEl;
  let lozengeContentEl;
  let lozengeDeleteEl;

  beforeEach(() => {
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

  it('creates a new lozenge inside the container provided', () => {
    assert.equal(lozengeContentEl.textContent, opts.content);
  });

  it('creates a new lozenge for a known named query term inside the container provided', () => {
    el = document.createElement('div');
    opts = {
      content: 'user:foo',
    };

    new LozengeController(el, opts);
    lozengeEl = el.querySelector('.js-lozenge');
    lozengeContentEl = lozengeEl.querySelector('.js-lozenge__content');
    const facetNameEl = lozengeContentEl.querySelector('.lozenge__facet-name');
    const facetValueEl = lozengeContentEl.querySelector('.lozenge__facet-value');

    assert.equal(facetNameEl.textContent, 'user');
    assert.equal(facetValueEl.textContent, 'foo');
  });

  it('does not create a new lozenge for named query term which is not known', () => {
    el = document.createElement('div');
    opts = {
      content: 'foo:bar',
    };

    new LozengeController(el, opts);
    lozengeEl = el.querySelector('.js-lozenge');
    lozengeContentEl = lozengeEl.querySelector('.js-lozenge__content');

    assert.isNull(lozengeContentEl.querySelector('.lozenge__facet-name'));
    assert.isNull(lozengeContentEl.querySelector('.lozenge__facet-value'));
    assert.equal(lozengeContentEl.textContent, opts.content);
  });

  it('removes the lozenge and executes the delete callback provided', () => {
    lozengeDeleteEl.dispatchEvent(new Event('mousedown'));
    assert(opts.deleteCallback.calledOnce);
    assert.isNull(el.querySelector('.js-lozenge'));
  });
});
