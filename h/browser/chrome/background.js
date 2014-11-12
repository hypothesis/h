var ACTION_STATES = {
  active: {
    icons: {
      19: "images/browser-icon-active.png",
      38: "images/browser-icon-active@2x.png"
    },
    title: "Disable annotation"
  },
  sleeping: {
    icons: {
      19: "images/browser-icon-inactive.png",
      38: "images/browser-icon-inactive@2x.png"
    },
    title: "Enable annotation"
  }
}
var CRX_BASE_URL = chrome.extension.getURL('/')
var PDF_VIEWER_URL = chrome.extension.getURL('content/web/viewer.html')

function getPDFViewerURL(url) {
  return PDF_VIEWER_URL + '?file=' + encodeURIComponent(url)
}


function isPDFURL(url) {
  return url.toLowerCase().indexOf('.pdf') > 0
}

function isPDFViewerURL(url) {
  return url.indexOf(getPDFViewerURL('')) === 0
}

function isFileURL(url) {
  return url.indexOf("file://") === 0
}

function injectionFailed(tab) {
  setBrowserAction(tab.id, state(tab.id, 'sleeping'))
}

function injectIntoPDF(tab) {
  if (!isPDFViewerURL(tab.url)) {
    chrome.tabs.update(tab.id, {
      url: getPDFViewerURL(tab.url)
    })
  }
}

function injectIntoLocalPDF(tab) {
  chrome.extension.isAllowedFileSchemeAccess(function (allowed) {
    if (allowed) {
      injectIntoPDF(tab)
    } else {
      showNoFileAccessHelpPage(tab)
    }
  });
}

function injectIntoHTML(tab) {
  chrome.tabs.executeScript(tab.id, {
    file: 'public/embed.js'
  }, function (result) {
    if (result !== undefined) {
      chrome.tabs.executeScript(tab.id, {
        code: 'window.annotator = true;'
      })
    } else {
      injectionFailed(tab)
    }
  })
}

// Render the help page. The helpSection should correspond to the id of a
// section within the help page.
function showHelpPage(helpSection, tab) {
  injectionFailed(tab)
  chrome.tabs.update(tab.id, {
    url: CRX_BASE_URL + "help/permissions.html#" + helpSection
  })
}

var showLocalFileHelpPage = showHelpPage.bind(null, 'local-file')
var showNoFileAccessHelpPage = showHelpPage.bind(null, 'no-file-access')

function injectConfig(tab, fn) {
  var src  = CRX_BASE_URL + 'public/config.js'
  var code = 'var script = document.createElement("script");' +
             'script.src = "{}";' +
             'document.body.appendChild(script);'

  chrome.tabs.executeScript(tab.id, {code: code.replace('{}', src)}, fn);
}

function inject(tab) {
  injectConfig(tab, function () {
    function checkPDF(success, fallback) {
      if (isPDFURL(tab.url)) {
        success(tab)
      } else {
        fallback(tab)
      }
    }

    if (isFileURL(tab.url)) {
      checkPDF(injectIntoLocalPDF, showLocalFileHelpPage)
    } else {
      checkPDF(injectIntoPDF, injectIntoHTML)
    }
  })
}

function remove(tab) {
  if (isPDFViewerURL(tab.url)) {
    url = tab.url.slice(getPDFViewerURL('').length).split('#')[0];
    chrome.tabs.update(tab.id, {
      url: decodeURIComponent(url)
    })
  } else {
    chrome.tabs.executeScript(tab.id, {
      code: [
        'var script = document.createElement("script");',
        'script.src = "' + CRX_BASE_URL + 'public/destroy.js' + '";',
        'document.body.appendChild(script);',
        'delete window.annotator;',
      ].join('\n')
    })
  }
}


function state(tabId, value) {
  var stateMap = localStorage.getItem('state')
  stateMap = stateMap ? JSON.parse(stateMap) : {}

  if (value === undefined) {
    return stateMap[tabId]
  }

  if (value) {
    stateMap[tabId] = value
  } else {
    delete stateMap[tabId]
  }

  localStorage.setItem('state', JSON.stringify(stateMap))

  return value
}


function setBrowserAction(tabId, value) {
  chrome.browserAction.setIcon({
    tabId: tabId,
    path: ACTION_STATES[value].icons
  })
  chrome.browserAction.setTitle({
    tabId: tabId,
    title: ACTION_STATES[value].title
  })
}


function onInstalled(installDetails) {
  if (installDetails.reason === 'install') {
    chrome.tabs.create({url: 'https://hypothes.is/welcome'}, function (tab) {
      state(tab.id, 'active');
    });
  }

  /* We need this so that 3-rd party cookie blocking does not kill us.
     See https://github.com/hypothesis/h/issues/634 for more info.
     This is intended to be a temporary fix only.
  */
  var details = {
    primaryPattern: 'https://hypothes.is/*',
    setting: 'allow'
  }
  chrome.contentSettings.cookies.set(details)
  chrome.contentSettings.images.set(details)
  chrome.contentSettings.javascript.set(details)

  chrome.tabs.query({}, function (tabs) {
    for (var i in tabs) {
      var tabId = tabs[i].id
        , tabState = state(tabId) || 'sleeping'
      setBrowserAction(tabId, tabState)
    }
  })
}


function onUpdateAvailable() {
  chrome.runtime.reload()
}


function onBrowserAction(tab) {
  var newState

  if (state(tab.id) === 'active') {
    newState = state(tab.id, 'sleeping')
    remove(tab)
  } else {
    newState = state(tab.id, 'active')
    inject(tab)
  }

  setBrowserAction(tab.id, newState)
}


function onTabCreated(tab) {
  state(tab.id, 'sleeping')
}


function onTabRemoved(tab) {
  state(tab.id, null)
}


function onTabUpdated(tabId, info, tab) {
  var currentState = state(tabId) || 'sleeping'

  setBrowserAction(tabId, currentState)

  if (currentState === 'active' && info.status === 'complete') {
    inject(tab)
  }
}


chrome.runtime.onInstalled.addListener(onInstalled)
chrome.runtime.onUpdateAvailable.addListener(onUpdateAvailable)
chrome.browserAction.onClicked.addListener(onBrowserAction)
chrome.tabs.onCreated.addListener(onTabCreated)
chrome.tabs.onRemoved.addListener(onTabRemoved)
chrome.tabs.onUpdated.addListener(onTabUpdated)
