'use strict';

var fs = require('fs');
var path = require('path');
var gulpUtil = require('gulp-util');
var request = require('request');
var through = require('through2');

var SENTRY_API_ROOT = 'https://app.getsentry.com/api/0';

/**
 * interface SentryOptions {
 *   /// The Sentry API key
 *   key: string;
 *   /// The Sentry organisation to upload the release to
 *   organization: string;
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
          response: response,
          body: body,
        });
      }
    });
  });
}


/** Create a release in Sentry. Returns a Promise. */
function createRelease(opts, project, release) {
  return httpRequest({
    uri: `${SENTRY_API_ROOT}/projects/${opts.organization}/${project}/releases/`,
    method: 'POST',
    auth: {
      user: opts.key,
      password: '',
    },
    body: {
      version: release,
    },
    json: true,
  }).then(function (result) {
    var success = (result.response.statusCode === 201);
    var alreadyCreated = (result.response.statusCode === 400 &&
                          result.body.detail.match(/already exists/));

    if (success || alreadyCreated) {
      return;
    }
    throw new Error(`unable to create release '${release}' in project '${project}'`);
  });
}


/** Upload a named file to a release in Sentry. Returns a Promise. */
function uploadReleaseFile(opts, project, release, file) {
  return httpRequest({
    uri: `${SENTRY_API_ROOT}/projects/${opts.organization}/${project}/releases/${release}/files/`,
    method: 'POST',
    auth: {
      user: opts.key,
      password: '',
    },
    formData: {
      file: fs.createReadStream(file.path),
      name: path.basename(file.path),
    }
  }).then(function (result) {
    if (result.response.statusCode === 201) {
      return;
    }
    throw new Error(`Uploading file failed: ${result.response.statusCode}: ${result.body}`);
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
 * @param {Array[String]} projects - A list of projects to which to upload
 *                                   files.
 * @param {String} release - The name of the release.
 * @return {NodeJS.ReadWriteStream} - A stream into which Vinyl files from
 *                                    gulp.src() etc. can be piped.
 */
module.exports = function uploadToSentry(opts, projects, release) {
  // Create releases in every project
  var releases = projects.map(function (project) {
    gulpUtil.log(`Creating release '${release}' in project '${project}'`);
    return createRelease(opts, project, release);
  });

  return through.obj(function (file, enc, callback) {
    Promise.all(releases)
    .then(function () {
      gulpUtil.log(`Uploading ${path.basename(file.path)}`);
      var uploads = projects.map(function (project) {
        return uploadReleaseFile(opts, project, release, file);
      });

      return Promise.all(uploads);
    })
    .then(function () {
      callback();
    })
    .catch(function (err) {
      gulpUtil.log('Sentry upload failed: ', err);
      callback(err);
    });
  });
};
