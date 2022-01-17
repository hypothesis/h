import syn from 'syn';

import { ShareWidgetController } from '../../controllers/share-widget-controller';

describe('ShareWidgetController', () => {
  // this is pseudo duplicating you see in share_widget.html.jinja2
  // but it only has the needed pieces to perform the functions we test
  const widgetTemplate = `
  <div class="js-share-widget">
    <div class="share-widget js-share-widget-owner">
      <div class="share-widget-target">
        <a share-target-href="https://twitter.com/intent/tweet?url={href}&hashtags=annotated"
          class="share-widget-target__icon">
          {{ svg_icon('twitter', 'share-widget-action') }}
        </a>
        <a share-target-href="https://www.facebook.com/sharer/sharer.php?u={href}"
          class="share-widget-target__icon">
          {{ svg_icon('facebook', 'share-widget-action') }}
        </a>
        <a share-target-href="mailto:?subject=Let%27s%20Annotate&amp;body={href}"
          class="share-widget-target__icon">
        </a>
      </div>
      <div class="share-widget-link">
          <input class="js-share-widget-clipboard" value="">
      </div>
      <div class="js-share-widget-msg-group">GROUP</div>
      <div class="js-share-widget-msg-private">PRIVATE</div>
    </div>
  </div>
  `;

  const template = `
    <button share-widget-config='{"url":"http://url1.goes?here=true", "private":false, "group":false}'>
      btn
    </button>
    <button share-widget-config='{"url":"http://url2.goes?here", "private":true, "group":false}'>
      btn
    </button>
    <button share-widget-config='{"url":"https://url3.goes?here=true", "private":false, "group":true}'>
      btn
    </button>
    <button share-widget-config='{"url":"http://url4.goes?here=alsotrue", "private":true, "group":true}'>
      <span><b>btn</b></span>
    </button>
  `;

  let container;
  let ctrl;

  const getTriggers = () => {
    return Array.from(container.querySelectorAll('[share-widget-config]'));
  };

  const widgetIsVisble = () => {
    return (
      container.querySelector('.js-share-widget').style.visibility === 'visible'
    );
  };

  const checkURLs = expectedURL => {
    Array.from(container.querySelectorAll('[share-target-href]')).forEach(
      anchor => {
        const tmpl = anchor.getAttribute('share-target-href');
        const expectedLink = tmpl.replace('{href}', expectedURL);
        const actualLink = anchor.href;
        assert.equal(actualLink, expectedLink);
      }
    );
  };

  const privateMessageVisible = () => {
    return (
      container.querySelector('.js-share-widget-msg-private').style.display ===
      'block'
    );
  };

  const groupMessageVisible = () => {
    return (
      container.querySelector('.js-share-widget-msg-group').style.display ===
      'block'
    );
  };

  beforeEach(() => {
    container = document.createElement('div');
    container.innerHTML = template + widgetTemplate;

    document.body.appendChild(container);

    ctrl = new ShareWidgetController(
      document.querySelector('.js-share-widget')
    );
  });

  afterEach(() => {
    container.remove();
    ctrl.beforeRemove();
  });

  it('shows/hides widget on clicking', done => {
    assert.isFalse(widgetIsVisble(), 'not visible by default');

    const btns = getTriggers();

    syn
      .click(btns[0], () => {
        assert.isTrue(widgetIsVisble(), 'visible after clicking trigger');
      })
      .click(document.body, () => {
        assert.isFalse(
          widgetIsVisble(),
          'hidden after clicking another trigger while it is open'
        );
      })
      .click(btns[3].querySelector('b'), () => {
        assert.isTrue(
          widgetIsVisble(),
          'opens when clicking elements inside of trigger'
        );
      })
      .click(btns[2], () => {
        assert.isTrue(
          widgetIsVisble(),
          'keeps trigger open when clicking another trigger while another dialog is open'
        );
      })
      .click(btns[2], () => {
        assert.isFalse(
          widgetIsVisble(),
          'close widget when clicking on the currently open trigger again'
        );
        done();
      });
  });

  it('displays correctly for current share link', done => {
    const btns = getTriggers();

    syn
      .click(btns[0], () => {
        checkURLs('http://url1.goes?here=true');
        assert.isFalse(privateMessageVisible());
        assert.isFalse(groupMessageVisible());
      })
      .click(btns[1], () => {
        checkURLs('http://url2.goes?here');
        assert.isTrue(privateMessageVisible());
        assert.isFalse(groupMessageVisible());
      })
      .click(btns[2], () => {
        checkURLs('https://url3.goes?here=true');
        assert.isFalse(privateMessageVisible());
        assert.isTrue(groupMessageVisible());
      })
      .click(btns[3].querySelector('b'), () => {
        checkURLs('http://url4.goes?here=alsotrue');
        assert.isTrue(privateMessageVisible());
        assert.isFalse(groupMessageVisible());
        done();
      });
  });
});
