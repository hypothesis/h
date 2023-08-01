import { Controller } from '../base/controller';

import { setElementState } from '../util/dom';

/**
 * Controller for dropdown menus.
 */
export class DropdownMenuController extends Controller {
  constructor(element) {
    super(element);

    const toggleEl = this.refs.dropdownMenuToggle;

    const handleClickOutside = event => {
      if (!this.refs.dropdownMenuContent.contains(event.target)) {
        // When clicking outside the menu on the toggle element, stop the event
        // so that it does not re-trigger the menu
        if (toggleEl.contains(event.target)) {
          event.stopPropagation();
          event.preventDefault();
        }

        this.setState({ open: false });

        element.ownerDocument.removeEventListener(
          'click',
          handleClickOutside,
          true /* capture */,
        );
      }
    };

    toggleEl.addEventListener('click', event => {
      event.preventDefault();
      event.stopPropagation();

      this.setState({ open: true });

      element.ownerDocument.addEventListener(
        'click',
        handleClickOutside,
        true /* capture */,
      );
    });
  }

  update(state) {
    setElementState(this.refs.dropdownMenuContent, { open: state.open });
    this.refs.dropdownMenuToggle.setAttribute(
      'aria-expanded',
      state.open.toString(),
    );
  }
}
