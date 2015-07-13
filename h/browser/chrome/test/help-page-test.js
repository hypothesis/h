describe('HelpPage', function () {
    var assert = chai.assert;
    var HelpPage = h.HelpPage;
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
            help.showHelpForError({id: 1, index: 1}, new h.LocalFileError('msg'));
            sinon.assert.called(fakeChromeTabs.create);
            sinon.assert.calledWith(fakeChromeTabs.create, {
                index: 2,
                openerTabId: 1,
                url: 'CRX_PATH/help/index.html#local-file'
            });
        });

        it('renders the "no-file-access" page when passed a NoFileAccessError', function () {
            help.showHelpForError({id: 1, index: 1}, new h.NoFileAccessError('msg'));
            sinon.assert.called(fakeChromeTabs.create);
            sinon.assert.calledWith(fakeChromeTabs.create, {
                index: 2,
                openerTabId: 1,
                url: 'CRX_PATH/help/index.html#no-file-access'
            });
        });

        it('renders the "no-file-access" page when passed a RestrictedProtocolError', function () {
            help.showHelpForError({id: 1, index: 1}, new h.RestrictedProtocolError('msg'));
            sinon.assert.called(fakeChromeTabs.create);
            sinon.assert.calledWith(fakeChromeTabs.create, {
                index: 2,
                openerTabId: 1,
                url: 'CRX_PATH/help/index.html#restricted-protocol'
            });
        });

        it('renders the "blocked-site" page when passed a BlockedSiteError', function () {
            help.showHelpForError({id: 1, index: 1}, new h.BlockedSiteError('msg'));
            sinon.assert.called(fakeChromeTabs.create);
            sinon.assert.calledWith(fakeChromeTabs.create, {
                index: 2,
                openerTabId: 1,
                url: 'CRX_PATH/help/index.html#blocked-site'
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
            help.showLocalFileHelpPage({id: 1, index: 1});
            sinon.assert.called(fakeChromeTabs.create);
            sinon.assert.calledWith(fakeChromeTabs.create, {
                index: 2,
                openerTabId: 1,
                url: 'CRX_PATH/help/index.html#local-file'
            });
        });
    });

    describe('.showNoFileAccessHelpPage', function () {
        it('should load the help page with the "no-file-access" fragment', function () {
            help.showNoFileAccessHelpPage({id: 1, index: 1});
            sinon.assert.called(fakeChromeTabs.create);
            sinon.assert.calledWith(fakeChromeTabs.create, {
                index: 2,
                openerTabId: 1,
                url: 'CRX_PATH/help/index.html#no-file-access'
            });
        });
    });

    describe('.showRestrictedProtocolPage', function () {
        it('should load the help page with the "restricted-protocol" fragment', function () {
            help.showRestrictedProtocolPage({id: 1, index: 1});
            sinon.assert.called(fakeChromeTabs.create);
            sinon.assert.calledWith(fakeChromeTabs.create, {
                index: 2,
                openerTabId: 1,
                url: 'CRX_PATH/help/index.html#restricted-protocol'
            });
        });
    });
});
