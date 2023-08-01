import { Controller } from '../base/controller';

export class AdminUsersController extends Controller {
  constructor(element, options) {
    super(element, options);

    const window_ = options.window || window;
    function confirmFormSubmit() {
      return window_.confirm(
        "This will permanently delete all the user's data. Are you sure?",
      );
    }

    this.on('submit', event => {
      if (!confirmFormSubmit()) {
        event.preventDefault();
      }
    });
  }
}
