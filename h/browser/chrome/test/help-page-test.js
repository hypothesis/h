describe('HelpPage', function () {
  var assert = chai.assert;
  var HelpPage = h.HelpPage;
  var fakeChromeTabs;
  var help;

  beforeEach(function () {
    fakeChromeTabs = {update: sinon.stub()};
    help = new HelpPage(fakeChromeTabs, function fakeExtensionURL(path) {
      return 'CRX_PATH' + path;
    });
  });

  describe('.showHelpForError', function () {
    it('renders the "local-file" page when passed a LocalFileError', function () {
      help.showLocalFileHelpPage({id: 1});
      sinon.assert.called(fakeChromeTabs.update);
      sinon.assert.calledWith(fakeChromeTabs.update, 1, {
        url: 'CRX_PATH/help/permissions.html#local-file'
      });
    });

    it('renders the "no-file-access" page when passed a NoFileAccessError', function () {
      help.showNoFileAccessHelpPage({id: 1});
      sinon.assert.called(fakeChromeTabs.update);
      sinon.assert.calledWith(fakeChromeTabs.update, 1, {
        url: 'CRX_PATH/help/permissions.html#no-file-access'
      });
    });

    it('throws an error if an unsupported error is provided', function () {
      assert.throws(function () {
        help.showHelpForError(new Error('Random Error'));
      });
    });
  });

  describe('.showLocalFileHelpPage', function () {
    it('should load the help page with the "local-file" fragment', function () {
      help.showLocalFileHelpPage({id: 1});
      sinon.assert.called(fakeChromeTabs.update);
      sinon.assert.calledWith(fakeChromeTabs.update, 1, {
        url: 'CRX_PATH/help/permissions.html#local-file'
      });
    });
  });

  describe('.showNoFileAccessHelpPage', function () {
    it('should load the help page with the "no-file-access" fragment', function () {
      help.showNoFileAccessHelpPage({id: 1});
      sinon.assert.called(fakeChromeTabs.update);
      sinon.assert.calledWith(fakeChromeTabs.update, 1, {
        url: 'CRX_PATH/help/permissions.html#no-file-access'
      });
    });
  });
});
