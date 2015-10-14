/**
 * Parses H account names of the form 'acct:<username>@<provider>'
 * into a {username, provider} object or null if the input does not
 * match the expected form.
 */
function parseAccountID(user) {
  if (!user) {
    return null;
  }
  var match = user.match(/^acct:([^@]+)@(.+)/);
  if (!match) {
    return null;
  }
  return {
    username: match[1],
    provider: match[2],
  };
}

module.exports = {
  parseAccountID: parseAccountID,

  /** Export parseAccountID() as an Angular filter */
  filter: function () {
    return function (user, part) {
      var account = parseAccountID(user);
      if (!account) {
        return null;
      }
      return account[part || 'username'];
    };
  }
};
