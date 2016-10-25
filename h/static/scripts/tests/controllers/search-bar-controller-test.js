'use strict';

var syn = require('syn');
var util = require('./util');

var SearchBarController = require('../../controllers/search-bar-controller');

function center(element) {
  let rect = element.getBoundingClientRect();
  return {
    pageX: rect.left + (rect.width / 2),
    pageY: rect.top + (rect.height / 2),
  };
}

function isActiveItem(element) {
  return element.classList.contains('js-search-bar-dropdown-menu-item--active');
}

describe('SearchBarController', function () {
  describe('Dropdown', function () {
    var testEl;
    var input;
    var dropdown;
    var dropdownItems;
    var ctrl;
    var form;
    var TEMPLATE = `
      <form>
        <div class="search-bar__lozenges" data-ref="searchBarLozenges">
        </div>
        <input data-ref="searchBarInput" class="search-bar__input" />
        <input data-ref="searchBarInputHidden" class="js-search-bar__input-hidden" name="q" value="foo" />
        <div data-ref="searchBarDropdown">
          <div>Narrow your search</div>
          <ul>
            <li data-ref="searchBarDropdownItem">
              <span data-ref="searchBarDropdownItemTitle">
                user:
              </span>
            </li>
            <li data-ref="searchBarDropdownItem">
              <span data-ref="searchBarDropdownItemTitle">
                tag:
              </span>
            </li>
            <li data-ref="searchBarDropdownItem">
              <span data-ref="searchBarDropdownItemTitle">
                url:
              </span>
            </li>
            <li data-ref="searchBarDropdownItem">
              <span data-ref="searchBarDropdownItemTitle">
                group:
              </span>
            </li>
          </ul>
        </div>
      </form>
    `;

    beforeEach(function () {
      testEl = document.createElement('div');
      testEl.innerHTML = TEMPLATE;
      document.body.appendChild(testEl);

      ctrl = new SearchBarController(testEl);

      input = ctrl.refs.searchBarInput;
      dropdown = ctrl.refs.searchBarDropdown;
      dropdownItems = testEl.querySelectorAll('[data-ref="searchBarDropdownItem"]');
      form = testEl.querySelector('form');

      form.addEventListener('submit', event => { event.preventDefault(); });
    });

    afterEach(function () {
      document.body.removeChild(testEl);
    });

    it('dropdown appears when the input field has focus', function (done) {
      syn
        .click(input, () => {
          assert.isTrue(dropdown.classList.contains('is-open'));
          done();
        });
    });

    it('dropdown is hidden when the input field loses focus', function (done) {
      syn
        .click(input)
        .click(document.body, () => {
          assert.isFalse(dropdown.classList.contains('is-open'));
          done();
        });
    });

    it('selects facet from dropdown on mousedown', function (done) {
      syn
        .click(input)
        .click(dropdownItems[0], () => {
          assert.equal(input.value, 'user:');
          done();
        });
    });

    it('highlights facet on up arrow', function (done) {
      syn
        .click(input)
        .type('[up]', () => {
          assert.isOk(isActiveItem(dropdownItems[3]));
          done();
        });
    });

    it('highlights facet on down arrow', function (done) {
      syn
        .click(input)
        .type('[down]', () => {
          assert.isOk(isActiveItem(dropdownItems[0]));
          done();
        });
    });

    it('highlights the correct facet for a combination of mouseover, up and down arrow keys', function (done) {
      let itemThreeCenter = center(dropdownItems[2]);
      syn
        .click(input)
        // Down arrow to select first item
        .type('[down]', () => {
          assert.isOk(isActiveItem(dropdownItems[0]));
        })
        // Move mouse from input to the middle of the third item.
        .move({
          from: center(input),
          to: itemThreeCenter,
          duration: 100,
        }, () => {
          assert.isNotOk(isActiveItem(dropdownItems[0]));
          assert.isOk(isActiveItem(dropdownItems[2]));
        })
        // Up arrow to select second item.
        .type('[up]', () => {
          assert.isNotOk(isActiveItem(dropdownItems[2]));
          assert.isOk(isActiveItem(dropdownItems[1]));
        })
        // Jiggle the mouse just a little over the third item.
        .move({
          from: itemThreeCenter,
          to: {
            pageX: itemThreeCenter.pageX + 1,
            pageY: itemThreeCenter.pageY + 1,
          },
          duration: 10,
        }, () => {
          assert.isNotOk(isActiveItem(dropdownItems[1]));
          assert.isOk(isActiveItem(dropdownItems[2]));
        })
        // Down arrow to select the fourth item.
        .type('[down]', () => {
          assert.isNotOk(isActiveItem(dropdownItems[2]));
          assert.isOk(isActiveItem(dropdownItems[3]));
          done();
        });
    });

    it('selects facet on enter', function (done) {
      syn
        .click(input)
        .type('[down][enter]', () => {
          assert.equal(input.value, 'user:');
          done();
        });
    });

    it('dropdown stays open when clicking on a part of it that is not one of the suggestions', function (done) {
      syn
        .click(input)
        .click(dropdown.querySelector('div'), () => {
          assert.isTrue(dropdown.classList.contains('is-open'));
          done();
        });
    });

    it('search options narrow as input changes', function (done) {
      syn
        .click(input)
        .type('g', () => {
          assert.isTrue(dropdownItems[0].classList.contains('is-hidden'));
          assert.isFalse(dropdownItems[1].classList.contains('is-hidden'));
          assert.isTrue(dropdownItems[2].classList.contains('is-hidden'));
          assert.isFalse(dropdownItems[3].classList.contains('is-hidden'));
          done();
        });
    });

    it('highlights the correct facet from narrowed dropdown items on up and down arrow keys', function (done) {
      syn
        .click(input)
        .type('g[down]', () => {
          assert.isOk(isActiveItem(dropdownItems[1]));
        })
        .type('[up]', () => {
          assert.isNotOk(isActiveItem(dropdownItems[1]));
          assert.isOk(isActiveItem(dropdownItems[3]));
          done();
        });
    });

    it('dropdown closes when user types ":"', function (done) {
      syn
        .click(input)
        .type(':', () => {
          assert.isFalse(dropdown.classList.contains('is-open'));
          done();
        });
    });

    it('dropdown closes when there are no matches', function (done) {
      syn
        .click(input)
        .type('x', () => {
          assert.isFalse(dropdown.classList.contains('is-open'));
          done();
        });
    });

    it('does not submit the form when a dropdown element is selected', function (done) {
      let submitted = false;
      form.addEventListener('submit', () => {
        submitted = true;
      });

      syn
        .click(input)
        .type('[down][enter]', () => {
          assert.isFalse(submitted);
          done();
        });
    });

    it('allows submitting the form when query is empty and no dropdown element is selected', function (done) {
      var submit = sinon.stub(form, 'submit');

      syn
        .click(input)
        .type('[enter]', () => {
          assert.isTrue(submit.calledOnce);
          done();
        });
    });
  });

  describe('Lozenges', function () {
    var ctrl;

    afterEach(function () {
      if (ctrl) {
        ctrl.element.remove();
        ctrl = null;
      }
    });

    /**
     * Make a <form> with the SearchBarController enhancement applied and
     * return the various parts of the component.
     *
     */
    function component(value) {
      value = value || '';
      var template = `
        <form>
          <div class="search-bar__lozenges" data-ref="searchBarLozenges"></div>
          <input data-ref="searchBarInput" class="search-bar__input">
          <input data-ref="searchBarInputHidden" class="js-search-bar__input-hidden" name="q" value="${value}">
          <div data-ref="searchBarDropdown"></div>
        </form>
      `.trim();

      ctrl = util.setupComponent(document, template, SearchBarController);

      return {
        ctrl: ctrl,
        input: ctrl.refs.searchBarInput,
        hiddenInput: ctrl.refs.searchBarInputHidden,
      };
    }

    /**
     * Return all of the given controller's lozenge elements (if any).
     *
     */
    function getLozenges(ctrl) {
      return ctrl.refs.searchBarLozenges.querySelectorAll('.js-lozenge__content');
    }

    it('should create lozenges for existing query terms in the hidden input on page load', function () {
      var {ctrl} = component('foo');

      assert.equal(getLozenges(ctrl)[0].textContent, 'foo');
    });

    it('should not create a lozenge for incomplete query strings in the hidden input on page load', function () {
      var {ctrl, input} = component("'bar");

      assert.equal(getLozenges(ctrl).length, 0);
      assert.equal(input.value, "'bar");
    });

    it('should create a lozenge when the user presses space and there are no incomplete query strings in the input', function (done) {
      var {ctrl, input, hiddenInput} = component('foo');

      syn
        .click(input)
        .type('gar')
        .type('[space]', () => {
          assert.equal(getLozenges(ctrl)[1].textContent, 'gar');
          done();
        });
    });

    it('should create a lozenge when the user completes a previously incomplete query string and then presses the space key', function (done) {
      var {ctrl, input} = component("'bar gar'");

      syn
        .click(input)
        .type(' gar\'')
        .type('[space]', () => {
          assert.equal(getLozenges(ctrl)[0].textContent, "'bar gar'");
          done();
        });
    });

    it('should not create a lozenge when the user does not completes a previously incomplete query string and presses the space key', function (done) {
      var {ctrl, input} = component("'bar");

      syn
        .click(input)
        .type('[space]')
        .type('gar')
        .type('[space]', () => {
          var lozenges = getLozenges(ctrl);
          assert.equal(lozenges.length, 0);
          assert.equal(input.value, "'bar gar ");
          done();
        });
    });
  });
});
