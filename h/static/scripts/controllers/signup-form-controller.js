import { Controller } from '../base/controller';

export class SignupFormController extends Controller {
  constructor(element) {
    super(element);

    const submitBtn = element.querySelector('.js-signup-btn');

    element.addEventListener('submit', () => {
      submitBtn.disabled = true;
    });
  }
}
