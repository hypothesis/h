function inject(tab) {
  chrome.tabs.executeScript(null, {
    file: 'js/inject.js'
  })
}

function state(tabId, value) {
  var stateMap = localStorage.getItem('state')
  stateMap = stateMap ? JSON.parse(stateMap) : {}

  if (value === undefined) {
    return stateMap[tabId]
  } else {
    if (value != null) {
      stateMap[tabId] = value
    } else {
      delete stateMap[tabId]
    }
    return localStorage.setItem('state', JSON.stringify(stateMap))
  }
}


function onPageAction(tab) {
  if (state(tab.id) != 'active') {
    state(tab.id, 'active')
    inject(tab.id)
  } else {
    state(tab.id, null)
  }
}


function onTabCreated(tab) {
  state(tab.id, null)
}


function onTabUpdated(tabId, info) {
  if (info.status != 'complete') return

  switch(state(tabId)) {
  case 'active':
    inject(tabId)
  default:
    chrome.pageAction.show(tabId)
  }
}

chrome.pageAction.onClicked.addListener(onPageAction)
chrome.tabs.onUpdated.addListener(onTabUpdated)
chrome.tabs.onCreated.addListener(onTabCreated)
