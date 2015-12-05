/**
 * A simple drop-down menu controller.
 *
 * All elements within 'rootElement' with the class 'js-menu-toggle'
 * become dropdown menu toggles that toggle their closest sibling
 * element with a 'js-menu' class, or the first element within
 * 'rootElement' that matches the selector set by 'data-menu-target'
 * on the toggle element.
 */
function DropdownMenuController(rootElement) {
  var menuToggles = rootElement.querySelectorAll('.js-menu-toggle');

  function setupMenu(menuToggle) {
    menuToggle.addEventListener('click', function (openEvent) {
      openEvent.preventDefault();

      var dropdown = menuToggle;
      if (menuToggle.dataset.menuTarget) {
        dropdown = rootElement.querySelector(menuToggle.dataset.menuTarget);
      } else {
        dropdown = dropdown.parentElement.querySelector('.js-menu');
      }
      if (!dropdown) {
        throw new Error('Associated menu not found');
      }

      var isOpen = dropdown.classList.toggle('is-open');
      if (isOpen) {
        document.addEventListener('click', function listener(event) {
          if (menuToggle.contains(event.target) || dropdown.contains(event.target)) {
            return;
          }
          dropdown.classList.remove('is-open');
          document.removeEventListener('click', listener);
        });
      }
    });
  }

  for (var i=0; i < menuToggles.length; i++) {
    setupMenu(menuToggles[i]);
  }
}

module.exports = DropdownMenuController;
