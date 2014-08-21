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

function isPDF(tabId) {
  tabState = pdfState(tabId) || 'unknown'
  return tabState == 'pdf'
}

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
  var pdf = isPDF(tab.id)
  var newState

  if (state(tab.id) == 'active') {
    newState = state(tab.id, 'sleeping')
    if (pdf) {
      // console.log("Going back to the native viewer.")
      params = {url: decodeURIComponent(parsePdfExtensionURL(tab.url))};
      chrome.tabs.update(tab.id, params)
    } else {
      // Normal non-pdf removal on page action
      // console.log("Doing normal non-pdf removal on page action");
      remove(tab.id)
    }
  } else {
    newState = state(tab.id, 'active')
    if (pdf) {
      // console.log("Reloading document with PDF.js...")
      chrome.tabs.reload(tab.id);
    } else {
      // Normal non-pdf injection on page action
      // console.log("Doing normal non-pdf insertion on page action");
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
  var pdf = isPDF(tabId)

  setPageAction(tabId, currentState)

  if ((currentState == 'active') && !pdf) {
    // console.log("Doing normal non-pdf insertion on update");
    inject(tabId)
  }
}

chrome.runtime.onInstalled.addListener(onInstalled)
chrome.runtime.onUpdateAvailable.addListener(onUpdateAvailable)
chrome.pageAction.onClicked.addListener(onPageAction)
chrome.tabs.onCreated.addListener(onTabCreated)
chrome.tabs.onRemoved.addListener(onTabRemoved)
chrome.tabs.onUpdated.addListener(onTabUpdated)
