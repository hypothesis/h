describe('SidebarInjector', function () {
    'use strict';

    var assert = chai.assert;
    var SidebarInjector = h.SidebarInjector;
    var injector;
    var fakeChromeTabs;
    var fakeFileAccess;

    beforeEach(function () {
        fakeChromeTabs = {
            update: sinon.stub(),
            executeScript: sinon.stub()
        };
        fakeFileAccess = sinon.stub().yields(true);

        injector = new SidebarInjector(fakeChromeTabs, {
            isAllowedFileSchemeAccess: fakeFileAccess,
            extensionURL: sinon.spy(function (path) {
                return 'CRX_PATH' + path;
            })
        });
    });

    // Used when asserting rejected promises to raise an error if the resolved
    // path is taken. Otherwise Mocha will just assume the test passed.
    function assertReject() {
        assert(false, 'Expected the promise to reject the call');
    }

    describe('.injectIntoTab', function () {
        beforeEach(function () {
            // Handle loading the config.
            fakeChromeTabs.executeScript.withArgs(1, {code: 'window.annotator'}).yields([false]);
            fakeChromeTabs.executeScript.yields([]);
        });

        beforeEach(function() {
            this.server = sinon.fakeServer.create();
            this.server.respondWith("GET", "/blocklist.json",
                [200, {"Content-Type": "application/json"},
                    '{"twitter.com": {}, "finance.yahoo.com": {}, "*.google.com": {}}']);
        });

        afterEach(function() {
            this.server.restore();
        });

        var protocols = ['chrome:', 'chrome-devtools:', 'chrome-extension'];
        protocols.forEach(function (protocol) {
            it('bails early when trying to load an unsupported ' + protocol + ' url', function () {
                var spy = fakeChromeTabs.executeScript;
                var url = protocol + '//foo/';

                var promise = injector.injectIntoTab({id: 1, url: url}).then(
                    assertReject, function (err) {
                        assert.instanceOf(err, h.RestrictedProtocolError);
                        sinon.assert.notCalled(spy);
                    }
                );
                this.server.respond();
                return promise;
            });
        });

        describe('when viewing a remote PDF', function () {
            it('injects hypothesis into the page', function () {
                var spy = fakeChromeTabs.update.yields({tab: 1});
                var url = 'http://example.com/foo.pdf';

                var promise = injector.injectIntoTab({id: 1, url: url});
                this.server.respond();
                return promise.then(function () {
                    sinon.assert.calledWith(spy, 1, {
                        url: 'CRX_PATH/content/web/viewer.html?file=' + encodeURIComponent(url)
                    });
                });
            });
        });

        describe('when viewing an remote HTML page', function () {
            it('injects hypothesis into the page', function () {
                var spy = fakeChromeTabs.executeScript;
                var url = 'http://example.com/foo.html';

                var promise = injector.injectIntoTab({id: 1, url: url});
                this.server.respond();
                return promise.then(function () {
                    sinon.assert.callCount(spy, 2);
                    sinon.assert.calledWith(spy, 1, {
                        code: sinon.match('/public/config.js')
                    });
                    sinon.assert.calledWith(spy, 1, {
                        code: sinon.match('/public/embed.js')
                    });
                });
            });
        });

        describe('when viewing a local PDF', function () {
            describe('when file access is enabled', function () {
                it('loads the PDFjs viewer', function () {
                    var spy = fakeChromeTabs.update.yields([]);
                    var url = 'file://foo.pdf';

                    var promise = injector.injectIntoTab({id: 1, url: url}).then(
                        function () {
                            sinon.assert.called(spy);
                            sinon.assert.calledWith(spy, 1, {
                                url: 'CRX_PATH/content/web/viewer.html?file=' + encodeURIComponent('file://foo.pdf')
                            });
                        }
                    );
                    this.server.respond();
                    return promise;
                });
            });

            describe('when file access is disabled', function () {
                beforeEach(function () {
                    fakeFileAccess.yields(false);
                });

                it('returns an error', function () {
                    var url = 'file://foo.pdf';

                    var promise = injector.injectIntoTab({id: 1, url: url}).then(assertReject, function (err) {
                        assert.instanceOf(err, h.NoFileAccessError);
                    });
                    this.server.respond();
                    return promise;
                });
            });

        describe('when viewing a local HTML file', function () {
            it('returns an error', function () {
                var url = 'file://foo.html';
                var promise = injector.injectIntoTab({id: 1, url: url}).then(assertReject, function (err) {
                    assert.instanceOf(err, h.LocalFileError);
                });
                this.server.respond();
                return promise;
            });

            it('retuns an error before loading the config', function () {
                var url = 'file://foo.html';
                var promise = injector.injectIntoTab({id: 1, url: url}).then(assertReject, function (err) {
                    sinon.assert.notCalled(fakeChromeTabs.executeScript);
                });
                this.server.respond();
                return promise;
            });
        });
    });

    describe("when there's a non-empty blocklist", function() {
        it("still injects the scripts on unblocked sites", function() {
            var promise = injector.injectIntoTab(
                {id: 1, url: "http://notblocked.com"});
            this.server.respond();
            return promise.then(
                function onFulfill() {
                    sinon.assert.called(fakeChromeTabs.executeScript);
                },
                function onRejected(reason) {
                    assert(false, "The promise should not be rejected");
            });
        });

        it("still injects scripts on subdomains of blocked domains", function() {
            var promise = injector.injectIntoTab(
                {id: 1, url: "http://subdomain.twitter.com"});
            this.server.respond();
            return promise.then(
                function onFulfill() {
                    sinon.assert.called(fakeChromeTabs.executeScript);
                },
                function onRejected(reason) {
                    assert(false, "The promise should not be rejected");
            });
        });

        it("doesn't inject any scripts on blocked sites", function() {
            var promise = injector.injectIntoTab({id: 1, url: "http://twitter.com"});
            this.server.respond();
            return promise.then(
                function onFulfill() {
                    assert(false, "The promise should not be fulfilled");
                },
                function onRejected(reason) {
                    sinon.assert.notCalled(fakeChromeTabs.executeScript);
            });
        });

        it("doesn't inject scripts on sub pages of blocked sites", function() {
            var promise = injector.injectIntoTab(
                {id: 1, url: "http://twitter.com/sub/page.html"});
            this.server.respond();
            return promise.then(
                function onFulfill() {
                    assert(false, "The promise should not be fulfilled");
                },
                function onRejected(reason) {
                    sinon.assert.notCalled(fakeChromeTabs.executeScript);
            });
        });

        it("doesn't inject scripts on blocked sites with queries", function() {
            var promise = injector.injectIntoTab(
                {id: 1, url: "http://twitter.com?tag=foo&user=bar"});
            this.server.respond();
            return promise.then(
                function onFulfill() {
                    assert(false, "The promise should not be fulfilled");
                },
                function onRejected(reason) {
                    sinon.assert.notCalled(fakeChromeTabs.executeScript);
            });
        });

        it("doesn't inject scripts on blocked sites with anchors", function() {
            var promise = injector.injectIntoTab(
                {id: 1, url: "http://twitter.com#foo"});
            this.server.respond();
            return promise.then(
                function onFulfill() {
                    assert(false, "The promise should not be fulfilled");
                },
                function onRejected(reason) {
                    sinon.assert.notCalled(fakeChromeTabs.executeScript);
            });
        });

        it("doesn't inject scripts on blocked sites with ports", function() {
            var promise = injector.injectIntoTab(
                {id: 1, url: "http://twitter.com:1234"});
            this.server.respond();
            return promise.then(
                function onFulfill() {
                    assert(false, "The promise should not be fulfilled");
                },
                function onRejected(reason) {
                    sinon.assert.notCalled(fakeChromeTabs.executeScript);
            });
        });

        it("doesn't inject on wildcard-blocked subdomains", function() {
            var promise = injector.injectIntoTab(
                {id: 1, url: "http://drive.google.com"});
            this.server.respond();
            return promise.then(
                function onFulfill() {
                    assert(false, "The promise should not be fulfilled");
                },
                function onRejected(reason) {
                    sinon.assert.notCalled(fakeChromeTabs.executeScript);
            });
        });
    });
});

    describe('.removeFromTab', function () {
        it('bails early when trying to unload a chrome url', function () {
            var spy = fakeChromeTabs.executeScript;
            var url = 'chrome://extensions/';

            return injector.removeFromTab({id: 1, url: url}).then(function () {
                sinon.assert.notCalled(spy);
            });
        });

        var protocols = ['chrome:', 'chrome-devtools:', 'chrome-extension'];
        protocols.forEach(function (protocol) {
            it('bails early when trying to unload an unsupported ' + protocol + ' url', function () {
                var spy = fakeChromeTabs.executeScript;
                var url = protocol + '//foobar/';

                return injector.removeFromTab({id: 1, url: url}).then(function () {
                    sinon.assert.notCalled(spy);
                });
            });
        });

        describe('when viewing a PDF', function () {
            it('reverts the tab back to the original document', function () {
                var spy = fakeChromeTabs.update.yields([]);
                var url = 'CRX_PATH/content/web/viewer.html?file=' + encodeURIComponent('http://example.com/foo.pdf');

                return injector.removeFromTab({id: 1, url: url}).then(function () {
                    sinon.assert.calledWith(spy, 1, {
                        url: 'http://example.com/foo.pdf'
                    });
                });
            });
        });

        describe('when viewing an HTML page', function () {
            it('injects a destroy script into the page', function () {
                var stub = fakeChromeTabs.executeScript.yields([true]);
                return injector.removeFromTab({id: 1, url: 'http://example.com/foo.html'}).then(function () {
                    sinon.assert.calledWith(stub, 1, {
                        code: sinon.match('/public/destroy.js')
                    });
                });
            });
        });
    });
});
