'use strict';

const Controller = require('../base/controller');
const { setElementState } = require('../util/dom');

class CharacterLimitController extends Controller {
  constructor(element) {
    super(element);

    this.refs.characterLimitInput.addEventListener('input', () => {
      this.forceUpdate();
    });
    this.forceUpdate();
  }

  update() {
    const input = this.refs.characterLimitInput;
    const maxlength = parseInt(input.dataset.maxlength);
    const counter = this.refs.characterLimitCounter;
    counter.textContent = input.value.length + '/' + maxlength;
    setElementState(counter, {tooLong: input.value.length > maxlength});
    setElementState(this.refs.characterLimitCounter, {ready: true});
  }
}

module.exports = CharacterLimitController;
