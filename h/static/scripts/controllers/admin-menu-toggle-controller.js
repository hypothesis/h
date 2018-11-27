'use strict';

const Controller = require('../base/controller');

class AdminMenuToggleController extends Controller {
  constructor(element, options) {
    super(element, options);

    const window_ = options.window || window;
    const menu = window_.document.querySelector(".js-admin-navbar__menu");

    this.on('click', (event) => {
      if (menu.classList.contains("is-open")) {
        menu.classList.remove("is-open");
        this.element.innerHTML = "Menu";
      } else {
        menu.classList.add("is-open");
        this.element.innerHTML = "Close";
      }
    });
  }
}

module.exports = AdminMenuToggleController;
