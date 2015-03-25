module.exports = function () {
    return function (value) {
        return encodeURIComponent(value);
    };
};
