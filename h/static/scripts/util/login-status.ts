type AuthStatus = 'logged-in' | 'logged-out';

type AuthStatusMessage = {
  type: 'auth-status';
  status: AuthStatus;
};

/**
 * Send a message to other tabs in the same browser to report whether the
 * user is logged in.
 */
export function notifyAuthStatus() {
  const channel = createChannel();
  if (!channel) {
    return;
  }
  const userid = document.querySelector('meta[name=userid]') as
    | HTMLMetaElement
    | undefined;

  const msg: AuthStatusMessage = {
    type: 'auth-status',
    status: userid?.content ? 'logged-in' : 'logged-out',
  };
  channel.postMessage(msg);
  channel.close();
}

/**
 * Register a listener for changes to the logged-in/logged-out status in other tabs.
 */
export function listenForAuthStatusChange(
  cb: (status: AuthStatus) => void,
  signal: AbortSignal,
) {
  const channel = createChannel();
  if (!channel) {
    return;
  }
  signal.addEventListener('abort', () => channel.close());
  channel.onmessage = e => {
    const data = e.data as AuthStatusMessage;
    if (data.type === 'auth-status') {
      cb(data.status);
    }
  };
}

function createChannel() {
  if (typeof BroadcastChannel !== 'function') {
    return undefined;
  }
  return new BroadcastChannel('account-events');
}
