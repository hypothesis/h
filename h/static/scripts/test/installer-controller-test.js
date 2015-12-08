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
      '<input class="link">';
    extensionBtn = rootElement.querySelector('.extension');
    bookmarkletBtn = rootElement.querySelector('.bookmarklet');
    linkField = rootElement.querySelector('.link');
    document.body.appendChild(rootElement);
  });

  afterEach(function () {
    rootElement.parentNode.removeChild(rootElement);
  });

  function createController(userAgentInfo) {
    var controller = proxyquire('../installer-controller', {
      './ua-detect': userAgentInfo
    });
    controller.showSupportedInstallers(rootElement);
    return controller;
  }

  function isHidden(el) {
    return el.classList.contains('is-hidden');
  }

  it('shows the chrome extension to desktop Chrome users', function () {
    var controller = createController({isChrome: true});
    assert.isFalse(isHidden(extensionBtn));
    assert.isTrue(isHidden(bookmarkletBtn));
  });

  it('shows the bookmarklet on desktop browsers', function () {
    var controller = createController({isChrome: true, isMobile: false});
    assert.isFalse(isHidden(extensionBtn));
    assert.isTrue(isHidden(bookmarkletBtn));
  });

  it('shows only the Via link to mobile browsers', function () {
    var controller = createController({isChrome: true, isMobile: true});
    assert.isTrue(isHidden(extensionBtn));
    assert.isTrue(isHidden(bookmarkletBtn));
  });

  it('shows only the Via link to Microsoft Edge users', function () {
    var controller = createController({isMicrosoftEdge: true});
    assert.isTrue(isHidden(extensionBtn));
    assert.isTrue(isHidden(bookmarkletBtn));
  });
});
