// Focus release function returned by most recent call to trap()
let currentReleaseFn;

/**
 * Trap focus within a group of elements.
 *
 * Watch focus changes in a document and react to and/or prevent focus moving
 * outside a specified group of elements.
 *
 * @param {Element[]} elements - Array of elements which make up the modal group
 * @param {(Element) => Element|null} callback - Callback which is invoked when
 *        focus tries to move outside the modal group. It is called with the
 *        new element that will be focused. If it returns null, the focus change
 *        will proceed, otherwise if it returns an element within the group,
 *        that element will be focused instead.
 * @return {Function} A function which releases the modal focus, if it has not
 *        been changed by another call to trap() in the meantime.
 */
export function trap(elements, callback) {
  if (currentReleaseFn) {
    currentReleaseFn();
  }

  // The most obvious way of detecting an element losing focus and reacting
  // based on the new focused element is the "focusout" event and the
  // FocusEvent#relatedTarget property.
  //
  // However, FocusEvent#relatedTarget is not implemented in all browsers
  // (Firefox < 48, IE) and is null in some cases even for browsers that do
  // support it.
  //
  // Instead we watch the 'focus' event on the document itself.

  const onFocusChange = event => {
    if (elements.some(el => el.contains(event.target))) {
      // Focus remains within modal group
      return;
    }

    // Focus is trying to move outside of the modal group, test whether to
    // allow this
    const newTarget = callback(event.target);
    if (newTarget) {
      event.preventDefault();
      event.stopPropagation();
      newTarget.focus();
    } else if (currentReleaseFn) {
      currentReleaseFn();
    }
  };
  document.addEventListener('focus', onFocusChange, true /* useCapture */);

  const releaseFn = () => {
    if (currentReleaseFn === releaseFn) {
      currentReleaseFn = null;
      document.removeEventListener(
        'focus',
        onFocusChange,
        true /* useCapture */,
      );
    }
  };
  currentReleaseFn = releaseFn;
  return releaseFn;
}
