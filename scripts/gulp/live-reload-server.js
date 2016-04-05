'use strict';

var fs = require('fs');
var gulpUtil = require('gulp-util');
var http = require('http');
var WebSocketServer = require('websocket').server;

function changelogText() {
  return fs.readFileSync('./CHANGES', 'utf-8');
}

/**
 * An HTTP and WebSocket server which enables live reloading of the client.
 *
 * A simple HTTP and WebSocket server
 * which serves a test page with the Hypothesis client embedded
 * and notifies connected clients when assets are modified, enabling
 * the client to live-reload.
 *
 * @param {number} port - The port that the test server should listen on.
 * @param {string} appServer - The URL of the Hypothesis service to load
 *                             the client from.
 *
 * @constructor
 */
function LiveReloadServer(port, appServer) {
  var connections = [];

  function listen() {
    var log = gulpUtil.log;
    var server = http.createServer(function (req, response) {
      var content = `
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Hypothesis Client Test</title>
    </head>
    <body>
      <pre style="margin: 75px;">${changelogText()}</pre>
      <script>
      window.hypothesisConfig = function () {
        return {
          liveReloadServer: 'ws://localhost:${port}',

          // Open the sidebar when the page loads
          firstRun: true,
        };
      };

      window.addEventListener('message', function (event) {
        if (event.data.type && event.data.type === 'reloadrequest') {
          window.location.reload();
        }
      });
      </script>
      <script src="${appServer}/embed.js"></script>
    </body>
    </html>
      `;
      response.end(content);
    });

    server.listen(port, function (err) {
      if (err) {
        log('Setting up live reload server failed', err);
      }
      log(`Live reload server listening at http://localhost:${port}/`);
    });

    var ws = new WebSocketServer({
      httpServer: server,
    });

    ws.on('request', function (req) {
      log('Live reload client connected');
      var conn = req.accept(null, req.origin);
      connections.push(conn);

      conn.on('close', function () {
        var closedConn = conn;
        connections = connections.filter(function (conn) {
          return conn !== closedConn;
        });
      });
    });
  }

  /**
   * Notify connected clients about assets that changed.
   *
   * @param {Array<string>} assets - A list of paths of assets that changed.
   *                                 Paths are relative to the root asset
   *                                 build directory.
   */
  this.notifyChanged = function (assets) {
    connections.forEach(function (conn) {
      conn.sendUTF(JSON.stringify({
        type: 'assets-changed',
        changed: assets,
      }));
    });
  };

  listen();
}

module.exports = LiveReloadServer;
