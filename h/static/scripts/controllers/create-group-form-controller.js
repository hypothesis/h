'use strict';

function CreateGroupFormController(element) {
  // Create Group form handling
  const self = this;
  this._submitBtn = element.querySelector('.js-create-group-create-btn');
  this._groupNameInput = element.querySelector('.js-group-name-input');
  this._infoLink = element.querySelector('.js-group-info-link');
  this._infoText = element.querySelector('.js-group-info-text');

  function groupNameChanged() {
    self._submitBtn.disabled = self._groupNameInput.value.trim().length === 0;
  }

  self._groupNameInput.addEventListener('input', groupNameChanged);
  groupNameChanged();

  this._infoLink.addEventListener('click', (event) => {
    event.preventDefault();
    self._infoLink.classList.add('is-hidden');
    self._infoText.classList.remove('is-hidden');
  });
}

module.exports = CreateGroupFormController;
