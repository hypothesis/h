'use strict';

const LozengeController = require('../../controllers/lozenge-controller');
const lozengeTemplate = require('./lozenge-template');
const { setupComponent } = require('./util');

describe('LozengeController', () => {
  function createLozenge(content) {
    return setupComponent(document, lozengeTemplate, LozengeController, {
      content,
      deleteCallback: sinon.spy(),
    });
  }

  it('displays the facet name and value for recognized facets', () => {
    const ctrl = createLozenge('user:foo');
    assert.equal(ctrl.refs.facetName.textContent, 'user:');
    assert.equal(ctrl.refs.facetValue.textContent, 'foo');
  });

  it('does not create a new lozenge for named query term which is not known', () => {
    const ctrl = createLozenge('foo:bar');
    assert.equal(ctrl.refs.facetName.textContent, '');
    assert.equal(ctrl.refs.facetValue.textContent, 'foo:bar');
  });

  it('removes the lozenge and executes the delete callback provided', () => {
    const ctrl = createLozenge('deleteme');
    ctrl.refs.deleteButton.dispatchEvent(new Event('click'));
    assert.calledOnce(ctrl.options.deleteCallback);
  });
});
