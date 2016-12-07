'use strict';

const Controller = require('../base/controller');

function isWordChar(event) {
  return event.key.match(/^\w$/) && !event.ctrlKey && !event.altKey &&
                                    !event.metaKey;
}

/**
 * Automatically focuses an input field when the user presses a letter, number
 * or backspace if no other element on the page has keyboard focus. The field's
 * focus can also be blurred by pressing Escape.
 *
 * This provides behavior similar to Google.com where the user can "type" in the
 * search box even if it is not focused.
 */
class InputAutofocusController extends Controller {
  constructor(element) {
    super(element);

    this._onKeyDown = (event) => {
      if (document.activeElement === document.body) {
        if (isWordChar(event) || event.key === 'Backspace') {
          element.focus();
        }
      } else if (document.activeElement === element && event.key === 'Escape') {
        element.blur();
      }
    };

    document.addEventListener('keydown', this._onKeyDown);
  }

  beforeRemove() {
    document.removeEventListener('keydown', this._onKeyDown);
  }
}

module.exports = InputAutofocusController;
