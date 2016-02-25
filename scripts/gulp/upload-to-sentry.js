'use strict';

var fs = require('fs');
var gulpUtil = require('gulp-util');
var path = require('path');
var request = require('request');
var through = require('through2');

/**
 * interface SentryOptions {
 *   /// The Sentry API key
 *   apiKey: string;
 *   /// The release string for the release to create
 *   release: string;
 *   /// The organization slug to use when constructing the API URL
 *   organization: string;
 *   /// The project name slug to use when constructing the API URL
 *   project: string;
 * }
 */

/** Wrapper around request() that returns a Promise. */
function httpRequest(opts) {
  return new Promise(function (resolve, reject) {
    request(opts, function (err, response, body) {
      if (err) {
        reject(err);
      } else {
        resolve({
          status: response.statusCode,
          body: body,
        });
      }
    });
  });
}

/**
 * Upload a stream of Vinyl files as a Sentry release.
 *
 * This creates a new release in Sentry using the organization, project
 * and release settings in @p opts and uploads the input stream of Vinyl
 * files as artefacts for the release.
 *
 * @param {SentryOptions} opts
 * @return {NodeJS.ReadWriteStream} - A stream into which Vinyl files from
 *                                    gulp.src() etc. can be piped.
 */
module.exports = function uploadToSentry(opts) {

  // A map of already-created release versions.
  // Once the release has been successfully created, this is used
  // to avoid creating it again.
  var createdReleases = {};

  return through.obj(function (file, enc, callback) {
    enc = enc;

    gulpUtil.log(`Uploading ${file.path} to Sentry`);

    var sentryURL =
      `https://app.getsentry.com/api/0/projects/${opts.organization}/${opts.project}/releases`;

    var releaseCreated;
    if (createdReleases[opts.release]) {
      releaseCreated = Promise.resolve();
    } else {
      releaseCreated = httpRequest({
          uri: `${sentryURL}/`,
          method: 'POST',
          auth: {
            user: opts.apiKey,
            password: '',
          },
          body: {
            version: opts.release,
          },
          json: true,
        }).then(function (result) {
          if (result.status === 201 ||
              (result.status === 400 &&
               result.body.detail.match(/already exists/))) {
            createdReleases[opts.release] = true;
            return;
          }
        });
    }

    releaseCreated.then(function () {
      return httpRequest({
        uri: `${sentryURL}/${opts.release}/files/`,
        method: 'POST',
        auth: {
          user: opts.apiKey,
          password: '',
        },
        formData: {
          file: fs.createReadStream(file.path),
          name: path.basename(file.path),
        },
      });
    }).then(function (result) {
      if (result.status === 201) {
        callback();
        return;
      }
      var message =
        `Uploading file failed: ${result.status}: ${result.body}`;
      throw new Error(message);
    }).catch(function (err) {
      gulpUtil.log('Sentry upload failed: ', err);
      throw err;
    });
  });
};
