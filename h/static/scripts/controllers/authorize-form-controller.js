import { Controller } from '../base/controller';

/**
 * Controller for the OAuth authorization popup.
 */
export class AuthorizeFormController extends Controller {
  constructor(element) {
    super(element);

    this.on('submit', () => {
      // Prevent multiple submission or clicking the "Cancel" button after
      // clicking "Accept".
      this.setState({ submitting: true });
    });

    this.refs.cancelBtn.addEventListener('click', () => {
      window.close();
    });

    window.addEventListener('beforeunload', () => {
      this._sendAuthCanceledMessage();
    });
  }

  /**
   * Notify the parent window that auth was canceled.
   *
   * This is necessary since there isn't a DOM event that a cross-origin opener
   * window can listen for to know when a popup window is closed.
   */
  _sendAuthCanceledMessage() {
    if (this.state.submitting) {
      // User already pressed "Accept" button.
      return;
    }

    if (window.opener) {
      let state;
      if (this.refs.stateInput) {
        state = this.refs.stateInput.value;
      }

      // Since this message contains no private data, just set the origin to
      // '*' (any).
      window.opener.postMessage(
        {
          type: 'authorization_canceled',
          state,
        },
        '*',
      );
    }
  }

  update() {
    this.refs.cancelBtn.disabled = !this.state.submitting;
    this.refs.acceptBtn.disabled = !this.state.submitting;
  }
}
