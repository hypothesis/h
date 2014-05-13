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

function injecting(tabId, value) {
  var stateMap = localStorage.getItem('injectState')
  stateMap = stateMap ? JSON.parse(stateMap) : {}

  if (value === undefined) {
    return stateMap[tabId]
  }

  if (value) {
    stateMap[tabId] = value
  } else {
    delete stateMap[tabId]
  }

  localStorage.setItem('injectState', JSON.stringify(stateMap))

  return value
}


function inject(tabId) {
  // If we are already injecting, don't have to do anything.
  if (!injecting(tabId)) {
    console.log(new Date(), "Initiating code injectation for tab", tabId);
    injecting(tabId, true);
    setTimeout(function(){ // Give it some time before insertation
      injecting(tabId, false);
      console.log(new Date(), "Executing code injectation on tab", tabId);
      chrome.tabs.executeScript(tabId, {
        file: 'public/js/embed.js'
      })
    }, 1000);
  } else {
    console.log(new Date(), "Requested code injectation for tab", tabId,
                "but since an injectation is already in progress,",
                "not doing anything.");
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
    chrome.tabs.executeScript(tab.id, {
      file: 'public/js/destroy.js'
    })
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
  if (info.status == "loading") {
    // No need to do anything yet. We will get another notification soon.
    console.log(new Date(), "tab", tabId, "is loading. Not doing anything.");
    return;
  }

  console.log(new Date(), "tab", tabId, "has been updated.");
  var currentState = state(tabId) || 'sleeping'
  console.log(new Date(), "State of tab", tabId, "is '", currentState, "'.");

  setPageAction(tabId, currentState)

  if (currentState == 'active' && info.status == 'complete') {
    console.log (new Date(), "Requesting code injectation for tab", tabId)
    inject(tabId)
  }
}

chrome.runtime.onInstalled.addListener(onInstalled)
chrome.runtime.onUpdateAvailable.addListener(onUpdateAvailable)
chrome.pageAction.onClicked.addListener(onPageAction)
chrome.tabs.onCreated.addListener(onTabCreated)
chrome.tabs.onRemoved.addListener(onTabRemoved)
chrome.tabs.onUpdated.addListener(onTabUpdated)
