'use strict';

var syn = require('syn');

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
  var template;
  var testEl;
  var input;
  var dropdown;
  var dropdownItems;
  var ctrl;

  before(function () {
    template = '<input data-ref="searchBarInput">' +
      '<div data-ref="searchBarDropdown">' +
      '<div>Narrow your search</div>' +
      '<ul>' +
      '<li data-ref="searchBarDropdownItem">' +
      '<span data-ref="searchBarDropdownItemTitle">' +
      'user:' +
      '</span>' +
      '</li>' +
      '<li data-ref="searchBarDropdownItem">' +
      '<span data-ref="searchBarDropdownItemTitle">' +
      'tag:' +
      '</span>' +
      '</li>' +
      '<li data-ref="searchBarDropdownItem">' +
      '<span data-ref="searchBarDropdownItemTitle">' +
      'url:' +
      '</span>' +
      '</li>' +
      '<li data-ref="searchBarDropdownItem">' +
      '<span data-ref="searchBarDropdownItemTitle">' +
      'group:' +
      '</span>' +
      '</li>' +
      '</ul>' +
      '</div>';
  });

  beforeEach(function () {
    testEl = document.createElement('div');
    testEl.innerHTML = template;
    document.body.appendChild(testEl);

    ctrl = new SearchBarController(testEl);

    input = ctrl.refs.searchBarInput;
    dropdown = ctrl.refs.searchBarDropdown;
    dropdownItems = testEl.querySelectorAll('[data-ref="searchBarDropdownItem"]');
  });

  afterEach(function () {
    document.body.removeChild(testEl);
  });

  it('dropdown appears when the input field has focus', function (done) {
    syn.click(input, () => {
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
        duration: 100
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
          pageY: itemThreeCenter.pageY + 1
        },
        duration: 10
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
});
