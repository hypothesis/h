import * as modalFocus from '../../util/modal-focus';

describe('util/modal-focus', () => {
  // Elements inside the focus group
  let insideEls;
  // Element outside the focus group
  let outsideEl;
  let onFocusOut;
  let releaseFocus;

  beforeEach(() => {
    insideEls = [1, 2, 3].map(() => document.createElement('input'));
    insideEls.forEach(el => document.body.appendChild(el));

    outsideEl = document.createElement('input');
    document.body.appendChild(outsideEl);

    onFocusOut = sinon.stub();
    releaseFocus = modalFocus.trap(insideEls, onFocusOut);
  });

  afterEach(() => {
    insideEls.forEach(el => el.remove());
    releaseFocus();
  });

  describe('#trap', () => {
    it('does not invoke the callback when an element in the group is focused', () => {
      insideEls[0].focus();
      insideEls[1].focus();
      assert.notCalled(onFocusOut);
    });

    it('invokes the callback when an element outside the group is focused', () => {
      outsideEl.focus();
      assert.calledWith(onFocusOut, outsideEl);
    });

    it('does not prevent the focus change if the callback returns null', () => {
      onFocusOut.returns(null);
      outsideEl.focus();
      assert.equal(document.activeElement, outsideEl);
    });

    it('prevents a focus change if the callback returns an element', () => {
      onFocusOut.returns(insideEls[0]);
      outsideEl.focus();
      assert.equal(document.activeElement, insideEls[0]);
    });

    it('releases focus when returned function is called', () => {
      onFocusOut.returns(insideEls[0]);

      releaseFocus();
      outsideEl.focus();

      assert.notCalled(onFocusOut);
      assert.equal(document.activeElement, outsideEl);
    });
  });
});
