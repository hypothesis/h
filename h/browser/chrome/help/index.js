// Detect the current OS and show approprite help.
chrome.runtime.getPlatformInfo(function (info) {
    var opts = document.querySelectorAll('[data-extension-path]');
    [].forEach.call(opts, function (opt) {
        if (opt.dataset.extensionPath !== info.os) {
            opt.hidden = true;
        }
    });
});
