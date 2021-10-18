import { Controller } from '../base/controller';

/**
 * For this form, disable all submit elements (inputs or buttons) after
 * the form has been submitted—helps prevent duplicate submission of form data.
 * Note that this will only work on buttons or inputs with `type="submit"`
 */
export class DisableOnSubmitController extends Controller {
  constructor(element) {
    super(element);

    const submitEls = element.querySelectorAll('[type="submit"]');

    element.addEventListener('submit', () => {
      for (let i = 0; i < submitEls.length; i++) {
        submitEls[i].disabled = true;
      }
    });
  }
}
