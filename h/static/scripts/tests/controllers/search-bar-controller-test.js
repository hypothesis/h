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
      <div>
        <form data-ref="searchBarForm">
          <div class="search-bar__lozenges" data-ref="searchBarLozenges">
          </div>
          <input data-ref="searchBarInput" class="search-bar__input" name="q" />
        </form>
      </div>
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
        <div>
          <form data-ref="searchBarForm">
            <div class="search-bar__lozenges" data-ref="searchBarLozenges"></div>
            <input data-ref="searchBarInput" class="search-bar__input" name="q" value="${value}">
          </form>
        </div>
      `.trim();

      ctrl = util.setupComponent(document, template, SearchBarController);

      // Stub the submit method so it doesn't actually do a full page reload.
      ctrl.refs.searchBarForm.submit = sinon.stub();

      return {
        ctrl: ctrl,
        hiddenInput: ctrl.element.querySelector('input[type="hidden"]'),
        input: ctrl.refs.searchBarInput,
      };
    }

    /**
     * Return all of the given controller's lozenge elements (if any).
     *
     */
    function getLozenges(ctrl) {
      return ctrl.refs.searchBarLozenges.querySelectorAll('.js-lozenge');
    }

    it('should create lozenges for existing query terms in the input on page load', function () {
      var {ctrl} = component('foo');

      assert.equal(getLozenges(ctrl)[0].textContent, 'foo');
    });

    it('inserts a hidden input on init', function () {
      const {hiddenInput} = component();

      assert.notEqual(hiddenInput, null);
    });

    it('removes the name="q" attribute from the input on init', function () {
      const {input} = component();

      assert.isFalse(input.hasAttribute('name'));
    });

    it('adds the name="q" attribute to the hidden input on init', function () {
      const {hiddenInput} = component();

      assert.equal(hiddenInput.getAttribute('name'), 'q');
    });

    it('leaves the hidden input empty on init if the visible input is empty', function () {
      const {hiddenInput} = component();

      assert.equal(hiddenInput.value, '');
    });

    it('copies lozengifiable text from the input into the hidden input on init', function () {
      const {hiddenInput} = component('these are my tag:lozenges');

      assert.equal(hiddenInput.value, 'these are my tag:lozenges');
    });

    it('copies unlozengifiable text from the input into the hidden input on init', function () {
      const {hiddenInput} = component("group:'unclosed quotes");

      assert.equal(hiddenInput.value, "group:'unclosed quotes");
    });

    it('copies lozengifiable and unlozengifiable text from the input into the hidden input on init', function () {
      const {hiddenInput} = component("these are my tag:lozenges group:'unclosed quotes");

      assert.equal(hiddenInput.value, "these are my tag:lozenges group:'unclosed quotes");
    });

    it('updates the value of the hidden input as text is typed into the visible input', function () {
      const {input, hiddenInput} = component('initial text');

      input.value = 'new text';  // This is just "new text" and not
                                 // "initial text new text" because the
                                 // "initial text" will have been moved into
                                 // lozenges.
      input.dispatchEvent(new Event('input'));

      assert.equal(hiddenInput.value, 'initial text new text');
    });

    it('updates the value of the hidden input as unlozengifiable text is typed into the visible input', function () {
      const {input, hiddenInput} = component("group:'unclosed quotes");

      input.value = "group:'unclosed quotes still unclosed";
      input.dispatchEvent(new Event('input'));

      assert.equal(hiddenInput.value, "group:'unclosed quotes still unclosed");
    });

    it('updates the value of the hidden input when a lozenge is deleted', function () {
      const {ctrl, hiddenInput} = component('foo bar');

      const lozenge = getLozenges(ctrl)[0];
      lozenge.querySelector('.js-lozenge__close').dispatchEvent(
        new Event('mousedown'));

      assert.equal(hiddenInput.value, 'bar');
    });

    it('should not create a lozenge for incomplete query strings in the input on page load', function () {
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
