var ACTION_STATES = {
  active: {
    icons: {
      19: "images/active_19.png",
      38: "images/active_38.png"
    },
    title: "Disable annotation"
  },
  sleeping: {
    icons: {
      19: "images/sleeping_19.png",
      38: "images/sleeping_38.png"
    },
    title: "Enable annotation"
  }
}


function inject(tabId) {
  chrome.tabs.executeScript(tabId, {
    file: 'public/embed.js'
  })
}

function remove(tabId) {
  chrome.tabs.executeScript(tabId, {
    file: 'public/destroy.js'
  })
}

function deployPDFjs(tabId, url) {
  chrome.tabs.update(tabId, {
    url: getViewerURL(url)
  })
}

function removePDFjs(tabId, url) {
  chrome.tabs.update(tabId, {
    url: decodeURIComponent(parsePdfExtensionURL(url))
  })
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


function pdfState(tabId, value) {
  var stateMap = localStorage.getItem('pdf-state')
  stateMap = stateMap ? JSON.parse(stateMap) : {}

  if (value === undefined) {
    return stateMap[tabId]
  }

  if (value) {
    stateMap[tabId] = value
  } else {
    delete stateMap[tabId]
  }

  localStorage.setItem('pdf-state', JSON.stringify(stateMap))

  return value
}

function markAsNotPDF(tabId) { pdfState(tabId, 'none') }
function markAsPDF(tabId)    { pdfState(tabId, 'pdf')  }

function isPDF(tabId, url) {
  tabState = pdfState(tabId)
  if (tabState === undefined) {
    console.log("I have no idea if this is a PDF. Checking URL:", url)
    if (url.toLowerCase().indexOf('.pdf') > 0) {
      console.log("Yes, marking as a PDF.");
      markAsPDF(tabId)
      return true
    } else {
      markAsNotPDF(tabId)
      return false
    }
  } else {
    return tabState == 'pdf'
  }
}

function inPDFjs(url) { return url.indexOf(chrome.extension.getURL('')) == 0 }

function setPageAction(tabId, value) {
  chrome.pageAction.setIcon({
    tabId: tabId,
    path: ACTION_STATES[value].icons
  })
  chrome.pageAction.setTitle({
    tabId: tabId,
    title: ACTION_STATES[value].title
  })
  chrome.pageAction.show(tabId)
}


function onInstalled() {
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
      setPageAction(tabId, tabState)
    }
  })
}


function onUpdateAvailable() {
  chrome.runtime.reload()
}


function onPageAction(tab) {
  var pdf = isPDF(tab.id, tab.url)
  var newState

  if (state(tab.id) == 'active') {
    newState = state(tab.id, 'sleeping')
    if (pdf) {
      // console.log("Going back to the native viewer.")
      removePDFjs(tab.id, tab.url)
    } else {
      // console.log("Doing normal non-pdf removal on page action")
      remove(tab.id)
    }
  } else {
    newState = state(tab.id, 'active')
    if (pdf) {
      // console.log("Reloading document with PDF.js...")
      deployPDFjs(tab.id, tab.url)
    } else {
      // console.log("Doing normal non-pdf insertion on page action")
      inject(tab.id)
    }
  }

  setPageAction(tab.id, newState)
}


function onTabCreated(tab) {
  state(tab.id, 'sleeping')
  pdfState(tab.id, null)
}


function onTabRemoved(tab) {
  state(tab.id, null)
  pdfState(tab.id, null)
}


function onTabUpdated(tabId, info) {
  var currentState = state(tabId) || 'sleeping'

  setPageAction(tabId, currentState)

  if (currentState == 'active') {
    if (isPDF(tabId, info.url)) {
      if (info.url && !inPDFjs(info.url)) {
        // console.log("Tab update: redirectign to PDF.js")
        deployPDFjs(tabId, info.url)
      }
    } else {
      // console.log("Doing normal non-pdf insertion on tab update")
      inject(tabId)
    }
  }
}

chrome.runtime.onInstalled.addListener(onInstalled)
chrome.runtime.onUpdateAvailable.addListener(onUpdateAvailable)
chrome.pageAction.onClicked.addListener(onPageAction)
chrome.tabs.onCreated.addListener(onTabCreated)
chrome.tabs.onRemoved.addListener(onTabRemoved)
chrome.tabs.onUpdated.addListener(onTabUpdated)
