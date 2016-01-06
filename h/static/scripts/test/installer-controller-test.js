var proxyquire = require('proxyquire');

describe('installer page', function () {
  var rootElement;
  var extensionBtn;
  var bookmarkletBtn;
  var linkField;

  beforeEach(function () {
    rootElement = document.createElement('div');
    rootElement.innerHTML =
      '<button class="extension js-install-chrome is-hidden"></button>' +
      '<button class="bookmarklet js-install-bookmarklet is-hidden"></button>' +
      '<input class="link">' +
      '<form class="js-proxy-form"><input name="url"></form>'
    extensionBtn = rootElement.querySelector('.extension');
    bookmarkletBtn = rootElement.querySelector('.bookmarklet');
    linkField = rootElement.querySelector('.link');
    document.body.appendChild(rootElement);
  });

  afterEach(function () {
    rootElement.parentNode.removeChild(rootElement);
  });

  function createController(userAgentInfo) {
    var Controller = proxyquire('../installer-controller', {
      './ua-detect': userAgentInfo
    });
    return new Controller(rootElement);
  }

  function isHidden(el) {
    return el.classList.contains('is-hidden');
  }

  it('shows the chrome extension to desktop Chrome users', function () {
    var controller = createController({chromeExtensionsSupported: true});
    assert.isFalse(isHidden(extensionBtn));
    assert.isTrue(isHidden(bookmarkletBtn));
  });

  it('shows the bookmarklet on desktop browsers', function () {
    var controller = createController({chromeExtensionsSupported: false,
                                       isMobile: false});
    assert.isTrue(isHidden(extensionBtn));
    assert.isFalse(isHidden(bookmarkletBtn));
  });

  it('shows only the Via link to mobile browsers', function () {
    var controller = createController({chromeExtensionsSupported: false,
                                       isMobile: true});
    assert.isTrue(isHidden(extensionBtn));
    assert.isTrue(isHidden(bookmarkletBtn));
  });

  it('shows only the Via link to Microsoft Edge users', function () {
    var controller = createController({isMicrosoftEdge: true});
    assert.isTrue(isHidden(extensionBtn));
    assert.isTrue(isHidden(bookmarkletBtn));
  });
});
