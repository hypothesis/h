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

import { CharacterLimitController } from './character-limit-controller';
import { CopyButtonController } from './copy-button-controller';
import { ConfirmSubmitController } from './confirm-submit-controller';
import { DisableOnSubmitController } from './disable-on-submit-controller';
import { DropdownMenuController } from './dropdown-menu-controller';
import { FormController } from './form-controller';
import { FormCancelController } from './form-cancel-controller';
import { FormInputController } from './form-input-controller';
import { FormSelectOnFocusController } from './form-select-onfocus-controller';
import { InputAutofocusController } from './input-autofocus-controller';
import { ListInputController } from './list-input-controller';
import { TooltipController } from './tooltip-controller';

export const sharedControllers = {
  '.js-character-limit': CharacterLimitController,
  '.js-copy-button': CopyButtonController,
  '.js-confirm-submit': ConfirmSubmitController,
  '.js-disable-on-submit': DisableOnSubmitController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-form': FormController,
  '.js-form-cancel': FormCancelController,
  '.js-form-input': FormInputController,
  '.js-input-autofocus': InputAutofocusController,
  '.js-list-input': ListInputController,
  '.js-select-onfocus': FormSelectOnFocusController,
  '.js-tooltip': TooltipController,
};
