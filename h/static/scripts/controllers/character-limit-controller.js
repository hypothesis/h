'use strict';

function CharacterLimitController(element) {
  var counter = element.parentElement.querySelector(
    '.js-character-limit-counter');
  var input = element.querySelector('.js-character-limit-input');
  var maxlength = parseInt(input.dataset.maxlength);

  counter.textContent = '';

  function updateCounter() {
    var length = input.value.length;

    counter.textContent = length + '/' + maxlength;

    if (length > maxlength) {
      counter.classList.add('is-too-long');
    } else {
      counter.classList.remove('is-too-long');
    }
  }

  updateCounter();
  input.addEventListener('input', updateCounter);

  counter.classList.add('is-ready');
}

module.exports = CharacterLimitController;
