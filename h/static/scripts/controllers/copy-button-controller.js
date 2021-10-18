import { Controller } from '../base/controller';

function isProbablyMobileSafari(userAgent) {
  return /\bMobile\b/.test(userAgent) && /\bSafari\b/.test(userAgent);
}

export class CopyButtonController extends Controller {
  constructor(element, options = {}) {
    super(element, options);

    const userAgent = options.userAgent || navigator.userAgent;

    // Make the input field read-only to avoid the user accidentally modifying
    // the link before copying it.
    //
    // An exception is made for Mobile Safari because selecting the contents of
    // a read-only input field is hard in that browser.
    this.refs.input.readOnly = !isProbablyMobileSafari(userAgent);

    this.refs.button.onclick = () => {
      // Method for selecting <input> text taken from 'select' package.
      // See https://github.com/zenorocha/select/issues/1 and
      // http://stackoverflow.com/questions/3272089
      this.refs.input.focus();
      this.refs.input.setSelectionRange(0, this.refs.input.value.length);

      const notificationText = document.execCommand('copy')
        ? 'Link copied to clipboard!'
        : 'Copying link failed';

      const NOTIFICATION_TEXT_TIMEOUT = 1000;
      const originalValue = this.refs.input.value;
      this.refs.input.value = notificationText;
      window.setTimeout(() => {
        this.refs.input.value = originalValue;
        // Copying can leave the <input> focused but its value text not
        // selected, and since it's already focused clicking on it to focus
        // it doesn't trigger the auto select all on focus. So we unfocus it.
        this.refs.input.blur();
      }, NOTIFICATION_TEXT_TIMEOUT);
    };
  }
}
