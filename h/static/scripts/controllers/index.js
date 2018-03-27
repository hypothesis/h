'use strict';

/**
 * Controllers provide client-side logic for server-rendered HTML.
 *
 * HTML elements declare their associated controller(s) using `js-`-prefixed
 * class names.
 *
 * This file exports a mapping between CSS selectors and controller
 * classes for "common" controls that are useful on both the admin and
 * user-facing sites.
 */

const CharacterLimitController = require('./character-limit-controller');
const CopyButtonController = require('./copy-button-controller');
const ConfirmSubmitController = require('./confirm-submit-controller');
const DropdownMenuController = require('./dropdown-menu-controller');
const FormController = require('./form-controller');
const FormCancelController = require('./form-cancel-controller');
const FormInputController = require('./form-input-controller');
const FormSelectOnFocusController = require('./form-select-onfocus-controller');
const InputAutofocusController = require('./input-autofocus-controller');
const ListInputController = require('./list-input-controller');
const TooltipController = require('./tooltip-controller');

module.exports = {
  '.js-character-limit': CharacterLimitController,
  '.js-copy-button': CopyButtonController,
  '.js-confirm-submit': ConfirmSubmitController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-form': FormController,
  '.js-form-cancel': FormCancelController,
  '.js-form-input': FormInputController,
  '.js-input-autofocus': InputAutofocusController,
  '.js-list-input': ListInputController,
  '.js-select-onfocus': FormSelectOnFocusController,
  '.js-tooltip': TooltipController,
};
