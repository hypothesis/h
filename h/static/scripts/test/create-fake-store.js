'use strict';

var redux = require('redux');

function reducer(state, action) {
  if (action.type === 'STATE_UPDATE') {
    return Object.assign({}, state, action.update);
  } else {
    return state;
  }
}

/**
 * Creates a fake Redux store for use in tests.
 *
 * Unlike a normal Redux store where the user provides a function that
 * transforms the state in response to actions and calls dispatch() to update
 * the state when actions occur, this store has a setState() method for
 * replacing state fields directly.
 */
function createFakeStore(initialState) {
  var store = redux.createStore(reducer, initialState);

  store.setState = function (update) {
    store.dispatch({
      type: 'STATE_UPDATE',
      update: update,
    });
  };

  return store;
}

module.exports = createFakeStore;
