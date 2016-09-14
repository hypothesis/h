'use strict';

var Controller = require('../base/controller');
var { setElementState } = require('../util/dom');

class CharacterLimitController extends Controller {
  constructor(element) {
    super(element);

    this.refs.characterLimitInput.addEventListener('input', () => {
      this.forceUpdate();
    });
    this.forceUpdate();
  }

  update() {
    var input = this.refs.characterLimitInput;
    var maxlength = parseInt(input.dataset.maxlength);
    var counter = this.refs.characterLimitCounter;
    counter.textContent = input.value.length + '/' + maxlength;
    setElementState(counter, {tooLong: input.value.length > maxlength});
    setElementState(this.refs.characterLimitCounter, {ready: true});
  }
}

module.exports = CharacterLimitController;
