import { Controller } from '../base/controller';

/* Turn a normal submit element into one that shows a confirm dialog.
 *
 * The element's form will only be submitted if the user answers the
 * confirmation dialog positively.
 *
 */
export class ConfirmSubmitController extends Controller {
  constructor(element, options) {
    super(element);

    const window_ = options.window || window;

    element.addEventListener(
      'click',
      event => {
        if (!window_.confirm(element.dataset.confirmMessage)) {
          event.preventDefault();
          event.stopPropagation();
          event.stopImmediatePropagation();
          return;
        }
      },
      /*capture*/ true,
    );
  }
}
