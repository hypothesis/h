import { Controller } from '../base/controller';

/**
 * A custom tooltip similar to the one used in Google Docs which appears
 * instantly when activated on a target element.
 *
 * The tooltip is displayed and hidden by setting its target element.
 *
 *  var tooltip = new Tooltip(document.body);
 *  tooltip.setState({target: aWidget}); // Show tooltip
 *  tooltip.setState({target: null}); // Hide tooltip
 *
 * The tooltip's label is derived from the target element's 'aria-label'
 * attribute.
 */
export class TooltipController extends Controller {
  constructor(el) {
    super(el);

    // With mouse input, show the tooltip on hover. On touch devices we rely on
    // the browser to synthesize 'mouseover' events to make the tooltip appear
    // when the host element is tapped and disappear when the host element loses
    // focus.
    // See http://www.codediesel.com/javascript/making-mouseover-event-work-on-an-ipad/
    el.addEventListener('mouseover', () => {
      this.setState({ target: el });
    });

    el.addEventListener('mouseout', () => {
      this.setState({ target: null });
    });

    this._tooltipEl = el.ownerDocument.createElement('div');
    this._tooltipEl.innerHTML =
      '<span class="tooltip-label js-tooltip-label"></span>';
    this._tooltipEl.className = 'tooltip';
    el.appendChild(this._tooltipEl);
    this._labelEl = this._tooltipEl.querySelector('.js-tooltip-label');

    this.setState({ target: null });
  }

  update(state) {
    if (!state.target) {
      this._tooltipEl.style.visibility = 'hidden';
      return;
    }

    const target = state.target;
    const label = target.getAttribute('aria-label');
    this._labelEl.textContent = label;

    Object.assign(this._tooltipEl.style, {
      visibility: '',
      bottom: 'calc(100% + 5px)',
    });
  }
}
