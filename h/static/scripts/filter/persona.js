module.exports = function () {
    return function (user, part) {
        if (typeof(part) === 'undefined') {
            part = 'username';
        }
        var index = ['term', 'username', 'provider'].indexOf(part);
        var groups = null;

        if (typeof(user) !== 'undefined' && user !== null) {
            groups = user.match(/^acct:([^@]+)@(.+)/);
        }

        if (groups) {
            return groups[index];
        } else if (part !== 'provider') {
            return user;
        }
    };
};
