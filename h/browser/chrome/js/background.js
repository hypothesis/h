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


function inject(tab) {
  chrome.tabs.executeScript(null, {
    file: 'public/js/embed.js'
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
  var newState

  if (state(tab.id) == 'active') {
    newState = state(tab.id, 'sleeping')
  } else {
    newState = state(tab.id, 'active')
    if (tab.status == 'complete') {
      inject(tab.id)
    }
  }

  setPageAction(tab.id, newState)
}


function onTabCreated(tab) {
  state(tab.id, 'sleeping')
}


function onTabRemoved(tab) {
  state(tab.id, null)
}


function onTabUpdated(tabId, info) {
  var currentState = state(tabId) || 'sleeping'

  setPageAction(tabId, currentState)

  if (currentState == 'active' && info.status == 'complete') {
    inject(tabId)
  }
}

chrome.runtime.onInstalled.addListener(onInstalled)
chrome.runtime.onUpdateAvailable.addListener(onUpdateAvailable)
chrome.pageAction.onClicked.addListener(onPageAction)
chrome.tabs.onCreated.addListener(onTabCreated)
chrome.tabs.onRemoved.addListener(onTabRemoved)
chrome.tabs.onUpdated.addListener(onTabUpdated)
