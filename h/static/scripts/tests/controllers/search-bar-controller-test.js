'use strict';

var syn = require('syn');
var util = require('./util');

var SearchBarController = require('../../controllers/search-bar-controller');


describe('SearchBarController', function () {
  describe('Autosuggest', function () {
    var testEl;
    var input;
    var dropdown;
    var ctrl;
    var TEMPLATE = `
      <form data-ref="searchBarForm">
        <div class="search-bar__lozenges" data-ref="searchBarLozenges">
        </div>
        <input data-ref="searchBarInput" class="search-bar__input" name="q" />
      </form>
    `;

    beforeEach(function () {
      testEl = document.createElement('div');
      testEl.innerHTML = TEMPLATE;
      document.body.appendChild(testEl);

      ctrl = new SearchBarController(testEl);

      input = ctrl.refs.searchBarInput;
      dropdown = input.nextSibling;
    });

    afterEach(function () {
      document.body.removeChild(testEl);
    });

    it('uses autosuggestion for initial facets', function (done) {

      assert.isFalse(dropdown.classList.contains('is-open'));

      syn
        .click(input, () => {
          assert.isTrue(dropdown.classList.contains('is-open'));

          let titles = Array.from(document.querySelectorAll('.search-bar__dropdown-menu-title')).map((node)=>{
            return node.textContent.trim();
          });

          assert.deepEqual(titles, ['user:', 'tag:', 'url:', 'group:']);

          done();
        });
    });

    it('it filters and updates input with autosuggested facet selection', function (done) {
      syn
        .click(input, ()=>{
          assert.notOk(input.value, 'baseline no value in input');
        })
        .type('r[down][enter]', ()=>{
          assert.equal(input.value, 'url:');
          done();
        });
    });


    it('allows submitting the form dropdown is open but has no selected value', function (done) {
      let form = testEl.querySelector('form');
      let submit = sinon.stub(form, 'submit');

      syn
        .click(input)
        .type('test[space]', () => {
          assert.isTrue(dropdown.classList.contains('is-open'));
        })
        .type('[enter]', () => {
          assert.equal(testEl.querySelector('input[type=hidden]').value, 'test');
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
          <input data-ref="searchBarInput" class="search-bar__input" name="q" value="${value}">
        </form>
      `.trim();

      ctrl = util.setupComponent(document, template, SearchBarController);

      return {
        ctrl: ctrl,
        input: ctrl.refs.searchBarInput,
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
      var {ctrl, input} = component('foo');

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
