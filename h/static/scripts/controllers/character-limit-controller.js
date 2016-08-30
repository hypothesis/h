'use strict';

var inherits = require('inherits');

var Controller = require('../base/controller');
var setElementState = require('../util/dom').setElementState;

function CharacterLimitController(element) {
  Controller.call(this, element);

  var self = this;
  this.refs.characterLimitInput.addEventListener('input', function () {
    self.forceUpdate();
  });
  this.forceUpdate();
}
inherits(CharacterLimitController, Controller);

CharacterLimitController.prototype.update = function () {
  var input = this.refs.characterLimitInput;
  var maxlength = parseInt(input.dataset.maxlength);
  var counter = this.refs.characterLimitCounter;
  counter.textContent = input.value.length + '/' + maxlength;
  setElementState(counter, {tooLong: input.value.length > maxlength});
  setElementState(this.refs.characterLimitCounter, {ready: true});
};

module.exports = CharacterLimitController;
