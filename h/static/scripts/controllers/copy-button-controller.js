'use strict';

var Controller = require('../base/controller');

class CopyButtonController extends Controller {
  constructor(element) {
    super(element);

    this.refs.button.onclick = () => {
      this.refs.input.select(); // We need to select the text before we copy.

      var copySucceeded = document.execCommand('copy');
      let notificationText = copySucceeded ? 'Link copied to clipboard!' : 'Copying link failed';

      const originalValue = this.refs.input.value;
      this.refs.input.value = notificationText;
      window.setTimeout(
        () => {
          this.refs.input.value = originalValue;
          // Copying can leave the <input> focused but its value text not
          // selected, and since it's already focused clicking on it to focus
          // it doesn't trigger the auto select all on focus. So we unfocus it.
          this.refs.input.blur();
        },
        1000);
    };
  }
}

module.exports = CopyButtonController;
