describe('HelpPage', function () {
  var errors = require('../lib/errors');
  var HelpPage = require('../lib/help-page');
  var fakeChromeTabs;
  var help;

  beforeEach(function () {
    fakeChromeTabs = {create: sinon.stub()};
    help = new HelpPage(fakeChromeTabs, function fakeExtensionURL(path) {
      return 'CRX_PATH' + path;
    });
  });

  describe('.showHelpForError', function () {
    it('renders the "local-file" page when passed a LocalFileError', function () {
      help.showHelpForError({id: 1, index: 1}, new errors.LocalFileError('msg'));
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        index: 2,
        openerTabId: 1,
        url: 'CRX_PATH/help/index.html#local-file'
      });
    });

    it('renders the "no-file-access" page when passed a NoFileAccessError', function () {
      help.showHelpForError({id: 1, index: 1}, new errors.NoFileAccessError('msg'));
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        index: 2,
        openerTabId: 1,
        url: 'CRX_PATH/help/index.html#no-file-access'
      });
    });

    it('renders the "no-file-access" page when passed a RestrictedProtocolError', function () {
      help.showHelpForError({id: 1, index: 1}, new errors.RestrictedProtocolError('msg'));
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        index: 2,
        openerTabId: 1,
        url: 'CRX_PATH/help/index.html#restricted-protocol'
      });
    });

    it('renders the "blocked-site" page when passed a BlockedSiteError', function () {
      help.showHelpForError({id: 1, index: 1}, new errors.BlockedSiteError('msg'));
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        index: 2,
        openerTabId: 1,
        url: 'CRX_PATH/help/index.html#blocked-site'
      });
    });

    it('renders the "other-error" page for unknown errors', function () {
      help.showHelpForError({id: 1, index: 1}, new Error('Unexpected Error'));
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        index: 2,
        openerTabId: 1,
        url: 'CRX_PATH/help/index.html?message=Unexpected%20Error#other-error'
      });
    });
  });

  describe('.showLocalFileHelpPage', function () {
    it('should load the help page with the "local-file" fragment', function () {
      help.showLocalFileHelpPage({id: 1, index: 1});
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        index: 2,
        openerTabId: 1,
        url: 'CRX_PATH/help/index.html#local-file'
      });
    });
  });

  describe('.showNoFileAccessHelpPage', function () {
    it('should load the help page with the "no-file-access" fragment', function () {
      help.showNoFileAccessHelpPage({id: 1, index: 1});
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        index: 2,
        openerTabId: 1,
        url: 'CRX_PATH/help/index.html#no-file-access'
      });
    });
  });

  describe('.showRestrictedProtocolPage', function () {
    it('should load the help page with the "restricted-protocol" fragment', function () {
      help.showRestrictedProtocolPage({id: 1, index: 1});
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        index: 2,
        openerTabId: 1,
        url: 'CRX_PATH/help/index.html#restricted-protocol'
      });
    });
  });
});
