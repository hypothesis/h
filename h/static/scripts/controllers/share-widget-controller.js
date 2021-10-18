import { Controller } from '../base/controller';

const CONFIG_ATTR = 'share-widget-config';
const TRIGGER_SELECTOR = `[${CONFIG_ATTR}]`;
const WIDGET_SELECTOR = '.js-share-widget-owner';
const TARGET_HREF_ATTR = 'share-target-href';
const TARGET_HREF_SELECTOR = `[${TARGET_HREF_ATTR}]`;
const CLIPBOARD_INPUT_SELECTOR = '.js-share-widget-clipboard';
const PRIVATE_MSG_SELECTOR = '.js-share-widget-msg-private';
const GROUP_MSG_SELECTOR = '.js-share-widget-msg-group';

const ARROW_PADDING_RIGHT = 16;
const ARROW_PADDING_BOTTOM = 5;

let shareWidgetAttached = false;

const getOffset = el => {
  el = el.getBoundingClientRect();
  return {
    // adjust for top left of the document
    left: el.left + window.pageXOffset,
    top: el.top + window.pageYOffset,
    width: el.width,
    height: el.height,
  };
};

class ShareWidget {
  constructor(containerElement) {
    // we only attach one to the dom since it's a global listener
    if (shareWidgetAttached) {
      return;
    }
    shareWidgetAttached = true;

    this._currentTrigger = null;
    this._container = containerElement;
    this._widget = this._container.querySelector(WIDGET_SELECTOR);
    this._widgetVisible = false;

    // on initialize we need to reset container visibility
    this.hide();

    this._handler = event => {
      const target = event.target;

      // do nothing if we are clicking inside of the widget
      if (this._container.contains(target)) {
        return;
      }

      const trigger = target.closest(TRIGGER_SELECTOR);

      if (trigger) {
        const config = JSON.parse(trigger.getAttribute(CONFIG_ATTR));

        // if we click the same trigger twice we expect
        // to close the current trigger. Otherwise, we need
        // to move to the new trigger and open
        if (trigger === this._currentTrigger && this._widgetVisible) {
          this.hide();
        } else {
          this.showForNode(trigger, config);
        }

        if (trigger !== this._currentTrigger) {
          this._currentTrigger = trigger;
        }

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        return;
      }

      // hide the widget if the click was not handled by
      // clicking on the triggers or widget itself
      if (this._widgetVisible) {
        this.hide();
      }
    };

    window.document.body.addEventListener('click', this._handler);
  }

  /**
   * @typedef {Object} ConfigOptions
   * @property {String} url - the url we are enabling to be shared
   * @property {Bool} [private] - is the card only visible to this user
   * @property {Bool} [group] - is the card posted in a group scope
   */

  /**
   * Update the template based on the config variables passed in
   *
   * @param  {ConfigOptions} config The details we need to apply update our template
   *   with the correct information per card.
   */
  _renderWidgetTemplate(config) {
    // copy to clipboard input
    this._widget.querySelector(CLIPBOARD_INPUT_SELECTOR).value = config.url;

    // social links
    Array.from(this._widget.querySelectorAll(TARGET_HREF_SELECTOR)).forEach(
      target => {
        target.href = target
          .getAttribute(TARGET_HREF_ATTR)
          .replace('{href}', encodeURI(config.url));
      }
    );

    // scope access dialog
    const privateMessage = this._widget.querySelector(PRIVATE_MSG_SELECTOR);
    const groupMessage = this._widget.querySelector(GROUP_MSG_SELECTOR);

    privateMessage.style.display = 'none';
    groupMessage.style.display = 'none';

    if (config.private) {
      privateMessage.style.display = 'block';
    } else if (config.group) {
      groupMessage.style.display = 'block';
    }
  }

  /**
   * Given a node, update the template, repostion the widget properly,
   *  and make it visible.
   *
   * @param  {HTMLElement} node The trigger node that we will place the widget
   *   next to.
   * @param  {ConfigOptions} config Passed through to rendering/interpolation
   */
  showForNode(node, config) {
    if (!node || !config) {
      throw new Error('showForNode did not recieve both arguments');
    }

    this._renderWidgetTemplate(config);

    // offsets affecting height need to be updated after variable replacement
    const widgetOffsets = getOffset(this._widget);
    const nodeOffset = getOffset(node);

    this._widget.style.top =
      nodeOffset.top - widgetOffsets.height - ARROW_PADDING_BOTTOM + 'px';
    this._widget.style.left =
      ARROW_PADDING_RIGHT +
      nodeOffset.left +
      nodeOffset.width / 2 -
      widgetOffsets.width +
      'px';

    this._container.style.visibility = 'visible';

    this._widgetVisible = true;
  }

  hide() {
    this._container.style.visibility = 'hidden';
    this._widgetVisible = false;
  }

  /**
   * Utility to clean up the listeners applied. Otherwise the subsequent
   * constructor will reset all other state. Primary use is meant for testing cleanup
   */
  detach() {
    window.document.body.removeEventListener('click', this._handler);
  }
}

/**
 * ShareWidgetController is the facade for the ShareWidget class that
 * does not mix the concerns of how our controller's lifecycle paradigm
 * in with the library code itself. Basically it maps what we define the
 * lifecycle of a controller to be into the appropriate method invocations on
 * the libraries api
 */
export class ShareWidgetController extends Controller {
  constructor(element, options = {}) {
    super(element, options);

    if (!shareWidgetAttached) {
      shareWidgetAttached = new ShareWidget(element);
    }
  }

  beforeRemove() {
    if (shareWidgetAttached) {
      shareWidgetAttached.detach();
      shareWidgetAttached = null;
    }
  }
}
