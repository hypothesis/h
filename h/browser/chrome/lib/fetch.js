/**
 * Performs a network fetch for JSON data and returns a Promise
 * for the result.
 */
function fetchJSON(url) {
  return new Promise(function (resolve, reject) {
    var xhr = new XMLHttpRequest();
    xhr.onload = function () {
      try {
        resolve(JSON.parse(this.response));
      } catch (err) {
        reject(err);
      }
    }
    xhr.open('GET', url);
    xhr.send();
  });
}

module.exports = fetchJSON;
