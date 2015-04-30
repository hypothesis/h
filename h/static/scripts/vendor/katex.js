(function(e){if("function"==typeof bootstrap)bootstrap("katex",e);else if("object"==typeof exports)module.exports=e();else if("function"==typeof define&&define.amd)define(e);else if("undefined"!=typeof ses){if(!ses.ok())return;ses.makeKatex=e}else"undefined"!=typeof window?window.katex=e():global.katex=e()})(function(){var define,ses,bootstrap,module,exports;
return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
/**
 * This is the main entry point for KaTeX. Here, we expose functions for
 * rendering expressions either to DOM nodes or to markup strings.
 *
 * We also expose the ParseError class to check if errors thrown from KaTeX are
 * errors in the expression, or errors in javascript handling.
 */

var ParseError = require("./src/ParseError");

var buildTree = require("./src/buildTree");
var parseTree = require("./src/parseTree");
var utils = require("./src/utils");

/**
 * Parse and build an expression, and place that expression in the DOM node
 * given.
 */
var render = function(toParse, baseNode) {
    utils.clearNode(baseNode);

    var tree = parseTree(toParse);
    var node = buildTree(tree).toNode();

    baseNode.appendChild(node);
};

// KaTeX's styles don't work properly in quirks mode. Print out an error, and
// disable rendering.
if (typeof document !== "undefined") {
    if (document.compatMode !== "CSS1Compat") {
        typeof console !== "undefined" && console.warn(
            "Warning: KaTeX doesn't work in quirks mode. Make sure your " +
                "website has a suitable doctype.");

        render = function() {
            throw new ParseError("KaTeX doesn't work in quirks mode.");
        };
    }
}

/**
 * Parse and build an expression, and return the markup for that.
 */
var renderToString = function(toParse) {
    var tree = parseTree(toParse);
    return buildTree(tree).toMarkup();
};

module.exports = {
    render: render,
    renderToString: renderToString,
    ParseError: ParseError
};

},{"./src/ParseError":4,"./src/buildTree":8,"./src/parseTree":13,"./src/utils":15}],2:[function(require,module,exports){
/**
 * The Lexer class handles tokenizing the input in various ways. Since our
 * parser expects us to be able to backtrack, the lexer allows lexing from any
 * given starting point.
 *
 * Its main exposed function is the `lex` function, which takes a position to
 * lex from and a type of token to lex. It defers to the appropriate `_innerLex`
 * function.
 *
 * The various `_innerLex` functions perform the actual lexing of different
 * kinds.
 */

var ParseError = require("./ParseError");

// The main lexer class
function Lexer(input) {
    this._input = input;
}

// The resulting token returned from `lex`.
function Token(text, data, position) {
    this.text = text;
    this.data = data;
    this.position = position;
}

// "normal" types of tokens. These are tokens which can be matched by a simple
// regex
var mathNormals = [
    /^[/|@.""`0-9a-zA-Z]/, // ords
    /^[*+-]/, // bins
    /^[=<>:]/, // rels
    /^[,;]/, // punctuation
    /^['\^_{}]/, // misc
    /^[(\[]/, // opens
    /^[)\]?!]/, // closes
    /^~/ // spacing
];

// These are "normal" tokens like above, but should instead be parsed in text
// mode.
var textNormals = [
    /^[a-zA-Z0-9`!@*()-=+\[\]'";:?\/.,]/, // ords
    /^[{}]/, // grouping
    /^~/ // spacing
];

// Regexes for matching whitespace
var whitespaceRegex = /^\s*/;
var whitespaceConcatRegex = /^( +|\\  +)/;

// This regex matches any other TeX function, which is a backslash followed by a
// word or a single symbol
var anyFunc = /^\\(?:[a-zA-Z]+|.)/;

/**
 * This function lexes a single normal token. It takes a position, a list of
 * "normal" tokens to try, and whether it should completely ignore whitespace or
 * not.
 */
Lexer.prototype._innerLex = function(pos, normals, ignoreWhitespace) {
    var input = this._input.slice(pos);
    var whitespace;

    if (ignoreWhitespace) {
        // Get rid of whitespace.
        whitespace = input.match(whitespaceRegex)[0];
        pos += whitespace.length;
        input = input.slice(whitespace.length);
    } else {
        // Do the funky concatenation of whitespace that happens in text mode.
        whitespace = input.match(whitespaceConcatRegex);
        if (whitespace !== null) {
            return new Token(" ", null, pos + whitespace[0].length);
        }
    }

    // If there's no more input to parse, return an EOF token
    if (input.length === 0) {
        return new Token("EOF", null, pos);
    }

    var match;
    if ((match = input.match(anyFunc))) {
        // If we match a function token, return it
        return new Token(match[0], null, pos + match[0].length);
    } else {
        // Otherwise, we look through the normal token regexes and see if it's
        // one of them.
        for (var i = 0; i < normals.length; i++) {
            var normal = normals[i];

            if ((match = input.match(normal))) {
                // If it is, return it
                return new Token(
                    match[0], null, pos + match[0].length);
            }
        }
    }

    throw new ParseError("Unexpected character: '" + input[0] +
        "'", this, pos);
};

// A regex to match a CSS color (like #ffffff or BlueViolet)
var cssColor = /^(#[a-z0-9]+|[a-z]+)/i;

/**
 * This function lexes a CSS color.
 */
Lexer.prototype._innerLexColor = function(pos) {
    var input = this._input.slice(pos);

    // Ignore whitespace
    var whitespace = input.match(whitespaceRegex)[0];
    pos += whitespace.length;
    input = input.slice(whitespace.length);

    var match;
    if ((match = input.match(cssColor))) {
        // If we look like a color, return a color
        return new Token(match[0], null, pos + match[0].length);
    } else {
        throw new ParseError("Invalid color", this, pos);
    }
};

// A regex to match a dimension. Dimensions look like
// "1.2em" or ".4pt" or "1 ex"
var sizeRegex = /^(-?)\s*(\d+(?:\.\d*)?|\.\d+)\s*([a-z]{2})/;

/**
 * This function lexes a dimension.
 */
Lexer.prototype._innerLexSize = function(pos) {
    var input = this._input.slice(pos);

    // Ignore whitespace
    var whitespace = input.match(whitespaceRegex)[0];
    pos += whitespace.length;
    input = input.slice(whitespace.length);

    var match;
    if ((match = input.match(sizeRegex))) {
        var unit = match[3];
        // We only currently handle "em" and "ex" units
        if (unit !== "em" && unit !== "ex") {
            throw new ParseError("Invalid unit: '" + unit + "'", this, pos);
        }
        return new Token(match[0], {
                number: +(match[1] + match[2]),
                unit: unit
            }, pos + match[0].length);
    }

    throw new ParseError("Invalid size", this, pos);
};

/**
 * This function lexes a string of whitespace.
 */
Lexer.prototype._innerLexWhitespace = function(pos) {
    var input = this._input.slice(pos);

    var whitespace = input.match(whitespaceRegex)[0];
    pos += whitespace.length;

    return new Token(whitespace, null, pos);
};

/**
 * This function lexes a single token starting at `pos` and of the given mode.
 * Based on the mode, we defer to one of the `_innerLex` functions.
 */
Lexer.prototype.lex = function(pos, mode) {
    if (mode === "math") {
        return this._innerLex(pos, mathNormals, true);
    } else if (mode === "text") {
        return this._innerLex(pos, textNormals, false);
    } else if (mode === "color") {
        return this._innerLexColor(pos);
    } else if (mode === "size") {
        return this._innerLexSize(pos);
    } else if (mode === "whitespace") {
        return this._innerLexWhitespace(pos);
    }
};

module.exports = Lexer;

},{"./ParseError":4}],3:[function(require,module,exports){
/**
 * This file contains information about the options that the Parser carries
 * around with it while parsing. Data is held in an `Options` object, and when
 * recursing, a new `Options` object can be created with the `.with*` and
 * `.reset` functions.
 */

/**
 * This is the main options class. It contains the style, size, and color of the
 * current parse level. It also contains the style and size of the parent parse
 * level, so size changes can be handled efficiently.
 *
 * Each of the `.with*` and `.reset` functions passes its current style and size
 * as the parentStyle and parentSize of the new options class, so parent
 * handling is taken care of automatically.
 */
function Options(style, size, color, parentStyle, parentSize) {
    this.style = style;
    this.color = color;
    this.size = size;

    if (parentStyle === undefined) {
        parentStyle = style;
    }
    this.parentStyle = parentStyle;

    if (parentSize === undefined) {
        parentSize = size;
    }
    this.parentSize = parentSize;
}

/**
 * Create a new options object with the given style.
 */
Options.prototype.withStyle = function(style) {
    return new Options(style, this.size, this.color, this.style, this.size);
};

/**
 * Create a new options object with the given size.
 */
Options.prototype.withSize = function(size) {
    return new Options(this.style, size, this.color, this.style, this.size);
};

/**
 * Create a new options object with the given color.
 */
Options.prototype.withColor = function(color) {
    return new Options(this.style, this.size, color, this.style, this.size);
};

/**
 * Create a new options object with the same style, size, and color. This is
 * used so that parent style and size changes are handled correctly.
 */
Options.prototype.reset = function() {
    return new Options(
        this.style, this.size, this.color, this.style, this.size);
};

/**
 * A map of color names to CSS colors.
 * TODO(emily): Remove this when we have real macros
 */
var colorMap = {
    "katex-blue": "#6495ed",
    "katex-orange": "#ffa500",
    "katex-pink": "#ff00af",
    "katex-red": "#df0030",
    "katex-green": "#28ae7b",
    "katex-gray": "gray",
    "katex-purple": "#9d38bd"
};

/**
 * Gets the CSS color of the current options object, accounting for the
 * `colorMap`.
 */
Options.prototype.getColor = function() {
    return colorMap[this.color] || this.color;
};

module.exports = Options;

},{}],4:[function(require,module,exports){
/**
 * This is the ParseError class, which is the main error thrown by KaTeX
 * functions when something has gone wrong. This is used to distinguish internal
 * errors from errors in the expression that the user provided.
 */
function ParseError(message, lexer, position) {
    var error = "KaTeX parse error: " + message;

    if (lexer !== undefined && position !== undefined) {
        // If we have the input and a position, make the error a bit fancier

        // Prepend some information
        error += " at position " + position + ": ";

        // Get the input
        var input = lexer._input;
        // Insert a combining underscore at the correct position
        input = input.slice(0, position) + "\u0332" +
            input.slice(position);

        // Extract some context from the input and add it to the error
        var begin = Math.max(0, position - 15);
        var end = position + 15;
        error += input.slice(begin, end);
    }

    // Some hackery to make ParseError a prototype of Error
    // See http://stackoverflow.com/a/8460753
    var self = new Error(error);
    self.name = "ParseError";
    self.__proto__ = ParseError.prototype;

    self.position = position;
    return self;
}

// More hackery
ParseError.prototype.__proto__ = Error.prototype;

module.exports = ParseError;

},{}],5:[function(require,module,exports){
var functions = require("./functions");
var Lexer = require("./Lexer");
var symbols = require("./symbols");
var utils = require("./utils");

var ParseError = require("./ParseError");

/**
 * This file contains the parser used to parse out a TeX expression from the
 * input. Since TeX isn't context-free, standard parsers don't work particularly
 * well.
 *
 * The strategy of this parser is as such:
 *
 * The main functions (the `.parse...` ones) take a position in the current
 * parse string to parse tokens from. The lexer (found in Lexer.js, stored at
 * this.lexer) also supports pulling out tokens at arbitrary places. When
 * individual tokens are needed at a position, the lexer is called to pull out a
 * token, which is then used.
 *
 * The main functions also take a mode that the parser is currently in
 * (currently "math" or "text"), which denotes whether the current environment
 * is a math-y one or a text-y one (e.g. inside \text). Currently, this serves
 * to limit the functions which can be used in text mode.
 *
 * The main functions then return an object which contains the useful data that
 * was parsed at its given point, and a new position at the end of the parsed
 * data. The main functions can call each other and continue the parsing by
 * using the returned position as a new starting point.
 *
 * There are also extra `.handle...` functions, which pull out some reused
 * functionality into self-contained functions.
 *
 * The earlier functions return `ParseResult`s, which contain a ParseNode and a
 * new position.
 *
 * The later functions (which are called deeper in the parse) sometimes return
 * ParseFuncOrArgument, which contain a ParseResult as well as some data about
 * whether the parsed object is a function which is missing some arguments, or a
 * standalone object which can be used as an argument to another function.
 */

/**
 * Main Parser class
 */
function Parser(input) {
    // Make a new lexer
    this.lexer = new Lexer(input);
}

/**
 * The resulting parse tree nodes of the parse tree.
 */
function ParseNode(type, value, mode) {
    this.type = type;
    this.value = value;
    this.mode = mode;
}

/**
 * A result and final position returned by the `.parse...` functions.
 */
function ParseResult(result, newPosition) {
    this.result = result;
    this.position = newPosition;
}

/**
 * An initial function (without its arguments), or an argument to a function.
 * The `result` argument should be a ParseResult.
 */
function ParseFuncOrArgument(result, isFunction, allowedInText, numArgs, numOptionalArgs, argTypes) {
    this.result = result;
    // Is this a function (i.e. is it something defined in functions.js)?
    this.isFunction = isFunction;
    // Is it allowed in text mode?
    this.allowedInText = allowedInText;
    // How many arguments?
    this.numArgs = numArgs;
    // How many optional arguments?
    this.numOptionalArgs = numOptionalArgs;
    // What types of arguments?
    this.argTypes = argTypes;
}

/**
 * Checks a result to make sure it has the right type, and throws an
 * appropriate error otherwise.
 */
Parser.prototype.expect = function(result, text) {
    if (result.text !== text) {
        throw new ParseError(
            "Expected '" + text + "', got '" + result.text + "'",
            this.lexer, result.position
        );
    }
};

/**
 * Main parsing function, which parses an entire input.
 *
 * @return {?Array.<ParseNode>}
 */
Parser.prototype.parse = function(input) {
    // Try to parse the input
    var parse = this.parseInput(0, "math");
    return parse.result;
};

/**
 * Parses an entire input tree.
 */
Parser.prototype.parseInput = function(pos, mode) {
    // Parse an expression
    var expression = this.parseExpression(pos, mode, false, null);
    // If we succeeded, make sure there's an EOF at the end
    var EOF = this.lexer.lex(expression.position, mode);
    this.expect(EOF, "EOF");
    return expression;
};

/**
 * Parses an "expression", which is a list of atoms.
 *
 * @param {boolean} breakOnInfix Should the parsing stop when we hit infix
 *                  nodes? This happens when functions have higher precendence
 *                  than infix nodes in implicit parses.
 *
 * @param {?string} breakOnToken The token that the expression should end with,
 *                  or `null` if something else should end the expression.
 *
 * @return {ParseResult}
 */
Parser.prototype.parseExpression = function(pos, mode, breakOnInfix, breakOnToken) {
    var body = [];
    // Keep adding atoms to the body until we can't parse any more atoms (either
    // we reached the end, a }, or a \right)
    while (true) {
        var lex = this.lexer.lex(pos, mode);
        if (breakOnToken != null && lex.text === breakOnToken) {
            break;
        }
        var atom = this.parseAtom(pos, mode);
        if (!atom) {
            break;
        }
        if (breakOnInfix && atom.result.type === "infix") {
            break;
        }
        body.push(atom.result);
        pos = atom.position;
    }
    return new ParseResult(this.handleInfixNodes(body, mode), pos);
};

/**
 * Rewrites infix operators such as \over with corresponding commands such
 * as \frac.
 *
 * There can only be one infix operator per group.  If there's more than one
 * then the expression is ambiguous.  This can be resolved by adding {}.
 *
 * @returns {Array}
 */
Parser.prototype.handleInfixNodes = function (body, mode) {
    var overIndex = -1;
    var func;
    var funcName;

    for (var i = 0; i < body.length; i++) {
        var node = body[i];
        if (node.type === "infix") {
            if (overIndex !== -1) {
                throw new ParseError("only one infix operator per group",
                    this.lexer, -1);
            }
            overIndex = i;
            funcName = node.value.replaceWith;
            func = functions.funcs[funcName];
        }
    }

    if (overIndex !== -1) {
        var numerNode, denomNode;

        var numerBody = body.slice(0, overIndex);
        var denomBody = body.slice(overIndex + 1);

        if (numerBody.length === 1 && numerBody[0].type === "ordgroup") {
            numerNode = numerBody[0];
        } else {
            numerNode = new ParseNode("ordgroup", numerBody, mode);
        }

        if (denomBody.length === 1 && denomBody[0].type === "ordgroup") {
            denomNode = denomBody[0];
        } else {
            denomNode = new ParseNode("ordgroup", denomBody, mode);
        }

        var value = func.handler(funcName, numerNode, denomNode);
        return [new ParseNode(value.type, value, mode)];
    } else {
        return body;
    }
};

// The greediness of a superscript or subscript
var SUPSUB_GREEDINESS = 1;

/**
 * Handle a subscript or superscript with nice errors.
 */
Parser.prototype.handleSupSubscript = function(pos, mode, symbol, name) {
    var group = this.parseGroup(pos, mode);

    if (!group) {
        throw new ParseError(
            "Expected group after '" + symbol + "'", this.lexer, pos);
    } else if (group.numArgs > 0) {
        // ^ and _ have a greediness, so handle interactions with functions'
        // greediness
        var funcGreediness = functions.getGreediness(group.result.result);
        if (funcGreediness > SUPSUB_GREEDINESS) {
            return this.parseFunction(pos, mode);
        } else {
            throw new ParseError(
                "Got function '" + group.result.result + "' with no arguments " +
                    "as " + name,
                this.lexer, pos);
        }
    } else {
        return group.result;
    }
};

/**
 * Parses a group with optional super/subscripts.
 *
 * @return {?ParseResult}
 */
Parser.prototype.parseAtom = function(pos, mode) {
    // The body of an atom is an implicit group, so that things like
    // \left(x\right)^2 work correctly.
    var base = this.parseImplicitGroup(pos, mode);

    // In text mode, we don't have superscripts or subscripts
    if (mode === "text") {
        return base;
    }

    // Handle an empty base
    var currPos;
    if (!base) {
        currPos = pos;
        base = undefined;
    } else {
        currPos = base.position;
    }

    var superscript;
    var subscript;
    var result;
    while (true) {
        // Lex the first token
        var lex = this.lexer.lex(currPos, mode);

        if (lex.text === "^") {
            // We got a superscript start
            if (superscript) {
                throw new ParseError(
                    "Double superscript", this.lexer, currPos);
            }
            result = this.handleSupSubscript(
                lex.position, mode, lex.text, "superscript");
            currPos = result.position;
            superscript = result.result;
        } else if (lex.text === "_") {
            // We got a subscript start
            if (subscript) {
                throw new ParseError(
                    "Double subscript", this.lexer, currPos);
            }
            result = this.handleSupSubscript(
                lex.position, mode, lex.text, "subscript");
            currPos = result.position;
            subscript = result.result;
        } else if (lex.text === "'") {
            // We got a prime
            var prime = new ParseNode("textord", "\\prime", mode);

            // Many primes can be grouped together, so we handle this here
            var primes = [prime];
            currPos = lex.position;
            // Keep lexing tokens until we get something that's not a prime
            while ((lex = this.lexer.lex(currPos, mode)).text === "'") {
                // For each one, add another prime to the list
                primes.push(prime);
                currPos = lex.position;
            }
            // Put them into an ordgroup as the superscript
            superscript = new ParseNode("ordgroup", primes, mode);
        } else {
            // If it wasn't ^, _, or ', stop parsing super/subscripts
            break;
        }
    }

    if (superscript || subscript) {
        // If we got either a superscript or subscript, create a supsub
        return new ParseResult(
            new ParseNode("supsub", {
                base: base && base.result,
                sup: superscript,
                sub: subscript
            }, mode),
            currPos);
    } else {
        // Otherwise return the original body
        return base;
    }
};

// A list of the size-changing functions, for use in parseImplicitGroup
var sizeFuncs = [
    "\\tiny", "\\scriptsize", "\\footnotesize", "\\small", "\\normalsize",
    "\\large", "\\Large", "\\LARGE", "\\huge", "\\Huge"
];

// A list of the style-changing functions, for use in parseImplicitGroup
var styleFuncs = [
    "\\displaystyle", "\\textstyle", "\\scriptstyle", "\\scriptscriptstyle"
];

/**
 * Parses an implicit group, which is a group that starts at the end of a
 * specified, and ends right before a higher explicit group ends, or at EOL. It
 * is used for functions that appear to affect the current style, like \Large or
 * \textrm, where instead of keeping a style we just pretend that there is an
 * implicit grouping after it until the end of the group. E.g.
 *   small text {\Large large text} small text again
 * It is also used for \left and \right to get the correct grouping.
 *
 * @return {?ParseResult}
 */
Parser.prototype.parseImplicitGroup = function(pos, mode) {
    var start = this.parseSymbol(pos, mode);

    if (!start || !start.result) {
        // If we didn't get anything we handle, fall back to parseFunction
        return this.parseFunction(pos, mode);
    }

    var func = start.result.result;
    var body;

    if (func === "\\left") {
        // If we see a left:
        // Parse the entire left function (including the delimiter)
        var left = this.parseFunction(pos, mode);
        // Parse out the implicit body
        body = this.parseExpression(left.position, mode, false, "}");
        // Check the next token
        var rightLex = this.parseSymbol(body.position, mode);

        if (rightLex && rightLex.result.result === "\\right") {
            // If it's a \right, parse the entire right function (including the delimiter)
            var right = this.parseFunction(body.position, mode);

            return new ParseResult(
                new ParseNode("leftright", {
                    body: body.result,
                    left: left.result.value.value,
                    right: right.result.value.value
                }, mode),
                right.position);
        } else {
            throw new ParseError("Missing \\right", this.lexer, body.position);
        }
    } else if (func === "\\right") {
        // If we see a right, explicitly fail the parsing here so the \left
        // handling ends the group
        return null;
    } else if (utils.contains(sizeFuncs, func)) {
        // If we see a sizing function, parse out the implict body
        body = this.parseExpression(start.result.position, mode, false, "}");
        return new ParseResult(
            new ParseNode("sizing", {
                // Figure out what size to use based on the list of functions above
                size: "size" + (utils.indexOf(sizeFuncs, func) + 1),
                value: body.result
            }, mode),
            body.position);
    } else if (utils.contains(styleFuncs, func)) {
        // If we see a styling function, parse out the implict body
        body = this.parseExpression(start.result.position, mode, true, "}");
        return new ParseResult(
            new ParseNode("styling", {
                // Figure out what style to use by pulling out the style from
                // the function name
                style: func.slice(1, func.length - 5),
                value: body.result
            }, mode),
            body.position);
    } else {
        // Defer to parseFunction if it's not a function we handle
        return this.parseFunction(pos, mode);
    }
};

/**
 * Parses an entire function, including its base and all of its arguments
 *
 * @return {?ParseResult}
 */
Parser.prototype.parseFunction = function(pos, mode) {
    var baseGroup = this.parseGroup(pos, mode);

    if (baseGroup) {
        if (baseGroup.isFunction) {
            var func = baseGroup.result.result;
            if (mode === "text" && !baseGroup.allowedInText) {
                throw new ParseError(
                    "Can't use function '" + func + "' in text mode",
                    this.lexer, baseGroup.position);
            }

            var newPos = baseGroup.result.position;
            var result;

            var totalArgs = baseGroup.numArgs + baseGroup.numOptionalArgs;

            if (totalArgs > 0) {
                var baseGreediness = functions.getGreediness(func);
                var args = [func];
                var positions = [newPos];

                for (var i = 0; i < totalArgs; i++) {
                    var argType = baseGroup.argTypes && baseGroup.argTypes[i];
                    var arg;
                    if (i < baseGroup.numOptionalArgs) {
                        if (argType) {
                            arg = this.parseSpecialGroup(newPos, argType, mode, true);
                        } else {
                            arg = this.parseOptionalGroup(newPos, mode);
                        }
                        if (!arg) {
                            args.push(null);
                            positions.push(newPos);
                            continue;
                        }
                    } else {
                        if (argType) {
                            arg = this.parseSpecialGroup(newPos, argType, mode);
                        } else {
                            arg = this.parseGroup(newPos, mode);
                        }
                        if (!arg) {
                            throw new ParseError(
                                "Expected group after '" + baseGroup.result.result +
                                    "'",
                                this.lexer, newPos);
                        }
                    }
                    var argNode;
                    if (arg.numArgs > 0) {
                        var argGreediness = functions.getGreediness(arg.result.result);
                        if (argGreediness > baseGreediness) {
                            argNode = this.parseFunction(newPos, mode);
                        } else {
                            throw new ParseError(
                                "Got function '" + arg.result.result + "' as " +
                                    "argument to function '" +
                                    baseGroup.result.result + "'",
                                this.lexer, arg.result.position - 1);
                        }
                    } else {
                        argNode = arg.result;
                    }
                    args.push(argNode.result);
                    positions.push(argNode.position);
                    newPos = argNode.position;
                }

                args.push(positions);

                result = functions.funcs[func].handler.apply(this, args);
            } else {
                result = functions.funcs[func].handler.apply(this, [func]);
            }

            return new ParseResult(
                new ParseNode(result.type, result, mode),
                newPos);
        } else {
            return baseGroup.result;
        }
    } else {
        return null;
    }
};

/**
 * Parses a group when the mode is changing. Takes a position, a new mode, and
 * an outer mode that is used to parse the outside.
 *
 * @return {?ParseFuncOrArgument}
 */
Parser.prototype.parseSpecialGroup = function(pos, mode, outerMode, optional) {
    if (mode === "color" || mode === "size") {
        // color and size modes are special because they should have braces and
        // should only lex a single symbol inside
        var openBrace = this.lexer.lex(pos, outerMode);
        if (optional && openBrace.text !== "[") {
            // optional arguments should return null if they don't exist
            return null;
        }
        this.expect(openBrace, optional ? "[" : "{");
        var inner = this.lexer.lex(openBrace.position, mode);
        var data;
        if (mode === "color") {
            data = inner.text;
        } else {
            data = inner.data;
        }
        var closeBrace = this.lexer.lex(inner.position, outerMode);
        this.expect(closeBrace, optional ? "]" : "}");
        return new ParseFuncOrArgument(
            new ParseResult(
                new ParseNode(mode, data, outerMode),
                closeBrace.position),
            false);
    } else if (mode === "text") {
        // text mode is special because it should ignore the whitespace before
        // it
        var whitespace = this.lexer.lex(pos, "whitespace");
        pos = whitespace.position;
    }

    if (optional) {
        return this.parseOptionalGroup(pos, mode);
    } else {
        return this.parseGroup(pos, mode);
    }
};

/**
 * Parses a group, which is either a single nucleus (like "x") or an expression
 * in braces (like "{x+y}")
 *
 * @return {?ParseFuncOrArgument}
 */
Parser.prototype.parseGroup = function(pos, mode) {
    var start = this.lexer.lex(pos, mode);
    // Try to parse an open brace
    if (start.text === "{") {
        // If we get a brace, parse an expression
        var expression = this.parseExpression(start.position, mode, false, "}");
        // Make sure we get a close brace
        var closeBrace = this.lexer.lex(expression.position, mode);
        this.expect(closeBrace, "}");
        return new ParseFuncOrArgument(
            new ParseResult(
                new ParseNode("ordgroup", expression.result, mode),
                closeBrace.position),
            false);
    } else {
        // Otherwise, just return a nucleus
        return this.parseSymbol(pos, mode);
    }
};

/**
 * Parses a group, which is an expression in brackets (like "[x+y]")
 *
 * @return {?ParseFuncOrArgument}
 */
Parser.prototype.parseOptionalGroup = function(pos, mode) {
    var start = this.lexer.lex(pos, mode);
    // Try to parse an open bracket
    if (start.text === "[") {
        // If we get a brace, parse an expression
        var expression = this.parseExpression(start.position, mode, false, "]");
        // Make sure we get a close bracket
        var closeBracket = this.lexer.lex(expression.position, mode);
        this.expect(closeBracket, "]");
        return new ParseFuncOrArgument(
            new ParseResult(
                new ParseNode("ordgroup", expression.result, mode),
                closeBracket.position),
            false);
    } else {
        // Otherwise, return null,
        return null;
    }
};

/**
 * Parse a single symbol out of the string. Here, we handle both the functions
 * we have defined, as well as the single character symbols
 *
 * @return {?ParseFuncOrArgument}
 */
Parser.prototype.parseSymbol = function(pos, mode) {
    var nucleus = this.lexer.lex(pos, mode);

    if (functions.funcs[nucleus.text]) {
        // If there is a function with this name, we use its data
        var func = functions.funcs[nucleus.text];

        // Here, we replace "original" argTypes with the current mode
        var argTypes = func.argTypes;
        if (argTypes) {
            argTypes = argTypes.slice();
            for (var i = 0; i < argTypes.length; i++) {
                if (argTypes[i] === "original") {
                    argTypes[i] = mode;
                }
            }
        }

        return new ParseFuncOrArgument(
            new ParseResult(nucleus.text, nucleus.position),
            true, func.allowedInText, func.numArgs, func.numOptionalArgs, argTypes);
    } else if (symbols[mode][nucleus.text]) {
        // Otherwise if this is a no-argument function, find the type it
        // corresponds to in the symbols map
        return new ParseFuncOrArgument(
            new ParseResult(
                new ParseNode(symbols[mode][nucleus.text].group,
                              nucleus.text, mode),
                nucleus.position),
            false);
    } else {
        return null;
    }
};

module.exports = Parser;

},{"./Lexer":2,"./ParseError":4,"./functions":12,"./symbols":14,"./utils":15}],6:[function(require,module,exports){
/**
 * This file contains information and classes for the various kinds of styles
 * used in TeX. It provides a generic `Style` class, which holds information
 * about a specific style. It then provides instances of all the different kinds
 * of styles possible, and provides functions to move between them and get
 * information about them.
 */

/**
 * The main style class. Contains a unique id for the style, a size (which is
 * the same for cramped and uncramped version of a style), a cramped flag, and a
 * size multiplier, which gives the size difference between a style and
 * textstyle.
 */
function Style(id, size, multiplier, cramped) {
    this.id = id;
    this.size = size;
    this.cramped = cramped;
    this.sizeMultiplier = multiplier;
}

/**
 * Get the style of a superscript given a base in the current style.
 */
Style.prototype.sup = function() {
    return styles[sup[this.id]];
};

/**
 * Get the style of a subscript given a base in the current style.
 */
Style.prototype.sub = function() {
    return styles[sub[this.id]];
};

/**
 * Get the style of a fraction numerator given the fraction in the current
 * style.
 */
Style.prototype.fracNum = function() {
    return styles[fracNum[this.id]];
};

/**
 * Get the style of a fraction denominator given the fraction in the current
 * style.
 */
Style.prototype.fracDen = function() {
    return styles[fracDen[this.id]];
};

/**
 * Get the cramped version of a style (in particular, cramping a cramped style
 * doesn't change the style).
 */
Style.prototype.cramp = function() {
    return styles[cramp[this.id]];
};

/**
 * HTML class name, like "displaystyle cramped"
 */
Style.prototype.cls = function() {
    return sizeNames[this.size] + (this.cramped ? " cramped" : " uncramped");
};

/**
 * HTML Reset class name, like "reset-textstyle"
 */
Style.prototype.reset = function() {
    return resetNames[this.size];
};

// IDs of the different styles
var D = 0;
var Dc = 1;
var T = 2;
var Tc = 3;
var S = 4;
var Sc = 5;
var SS = 6;
var SSc = 7;

// String names for the different sizes
var sizeNames = [
    "displaystyle textstyle",
    "textstyle",
    "scriptstyle",
    "scriptscriptstyle"
];

// Reset names for the different sizes
var resetNames = [
    "reset-textstyle",
    "reset-textstyle",
    "reset-scriptstyle",
    "reset-scriptscriptstyle"
];

// Instances of the different styles
var styles = [
    new Style(D, 0, 1.0, false),
    new Style(Dc, 0, 1.0, true),
    new Style(T, 1, 1.0, false),
    new Style(Tc, 1, 1.0, true),
    new Style(S, 2, 0.7, false),
    new Style(Sc, 2, 0.7, true),
    new Style(SS, 3, 0.5, false),
    new Style(SSc, 3, 0.5, true)
];

// Lookup tables for switching from one style to another
var sup = [S, Sc, S, Sc, SS, SSc, SS, SSc];
var sub = [Sc, Sc, Sc, Sc, SSc, SSc, SSc, SSc];
var fracNum = [T, Tc, S, Sc, SS, SSc, SS, SSc];
var fracDen = [Tc, Tc, Sc, Sc, SSc, SSc, SSc, SSc];
var cramp = [Dc, Dc, Tc, Tc, Sc, Sc, SSc, SSc];

// We only export some of the styles. Also, we don't export the `Style` class so
// no more styles can be generated.
module.exports = {
    DISPLAY: styles[D],
    TEXT: styles[T],
    SCRIPT: styles[S],
    SCRIPTSCRIPT: styles[SS]
};

},{}],7:[function(require,module,exports){
/**
 * This module contains general functions that can be used for building
 * different kinds of domTree nodes in a consistent manner.
 */

var domTree = require("./domTree");
var fontMetrics = require("./fontMetrics");
var symbols = require("./symbols");

/**
 * Makes a symbolNode after translation via the list of symbols in symbols.js.
 * Correctly pulls out metrics for the character, and optionally takes a list of
 * classes to be attached to the node.
 */
var makeSymbol = function(value, style, mode, color, classes) {
    // Replace the value with its replaced value from symbol.js
    if (symbols[mode][value] && symbols[mode][value].replace) {
        value = symbols[mode][value].replace;
    }

    var metrics = fontMetrics.getCharacterMetrics(value, style);

    var symbolNode;
    if (metrics) {
        symbolNode = new domTree.symbolNode(
            value, metrics.height, metrics.depth, metrics.italic, metrics.skew,
            classes);
    } else {
        // TODO(emily): Figure out a good way to only print this in development
        typeof console !== "undefined" && console.warn(
            "No character metrics for '" + value + "' in style '" +
                style + "'");
        symbolNode = new domTree.symbolNode(value, 0, 0, 0, 0, classes);
    }

    if (color) {
        symbolNode.style.color = color;
    }

    return symbolNode;
};

/**
 * Makes a symbol in the italic math font.
 */
var mathit = function(value, mode, color, classes) {
    return makeSymbol(
        value, "Math-Italic", mode, color, classes.concat(["mathit"]));
};

/**
 * Makes a symbol in the upright roman font.
 */
var mathrm = function(value, mode, color, classes) {
    // Decide what font to render the symbol in by its entry in the symbols
    // table.
    if (symbols[mode][value].font === "main") {
        return makeSymbol(value, "Main-Regular", mode, color, classes);
    } else {
        return makeSymbol(
            value, "AMS-Regular", mode, color, classes.concat(["amsrm"]));
    }
};

/**
 * Calculate the height, depth, and maxFontSize of an element based on its
 * children.
 */
var sizeElementFromChildren = function(elem) {
    var height = 0;
    var depth = 0;
    var maxFontSize = 0;

    if (elem.children) {
        for (var i = 0; i < elem.children.length; i++) {
            if (elem.children[i].height > height) {
                height = elem.children[i].height;
            }
            if (elem.children[i].depth > depth) {
                depth = elem.children[i].depth;
            }
            if (elem.children[i].maxFontSize > maxFontSize) {
                maxFontSize = elem.children[i].maxFontSize;
            }
        }
    }

    elem.height = height;
    elem.depth = depth;
    elem.maxFontSize = maxFontSize;
};

/**
 * Makes a span with the given list of classes, list of children, and color.
 */
var makeSpan = function(classes, children, color) {
    var span = new domTree.span(classes, children);

    sizeElementFromChildren(span);

    if (color) {
        span.style.color = color;
    }

    return span;
};

/**
 * Makes a document fragment with the given list of children.
 */
var makeFragment = function(children) {
    var fragment = new domTree.documentFragment(children);

    sizeElementFromChildren(fragment);

    return fragment;
};

/**
 * Makes an element placed in each of the vlist elements to ensure that each
 * element has the same max font size. To do this, we create a zero-width space
 * with the correct font size.
 */
var makeFontSizer = function(options, fontSize) {
    var fontSizeInner = makeSpan([], [new domTree.symbolNode("\u200b")]);
    fontSizeInner.style.fontSize = (fontSize / options.style.sizeMultiplier) + "em";

    var fontSizer = makeSpan(
        ["fontsize-ensurer", "reset-" + options.size, "size5"],
        [fontSizeInner]);

    return fontSizer;
};

/**
 * Makes a vertical list by stacking elements and kerns on top of each other.
 * Allows for many different ways of specifying the positioning method.
 *
 * Arguments:
 *  - children: A list of child or kern nodes to be stacked on top of each other
 *              (i.e. the first element will be at the bottom, and the last at
 *              the top). Element nodes are specified as
 *                {type: "elem", elem: node}
 *              while kern nodes are specified as
 *                {type: "kern", size: size}
 *  - positionType: The method by which the vlist should be positioned. Valid
 *                  values are:
 *                   - "individualShift": The children list only contains elem
 *                                        nodes, and each node contains an extra
 *                                        "shift" value of how much it should be
 *                                        shifted (note that shifting is always
 *                                        moving downwards). positionData is
 *                                        ignored.
 *                   - "top": The positionData specifies the topmost point of
 *                            the vlist (note this is expected to be a height,
 *                            so positive values move up)
 *                   - "bottom": The positionData specifies the bottommost point
 *                               of the vlist (note this is expected to be a
 *                               depth, so positive values move down
 *                   - "shift": The vlist will be positioned such that its
 *                              baseline is positionData away from the baseline
 *                              of the first child. Positive values move
 *                              downwards.
 *                   - "firstBaseline": The vlist will be positioned such that
 *                                      its baseline is aligned with the
 *                                      baseline of the first child.
 *                                      positionData is ignored. (this is
 *                                      equivalent to "shift" with
 *                                      positionData=0)
 *  - positionData: Data used in different ways depending on positionType
 *  - options: An Options object
 *
 */
var makeVList = function(children, positionType, positionData, options) {
    var depth;
    var currPos;
    var i;
    if (positionType === "individualShift") {
        var oldChildren = children;
        children = [oldChildren[0]];

        // Add in kerns to the list of children to get each element to be
        // shifted to the correct specified shift
        depth = -oldChildren[0].shift - oldChildren[0].elem.depth;
        currPos = depth;
        for (i = 1; i < oldChildren.length; i++) {
            var diff = -oldChildren[i].shift - currPos -
                oldChildren[i].elem.depth;
            var size = diff -
                (oldChildren[i - 1].elem.height +
                 oldChildren[i - 1].elem.depth);

            currPos = currPos + diff;

            children.push({type: "kern", size: size});
            children.push(oldChildren[i]);
        }
    } else if (positionType === "top") {
        // We always start at the bottom, so calculate the bottom by adding up
        // all the sizes
        var bottom = positionData;
        for (i = 0; i < children.length; i++) {
            if (children[i].type === "kern") {
                bottom -= children[i].size;
            } else {
                bottom -= children[i].elem.height + children[i].elem.depth;
            }
        }
        depth = bottom;
    } else if (positionType === "bottom") {
        depth = -positionData;
    } else if (positionType === "shift") {
        depth = -children[0].elem.depth - positionData;
    } else if (positionType === "firstBaseline") {
        depth = -children[0].elem.depth;
    } else {
        depth = 0;
    }

    // Make the fontSizer
    var maxFontSize = 0;
    for (i = 0; i < children.length; i++) {
        if (children[i].type === "elem") {
            maxFontSize = Math.max(maxFontSize, children[i].elem.maxFontSize);
        }
    }
    var fontSizer = makeFontSizer(options, maxFontSize);

    // Create a new list of actual children at the correct offsets
    var realChildren = [];
    currPos = depth;
    for (i = 0; i < children.length; i++) {
        if (children[i].type === "kern") {
            currPos += children[i].size;
        } else {
            var child = children[i].elem;

            var shift = -child.depth - currPos;
            currPos += child.height + child.depth;

            var childWrap = makeSpan([], [fontSizer, child]);
            childWrap.height -= shift;
            childWrap.depth += shift;
            childWrap.style.top = shift + "em";

            realChildren.push(childWrap);
        }
    }

    // Add in an element at the end with no offset to fix the calculation of
    // baselines in some browsers (namely IE, sometimes safari)
    var baselineFix = makeSpan(
        ["baseline-fix"], [fontSizer, new domTree.symbolNode("\u200b")]);
    realChildren.push(baselineFix);

    var vlist = makeSpan(["vlist"], realChildren);
    // Fix the final height and depth, in case there were kerns at the ends
    // since the makeSpan calculation won't take that in to account.
    vlist.height = Math.max(currPos, vlist.height);
    vlist.depth = Math.max(-depth, vlist.depth);
    return vlist;
};

module.exports = {
    makeSymbol: makeSymbol,
    mathit: mathit,
    mathrm: mathrm,
    makeSpan: makeSpan,
    makeFragment: makeFragment,
    makeVList: makeVList
};

},{"./domTree":10,"./fontMetrics":11,"./symbols":14}],8:[function(require,module,exports){
/**
 * This file does the main work of building a domTree structure from a parse
 * tree. The entry point is the `buildTree` function, which takes a parse tree.
 * Then, the buildExpression, buildGroup, and various groupTypes functions are
 * called, to produce a final tree.
 */

var Options = require("./Options");
var ParseError = require("./ParseError");
var Style = require("./Style");

var buildCommon = require("./buildCommon");
var delimiter = require("./delimiter");
var domTree = require("./domTree");
var fontMetrics = require("./fontMetrics");
var utils = require("./utils");

var makeSpan = buildCommon.makeSpan;

/**
 * Take a list of nodes, build them in order, and return a list of the built
 * nodes. This function handles the `prev` node correctly, and passes the
 * previous element from the list as the prev of the next element.
 */
var buildExpression = function(expression, options, prev) {
    var groups = [];
    for (var i = 0; i < expression.length; i++) {
        var group = expression[i];
        groups.push(buildGroup(group, options, prev));
        prev = group;
    }
    return groups;
};

// List of types used by getTypeOfGroup
var groupToType = {
    mathord: "mord",
    textord: "mord",
    bin: "mbin",
    rel: "mrel",
    text: "mord",
    open: "mopen",
    close: "mclose",
    inner: "minner",
    frac: "minner",
    spacing: "mord",
    punct: "mpunct",
    ordgroup: "mord",
    op: "mop",
    katex: "mord",
    overline: "mord",
    rule: "mord",
    leftright: "minner",
    sqrt: "mord",
    accent: "mord"
};

/**
 * Gets the final math type of an expression, given its group type. This type is
 * used to determine spacing between elements, and affects bin elements by
 * causing them to change depending on what types are around them. This type
 * must be attached to the outermost node of an element as a CSS class so that
 * spacing with its surrounding elements works correctly.
 *
 * Some elements can be mapped one-to-one from group type to math type, and
 * those are listed in the `groupToType` table.
 *
 * Others (usually elements that wrap around other elements) often have
 * recursive definitions, and thus call `getTypeOfGroup` on their inner
 * elements.
 */
var getTypeOfGroup = function(group) {
    if (group == null) {
        // Like when typesetting $^3$
        return groupToType.mathord;
    } else if (group.type === "supsub") {
        return getTypeOfGroup(group.value.base);
    } else if (group.type === "llap" || group.type === "rlap") {
        return getTypeOfGroup(group.value);
    } else if (group.type === "color") {
        return getTypeOfGroup(group.value.value);
    } else if (group.type === "sizing") {
        return getTypeOfGroup(group.value.value);
    } else if (group.type === "styling") {
        return getTypeOfGroup(group.value.value);
    } else if (group.type === "delimsizing") {
        return groupToType[group.value.delimType];
    } else {
        return groupToType[group.type];
    }
};

/**
 * Sometimes, groups perform special rules when they have superscripts or
 * subscripts attached to them. This function lets the `supsub` group know that
 * its inner element should handle the superscripts and subscripts instead of
 * handling them itself.
 */
var shouldHandleSupSub = function(group, options) {
    if (!group) {
        return false;
    } else if (group.type === "op") {
        // Operators handle supsubs differently when they have limits
        // (e.g. `\displaystyle\sum_2^3`)
        return group.value.limits && options.style.size === Style.DISPLAY.size;
    } else if (group.type === "accent") {
        return isCharacterBox(group.value.base);
    } else {
        return null;
    }
};

/**
 * Sometimes we want to pull out the innermost element of a group. In most
 * cases, this will just be the group itself, but when ordgroups and colors have
 * a single element, we want to pull that out.
 */
var getBaseElem = function(group) {
    if (!group) {
        return false;
    } else if (group.type === "ordgroup") {
        if (group.value.length === 1) {
            return getBaseElem(group.value[0]);
        } else {
            return group;
        }
    } else if (group.type === "color") {
        if (group.value.value.length === 1) {
            return getBaseElem(group.value.value[0]);
        } else {
            return group;
        }
    } else {
        return group;
    }
};

/**
 * TeXbook algorithms often reference "character boxes", which are simply groups
 * with a single character in them. To decide if something is a character box,
 * we find its innermost group, and see if it is a single character.
 */
var isCharacterBox = function(group) {
    var baseElem = getBaseElem(group);

    // These are all they types of groups which hold single characters
    return baseElem.type === "mathord" ||
        baseElem.type === "textord" ||
        baseElem.type === "bin" ||
        baseElem.type === "rel" ||
        baseElem.type === "inner" ||
        baseElem.type === "open" ||
        baseElem.type === "close" ||
        baseElem.type === "punct";
};

/**
 * This is a map of group types to the function used to handle that type.
 * Simpler types come at the beginning, while complicated types come afterwards.
 */
var groupTypes = {
    mathord: function(group, options, prev) {
        return buildCommon.mathit(
            group.value, group.mode, options.getColor(), ["mord"]);
    },

    textord: function(group, options, prev) {
        return buildCommon.mathrm(
            group.value, group.mode, options.getColor(), ["mord"]);
    },

    bin: function(group, options, prev) {
        var className = "mbin";
        // Pull out the most recent element. Do some special handling to find
        // things at the end of a \color group. Note that we don't use the same
        // logic for ordgroups (which count as ords).
        var prevAtom = prev;
        while (prevAtom && prevAtom.type == "color") {
            var atoms = prevAtom.value.value;
            prevAtom = atoms[atoms.length - 1];
        }
        // See TeXbook pg. 442-446, Rules 5 and 6, and the text before Rule 19.
        // Here, we determine whether the bin should turn into an ord. We
        // currently only apply Rule 5.
        if (!prev || utils.contains(["mbin", "mopen", "mrel", "mop", "mpunct"],
                getTypeOfGroup(prevAtom))) {
            group.type = "textord";
            className = "mord";
        }

        return buildCommon.mathrm(
            group.value, group.mode, options.getColor(), [className]);
    },

    rel: function(group, options, prev) {
        return buildCommon.mathrm(
            group.value, group.mode, options.getColor(), ["mrel"]);
    },

    open: function(group, options, prev) {
        return buildCommon.mathrm(
            group.value, group.mode, options.getColor(), ["mopen"]);
    },

    close: function(group, options, prev) {
        return buildCommon.mathrm(
            group.value, group.mode, options.getColor(), ["mclose"]);
    },

    inner: function(group, options, prev) {
        return buildCommon.mathrm(
            group.value, group.mode, options.getColor(), ["minner"]);
    },

    punct: function(group, options, prev) {
        return buildCommon.mathrm(
            group.value, group.mode, options.getColor(), ["mpunct"]);
    },

    ordgroup: function(group, options, prev) {
        return makeSpan(
            ["mord", options.style.cls()],
            buildExpression(group.value, options.reset())
        );
    },

    text: function(group, options, prev) {
        return makeSpan(["text", "mord", options.style.cls()],
            buildExpression(group.value.body, options.reset()));
    },

    color: function(group, options, prev) {
        var elements = buildExpression(
            group.value.value,
            options.withColor(group.value.color),
            prev
        );

        // \color isn't supposed to affect the type of the elements it contains.
        // To accomplish this, we wrap the results in a fragment, so the inner
        // elements will be able to directly interact with their neighbors. For
        // example, `\color{red}{2 +} 3` has the same spacing as `2 + 3`
        return new buildCommon.makeFragment(elements);
    },

    supsub: function(group, options, prev) {
        // Superscript and subscripts are handled in the TeXbook on page
        // 445-446, rules 18(a-f).

        // Here is where we defer to the inner group if it should handle
        // superscripts and subscripts itself.
        if (shouldHandleSupSub(group.value.base, options)) {
            return groupTypes[group.value.base.type](group, options, prev);
        }

        var base = buildGroup(group.value.base, options.reset());
        var supmid, submid, sup, sub;

        if (group.value.sup) {
            sup = buildGroup(group.value.sup,
                    options.withStyle(options.style.sup()));
            supmid = makeSpan(
                    [options.style.reset(), options.style.sup().cls()], [sup]);
        }

        if (group.value.sub) {
            sub = buildGroup(group.value.sub,
                    options.withStyle(options.style.sub()));
            submid = makeSpan(
                    [options.style.reset(), options.style.sub().cls()], [sub]);
        }

        // Rule 18a
        var supShift, subShift;
        if (isCharacterBox(group.value.base)) {
            supShift = 0;
            subShift = 0;
        } else {
            supShift = base.height - fontMetrics.metrics.supDrop;
            subShift = base.depth + fontMetrics.metrics.subDrop;
        }

        // Rule 18c
        var minSupShift;
        if (options.style === Style.DISPLAY) {
            minSupShift = fontMetrics.metrics.sup1;
        } else if (options.style.cramped) {
            minSupShift = fontMetrics.metrics.sup3;
        } else {
            minSupShift = fontMetrics.metrics.sup2;
        }

        // scriptspace is a font-size-independent size, so scale it
        // appropriately
        var multiplier = Style.TEXT.sizeMultiplier *
                options.style.sizeMultiplier;
        var scriptspace =
            (0.5 / fontMetrics.metrics.ptPerEm) / multiplier + "em";

        var supsub;
        if (!group.value.sup) {
            // Rule 18b
            subShift = Math.max(
                subShift, fontMetrics.metrics.sub1,
                sub.height - 0.8 * fontMetrics.metrics.xHeight);

            supsub = buildCommon.makeVList([
                {type: "elem", elem: submid}
            ], "shift", subShift, options);

            supsub.children[0].style.marginRight = scriptspace;

            // Subscripts shouldn't be shifted by the base's italic correction.
            // Account for that by shifting the subscript back the appropriate
            // amount. Note we only do this when the base is a single symbol.
            if (base instanceof domTree.symbolNode) {
                supsub.children[0].style.marginLeft = -base.italic + "em";
            }
        } else if (!group.value.sub) {
            // Rule 18c, d
            supShift = Math.max(supShift, minSupShift,
                sup.depth + 0.25 * fontMetrics.metrics.xHeight);

            supsub = buildCommon.makeVList([
                {type: "elem", elem: supmid}
            ], "shift", -supShift, options);

            supsub.children[0].style.marginRight = scriptspace;
        } else {
            supShift = Math.max(
                supShift, minSupShift,
                sup.depth + 0.25 * fontMetrics.metrics.xHeight);
            subShift = Math.max(subShift, fontMetrics.metrics.sub2);

            var ruleWidth = fontMetrics.metrics.defaultRuleThickness;

            // Rule 18e
            if ((supShift - sup.depth) - (sub.height - subShift) <
                    4 * ruleWidth) {
                subShift = 4 * ruleWidth - (supShift - sup.depth) + sub.height;
                var psi = 0.8 * fontMetrics.metrics.xHeight -
                    (supShift - sup.depth);
                if (psi > 0) {
                    supShift += psi;
                    subShift -= psi;
                }
            }

            supsub = buildCommon.makeVList([
                {type: "elem", elem: submid, shift: subShift},
                {type: "elem", elem: supmid, shift: -supShift}
            ], "individualShift", null, options);

            // See comment above about subscripts not being shifted
            if (base instanceof domTree.symbolNode) {
                supsub.children[0].style.marginLeft = -base.italic + "em";
            }

            supsub.children[0].style.marginRight = scriptspace;
            supsub.children[1].style.marginRight = scriptspace;
        }

        return makeSpan([getTypeOfGroup(group.value.base)],
            [base, supsub]);
    },

    genfrac: function(group, options, prev) {
        // Fractions are handled in the TeXbook on pages 444-445, rules 15(a-e).
        // Figure out what style this fraction should be in based on the
        // function used
        var fstyle = options.style;
        if (group.value.size === "display") {
            fstyle = Style.DISPLAY;
        } else if (group.value.size === "text") {
            fstyle = Style.TEXT;
        }

        var nstyle = fstyle.fracNum();
        var dstyle = fstyle.fracDen();

        var numer = buildGroup(group.value.numer, options.withStyle(nstyle));
        var numerreset = makeSpan([fstyle.reset(), nstyle.cls()], [numer]);

        var denom = buildGroup(group.value.denom, options.withStyle(dstyle));
        var denomreset = makeSpan([fstyle.reset(), dstyle.cls()], [denom]);

        var ruleWidth;
        if (group.value.hasBarLine) {
            ruleWidth = fontMetrics.metrics.defaultRuleThickness /
                options.style.sizeMultiplier;
        } else {
            ruleWidth = 0;
        }

        // Rule 15b
        var numShift;
        var clearance;
        var denomShift;
        if (fstyle.size === Style.DISPLAY.size) {
            numShift = fontMetrics.metrics.num1;
            if (ruleWidth > 0) {
                clearance = 3 * ruleWidth;
            } else {
                clearance = 7 * fontMetrics.metrics.defaultRuleThickness;
            }
            denomShift = fontMetrics.metrics.denom1;
        } else {
            if (ruleWidth > 0) {
                numShift = fontMetrics.metrics.num2;
                clearance = ruleWidth;
            } else {
                numShift = fontMetrics.metrics.num3;
                clearance = 3 * fontMetrics.metrics.defaultRuleThickness;
            }
            denomShift = fontMetrics.metrics.denom2;
        }

        var frac;
        if (ruleWidth === 0) {
            // Rule 15c
            var candiateClearance =
                (numShift - numer.depth) - (denom.height - denomShift);
            if (candiateClearance < clearance) {
                numShift += 0.5 * (clearance - candiateClearance);
                denomShift += 0.5 * (clearance - candiateClearance);
            }

            frac = buildCommon.makeVList([
                {type: "elem", elem: denomreset, shift: denomShift},
                {type: "elem", elem: numerreset, shift: -numShift}
            ], "individualShift", null, options);
        } else {
            // Rule 15d
            var axisHeight = fontMetrics.metrics.axisHeight;

            if ((numShift - numer.depth) - (axisHeight + 0.5 * ruleWidth)
                    < clearance) {
                numShift +=
                    clearance - ((numShift - numer.depth) -
                                 (axisHeight + 0.5 * ruleWidth));
            }

            if ((axisHeight - 0.5 * ruleWidth) - (denom.height - denomShift)
                    < clearance) {
                denomShift +=
                    clearance - ((axisHeight - 0.5 * ruleWidth) -
                                 (denom.height - denomShift));
            }

            var mid = makeSpan(
                [options.style.reset(), Style.TEXT.cls(), "frac-line"]);
            // Manually set the height of the line because its height is
            // created in CSS
            mid.height = ruleWidth;

            var midShift = -(axisHeight - 0.5 * ruleWidth);

            frac = buildCommon.makeVList([
                {type: "elem", elem: denomreset, shift: denomShift},
                {type: "elem", elem: mid,        shift: midShift},
                {type: "elem", elem: numerreset, shift: -numShift}
            ], "individualShift", null, options);
        }

        // Since we manually change the style sometimes (with \dfrac or \tfrac),
        // account for the possible size change here.
        frac.height *= fstyle.sizeMultiplier / options.style.sizeMultiplier;
        frac.depth *= fstyle.sizeMultiplier / options.style.sizeMultiplier;

        // Rule 15e
        var innerChildren = [makeSpan(["mfrac"], [frac])];

        var delimSize;
        if (fstyle.size === Style.DISPLAY.size) {
            delimSize = fontMetrics.metrics.delim1;
        } else {
            delimSize = fontMetrics.metrics.getDelim2(fstyle);
        }

        if (group.value.leftDelim != null) {
            innerChildren.unshift(
                delimiter.customSizedDelim(
                    group.value.leftDelim, delimSize, true,
                    options.withStyle(fstyle), group.mode)
            );
        }
        if (group.value.rightDelim != null) {
            innerChildren.push(
                delimiter.customSizedDelim(
                    group.value.rightDelim, delimSize, true,
                    options.withStyle(fstyle), group.mode)
            );
        }

        return makeSpan(
            ["minner", options.style.reset(), fstyle.cls()],
            innerChildren,
            options.getColor());
    },

    spacing: function(group, options, prev) {
        if (group.value === "\\ " || group.value === "\\space" ||
            group.value === " " || group.value === "~") {
            // Spaces are generated by adding an actual space. Each of these
            // things has an entry in the symbols table, so these will be turned
            // into appropriate outputs.
            return makeSpan(
                ["mord", "mspace"],
                [buildCommon.mathrm(group.value, group.mode)]
            );
        } else {
            // Other kinds of spaces are of arbitrary width. We use CSS to
            // generate these.
            var spacingClassMap = {
                "\\qquad": "qquad",
                "\\quad": "quad",
                "\\enspace": "enspace",
                "\\;": "thickspace",
                "\\:": "mediumspace",
                "\\,": "thinspace",
                "\\!": "negativethinspace"
            };

            return makeSpan(
                ["mord", "mspace", spacingClassMap[group.value]]);
        }
    },

    llap: function(group, options, prev) {
        var inner = makeSpan(
            ["inner"], [buildGroup(group.value.body, options.reset())]);
        var fix = makeSpan(["fix"], []);
        return makeSpan(
            ["llap", options.style.cls()], [inner, fix]);
    },

    rlap: function(group, options, prev) {
        var inner = makeSpan(
            ["inner"], [buildGroup(group.value.body, options.reset())]);
        var fix = makeSpan(["fix"], []);
        return makeSpan(
            ["rlap", options.style.cls()], [inner, fix]);
    },

    op: function(group, options, prev) {
        // Operators are handled in the TeXbook pg. 443-444, rule 13(a).
        var supGroup;
        var subGroup;
        var hasLimits = false;
        if (group.type === "supsub" ) {
            // If we have limits, supsub will pass us its group to handle. Pull
            // out the superscript and subscript and set the group to the op in
            // its base.
            supGroup = group.value.sup;
            subGroup = group.value.sub;
            group = group.value.base;
            hasLimits = true;
        }

        // Most operators have a large successor symbol, but these don't.
        var noSuccessor = [
            "\\smallint"
        ];

        var large = false;
        if (options.style.size === Style.DISPLAY.size &&
            group.value.symbol &&
            !utils.contains(noSuccessor, group.value.body)) {

            // Most symbol operators get larger in displaystyle (rule 13)
            large = true;
        }

        var base;
        var baseShift = 0;
        var slant = 0;
        if (group.value.symbol) {
            // If this is a symbol, create the symbol.
            var style = large ? "Size2-Regular" : "Size1-Regular";
            base = buildCommon.makeSymbol(
                group.value.body, style, "math", options.getColor(),
                ["op-symbol", large ? "large-op" : "small-op", "mop"]);

            // Shift the symbol so its center lies on the axis (rule 13). It
            // appears that our fonts have the centers of the symbols already
            // almost on the axis, so these numbers are very small. Note we
            // don't actually apply this here, but instead it is used either in
            // the vlist creation or separately when there are no limits.
            baseShift = (base.height - base.depth) / 2 -
                fontMetrics.metrics.axisHeight *
                options.style.sizeMultiplier;

            // The slant of the symbol is just its italic correction.
            slant = base.italic;
        } else {
            // Otherwise, this is a text operator. Build the text from the
            // operator's name.
            // TODO(emily): Add a space in the middle of some of these
            // operators, like \limsup
            var output = [];
            for (var i = 1; i < group.value.body.length; i++) {
                output.push(buildCommon.mathrm(group.value.body[i], group.mode));
            }
            base = makeSpan(["mop"], output, options.getColor());
        }

        if (hasLimits) {
            // IE 8 clips \int if it is in a display: inline-block. We wrap it
            // in a new span so it is an inline, and works.
            base = makeSpan([], [base]);

            var supmid, supKern, submid, subKern;
            // We manually have to handle the superscripts and subscripts. This,
            // aside from the kern calculations, is copied from supsub.
            if (supGroup) {
                var sup = buildGroup(
                    supGroup, options.withStyle(options.style.sup()));
                supmid = makeSpan(
                    [options.style.reset(), options.style.sup().cls()], [sup]);

                supKern = Math.max(
                    fontMetrics.metrics.bigOpSpacing1,
                    fontMetrics.metrics.bigOpSpacing3 - sup.depth);
            }

            if (subGroup) {
                var sub = buildGroup(
                    subGroup, options.withStyle(options.style.sub()));
                submid = makeSpan(
                    [options.style.reset(), options.style.sub().cls()],
                    [sub]);

                subKern = Math.max(
                    fontMetrics.metrics.bigOpSpacing2,
                    fontMetrics.metrics.bigOpSpacing4 - sub.height);
            }

            // Build the final group as a vlist of the possible subscript, base,
            // and possible superscript.
            var finalGroup, top, bottom;
            if (!supGroup) {
                top = base.height - baseShift;

                finalGroup = buildCommon.makeVList([
                    {type: "kern", size: fontMetrics.metrics.bigOpSpacing5},
                    {type: "elem", elem: submid},
                    {type: "kern", size: subKern},
                    {type: "elem", elem: base}
                ], "top", top, options);

                // Here, we shift the limits by the slant of the symbol. Note
                // that we are supposed to shift the limits by 1/2 of the slant,
                // but since we are centering the limits adding a full slant of
                // margin will shift by 1/2 that.
                finalGroup.children[0].style.marginLeft = -slant + "em";
            } else if (!subGroup) {
                bottom = base.depth + baseShift;

                finalGroup = buildCommon.makeVList([
                    {type: "elem", elem: base},
                    {type: "kern", size: supKern},
                    {type: "elem", elem: supmid},
                    {type: "kern", size: fontMetrics.metrics.bigOpSpacing5}
                ], "bottom", bottom, options);

                // See comment above about slants
                finalGroup.children[1].style.marginLeft = slant + "em";
            } else if (!supGroup && !subGroup) {
                // This case probably shouldn't occur (this would mean the
                // supsub was sending us a group with no superscript or
                // subscript) but be safe.
                return base;
            } else {
                bottom = fontMetrics.metrics.bigOpSpacing5 +
                    submid.height + submid.depth +
                    subKern +
                    base.depth + baseShift;

                finalGroup = buildCommon.makeVList([
                    {type: "kern", size: fontMetrics.metrics.bigOpSpacing5},
                    {type: "elem", elem: submid},
                    {type: "kern", size: subKern},
                    {type: "elem", elem: base},
                    {type: "kern", size: supKern},
                    {type: "elem", elem: supmid},
                    {type: "kern", size: fontMetrics.metrics.bigOpSpacing5}
                ], "bottom", bottom, options);

                // See comment above about slants
                finalGroup.children[0].style.marginLeft = -slant + "em";
                finalGroup.children[2].style.marginLeft = slant + "em";
            }

            return makeSpan(["mop", "op-limits"], [finalGroup]);
        } else {
            if (group.value.symbol) {
                base.style.top = baseShift + "em";
            }

            return base;
        }
    },

    katex: function(group, options, prev) {
        // The KaTeX logo. The offsets for the K and a were chosen to look
        // good, but the offsets for the T, E, and X were taken from the
        // definition of \TeX in TeX (see TeXbook pg. 356)
        var k = makeSpan(
            ["k"], [buildCommon.mathrm("K", group.mode)]);
        var a = makeSpan(
            ["a"], [buildCommon.mathrm("A", group.mode)]);

        a.height = (a.height + 0.2) * 0.75;
        a.depth = (a.height - 0.2) * 0.75;

        var t = makeSpan(
            ["t"], [buildCommon.mathrm("T", group.mode)]);
        var e = makeSpan(
            ["e"], [buildCommon.mathrm("E", group.mode)]);

        e.height = (e.height - 0.2155);
        e.depth = (e.depth + 0.2155);

        var x = makeSpan(
            ["x"], [buildCommon.mathrm("X", group.mode)]);

        return makeSpan(
            ["katex-logo"], [k, a, t, e, x], options.getColor());
    },

    overline: function(group, options, prev) {
        // Overlines are handled in the TeXbook pg 443, Rule 9.

        // Build the inner group in the cramped style.
        var innerGroup = buildGroup(group.value.body,
                options.withStyle(options.style.cramp()));

        var ruleWidth = fontMetrics.metrics.defaultRuleThickness /
            options.style.sizeMultiplier;

        // Create the line above the body
        var line = makeSpan(
            [options.style.reset(), Style.TEXT.cls(), "overline-line"]);
        line.height = ruleWidth;
        line.maxFontSize = 1.0;

        // Generate the vlist, with the appropriate kerns
        var vlist = buildCommon.makeVList([
            {type: "elem", elem: innerGroup},
            {type: "kern", size: 3 * ruleWidth},
            {type: "elem", elem: line},
            {type: "kern", size: ruleWidth}
        ], "firstBaseline", null, options);

        return makeSpan(["overline", "mord"], [vlist], options.getColor());
    },

    sqrt: function(group, options, prev) {
        // Square roots are handled in the TeXbook pg. 443, Rule 11.

        // First, we do the same steps as in overline to build the inner group
        // and line
        var inner = buildGroup(group.value.body,
                options.withStyle(options.style.cramp()));

        var ruleWidth = fontMetrics.metrics.defaultRuleThickness /
            options.style.sizeMultiplier;

        var line = makeSpan(
            [options.style.reset(), Style.TEXT.cls(), "sqrt-line"], [],
            options.getColor());
        line.height = ruleWidth;
        line.maxFontSize = 1.0;

        var phi = ruleWidth;
        if (options.style.id < Style.TEXT.id) {
            phi = fontMetrics.metrics.xHeight;
        }

        // Calculate the clearance between the body and line
        var lineClearance = ruleWidth + phi / 4;

        var innerHeight =
            (inner.height + inner.depth) * options.style.sizeMultiplier;
        var minDelimiterHeight = innerHeight + lineClearance + ruleWidth;

        // Create a \surd delimiter of the required minimum size
        var delim = makeSpan(["sqrt-sign"], [
            delimiter.customSizedDelim("\\surd", minDelimiterHeight,
                                       false, options, group.mode)],
                             options.getColor());

        var delimDepth = (delim.height + delim.depth) - ruleWidth;

        // Adjust the clearance based on the delimiter size
        if (delimDepth > inner.height + inner.depth + lineClearance) {
            lineClearance =
                (lineClearance + delimDepth - inner.height - inner.depth) / 2;
        }

        // Shift the delimiter so that its top lines up with the top of the line
        var delimShift = -(inner.height + lineClearance + ruleWidth) + delim.height;
        delim.style.top = delimShift + "em";
        delim.height -= delimShift;
        delim.depth += delimShift;

        // We add a special case here, because even when `inner` is empty, we
        // still get a line. So, we use a simple heuristic to decide if we
        // should omit the body entirely. (note this doesn't work for something
        // like `\sqrt{\rlap{x}}`, but if someone is doing that they deserve for
        // it not to work.
        var body;
        if (inner.height === 0 && inner.depth === 0) {
            body = makeSpan();
        } else {
            body = buildCommon.makeVList([
                {type: "elem", elem: inner},
                {type: "kern", size: lineClearance},
                {type: "elem", elem: line},
                {type: "kern", size: ruleWidth}
            ], "firstBaseline", null, options);
        }

        return makeSpan(["sqrt", "mord"], [delim, body]);
    },

    sizing: function(group, options, prev) {
        // Handle sizing operators like \Huge. Real TeX doesn't actually allow
        // these functions inside of math expressions, so we do some special
        // handling.
        var inner = buildExpression(group.value.value,
                options.withSize(group.value.size), prev);

        var span = makeSpan(["mord"],
            [makeSpan(["sizing", "reset-" + options.size, group.value.size,
                       options.style.cls()],
                      inner)]);

        // Calculate the correct maxFontSize manually
        var fontSize = sizingMultiplier[group.value.size];
        span.maxFontSize = fontSize * options.style.sizeMultiplier;

        return span;
    },

    styling: function(group, options, prev) {
        // Style changes are handled in the TeXbook on pg. 442, Rule 3.

        // Figure out what style we're changing to.
        var style = {
            "display": Style.DISPLAY,
            "text": Style.TEXT,
            "script": Style.SCRIPT,
            "scriptscript": Style.SCRIPTSCRIPT
        };

        var newStyle = style[group.value.style];

        // Build the inner expression in the new style.
        var inner = buildExpression(
            group.value.value, options.withStyle(newStyle), prev);

        return makeSpan([options.style.reset(), newStyle.cls()], inner);
    },

    delimsizing: function(group, options, prev) {
        var delim = group.value.value;

        if (delim === ".") {
            // Empty delimiters still count as elements, even though they don't
            // show anything.
            return makeSpan([groupToType[group.value.delimType]]);
        }

        // Use delimiter.sizedDelim to generate the delimiter.
        return makeSpan(
            [groupToType[group.value.delimType]],
            [delimiter.sizedDelim(
                delim, group.value.size, options, group.mode)]);
    },

    leftright: function(group, options, prev) {
        // Build the inner expression
        var inner = buildExpression(group.value.body, options.reset());

        var innerHeight = 0;
        var innerDepth = 0;

        // Calculate its height and depth
        for (var i = 0; i < inner.length; i++) {
            innerHeight = Math.max(inner[i].height, innerHeight);
            innerDepth = Math.max(inner[i].depth, innerDepth);
        }

        // The size of delimiters is the same, regardless of what style we are
        // in. Thus, to correctly calculate the size of delimiter we need around
        // a group, we scale down the inner size based on the size.
        innerHeight *= options.style.sizeMultiplier;
        innerDepth *= options.style.sizeMultiplier;

        var leftDelim;
        if (group.value.left === ".") {
            // Empty delimiters in \left and \right make null delimiter spaces.
            leftDelim = makeSpan(["nulldelimiter"]);
        } else {
            // Otherwise, use leftRightDelim to generate the correct sized
            // delimiter.
            leftDelim = delimiter.leftRightDelim(
                group.value.left, innerHeight, innerDepth, options,
                group.mode);
        }
        // Add it to the beginning of the expression
        inner.unshift(leftDelim);

        var rightDelim;
        // Same for the right delimiter
        if (group.value.right === ".") {
            rightDelim = makeSpan(["nulldelimiter"]);
        } else {
            rightDelim = delimiter.leftRightDelim(
                group.value.right, innerHeight, innerDepth, options,
                group.mode);
        }
        // Add it to the end of the expression.
        inner.push(rightDelim);

        return makeSpan(
            ["minner", options.style.cls()], inner, options.getColor());
    },

    rule: function(group, options, prev) {
        // Make an empty span for the rule
        var rule = makeSpan(["mord", "rule"], [], options.getColor());

        // Calculate the shift, width, and height of the rule, and account for units
        var shift = 0;
        if (group.value.shift) {
            shift = group.value.shift.number;
            if (group.value.shift.unit === "ex") {
                shift *= fontMetrics.metrics.xHeight;
            }
        }

        var width = group.value.width.number;
        if (group.value.width.unit === "ex") {
            width *= fontMetrics.metrics.xHeight;
        }

        var height = group.value.height.number;
        if (group.value.height.unit === "ex") {
            height *= fontMetrics.metrics.xHeight;
        }

        // The sizes of rules are absolute, so make it larger if we are in a
        // smaller style.
        shift /= options.style.sizeMultiplier;
        width /= options.style.sizeMultiplier;
        height /= options.style.sizeMultiplier;

        // Style the rule to the right size
        rule.style.borderRightWidth = width + "em";
        rule.style.borderTopWidth = height + "em";
        rule.style.bottom = shift + "em";

        // Record the height and width
        rule.width = width;
        rule.height = height + shift;
        rule.depth = -shift;

        return rule;
    },

    accent: function(group, options, prev) {
        // Accents are handled in the TeXbook pg. 443, rule 12.
        var base = group.value.base;

        var supsubGroup;
        if (group.type === "supsub") {
            // If our base is a character box, and we have superscripts and
            // subscripts, the supsub will defer to us. In particular, we want
            // to attach the superscripts and subscripts to the inner body (so
            // that the position of the superscripts and subscripts won't be
            // affected by the height of the accent). We accomplish this by
            // sticking the base of the accent into the base of the supsub, and
            // rendering that, while keeping track of where the accent is.

            // The supsub group is the group that was passed in
            var supsub = group;
            // The real accent group is the base of the supsub group
            group = supsub.value.base;
            // The character box is the base of the accent group
            base = group.value.base;
            // Stick the character box into the base of the supsub group
            supsub.value.base = base;

            // Rerender the supsub group with its new base, and store that
            // result.
            supsubGroup = buildGroup(
                supsub, options.reset(), prev);
        }

        // Build the base group
        var body = buildGroup(
            base, options.withStyle(options.style.cramp()));

        // Calculate the skew of the accent. This is based on the line "If the
        // nucleus is not a single character, let s = 0; otherwise set s to the
        // kern amount for the nucleus followed by the \skewchar of its font."
        // Note that our skew metrics are just the kern between each character
        // and the skewchar.
        var skew;
        if (isCharacterBox(base)) {
            // If the base is a character box, then we want the skew of the
            // innermost character. To do that, we find the innermost character:
            var baseChar = getBaseElem(base);
            // Then, we render its group to get the symbol inside it
            var baseGroup = buildGroup(
                baseChar, options.withStyle(options.style.cramp()));
            // Finally, we pull the skew off of the symbol.
            skew = baseGroup.skew;
            // Note that we now throw away baseGroup, because the layers we
            // removed with getBaseElem might contain things like \color which
            // we can't get rid of.
            // TODO(emily): Find a better way to get the skew
        } else {
            skew = 0;
        }

        // calculate the amount of space between the body and the accent
        var clearance = Math.min(body.height, fontMetrics.metrics.xHeight);

        // Build the accent
        var accent = buildCommon.makeSymbol(
            group.value.accent, "Main-Regular", "math", options.getColor());
        // Remove the italic correction of the accent, because it only serves to
        // shift the accent over to a place we don't want.
        accent.italic = 0;

        // The \vec character that the fonts use is a combining character, and
        // thus shows up much too far to the left. To account for this, we add a
        // specific class which shifts the accent over to where we want it.
        // TODO(emily): Fix this in a better way, like by changing the font
        var vecClass = group.value.accent === "\\vec" ? "accent-vec" : null;

        var accentBody = makeSpan(["accent-body", vecClass], [
            makeSpan([], [accent])]);

        accentBody = buildCommon.makeVList([
            {type: "elem", elem: body},
            {type: "kern", size: -clearance},
            {type: "elem", elem: accentBody}
        ], "firstBaseline", null, options);

        // Shift the accent over by the skew. Note we shift by twice the skew
        // because we are centering the accent, so by adding 2*skew to the left,
        // we shift it to the right by 1*skew.
        accentBody.children[1].style.marginLeft = 2 * skew + "em";

        var accentWrap = makeSpan(["mord", "accent"], [accentBody]);

        if (supsubGroup) {
            // Here, we replace the "base" child of the supsub with our newly
            // generated accent.
            supsubGroup.children[0] = accentWrap;

            // Since we don't rerun the height calculation after replacing the
            // accent, we manually recalculate height.
            supsubGroup.height = Math.max(accentWrap.height, supsubGroup.height);

            // Accents should always be ords, even when their innards are not.
            supsubGroup.classes[0] = "mord";

            return supsubGroup;
        } else {
            return accentWrap;
        }
    }
};

var sizingMultiplier = {
    size1: 0.5,
    size2: 0.7,
    size3: 0.8,
    size4: 0.9,
    size5: 1.0,
    size6: 1.2,
    size7: 1.44,
    size8: 1.73,
    size9: 2.07,
    size10: 2.49
};

/**
 * buildGroup is the function that takes a group and calls the correct groupType
 * function for it. It also handles the interaction of size and style changes
 * between parents and children.
 */
var buildGroup = function(group, options, prev) {
    if (!group) {
        return makeSpan();
    }

    if (groupTypes[group.type]) {
        // Call the groupTypes function
        var groupNode = groupTypes[group.type](group, options, prev);
        var multiplier;

        // If the style changed between the parent and the current group,
        // account for the size difference
        if (options.style !== options.parentStyle) {
            multiplier = options.style.sizeMultiplier /
                    options.parentStyle.sizeMultiplier;

            groupNode.height *= multiplier;
            groupNode.depth *= multiplier;
        }

        // If the size changed between the parent and the current group, account
        // for that size difference.
        if (options.size !== options.parentSize) {
            multiplier = sizingMultiplier[options.size] /
                    sizingMultiplier[options.parentSize];

            groupNode.height *= multiplier;
            groupNode.depth *= multiplier;
        }

        return groupNode;
    } else {
        throw new ParseError(
            "Got group of unknown type: '" + group.type + "'");
    }
};

/**
 * Take an entire parse tree, and build it into an appropriate set of nodes.
 */
var buildTree = function(tree) {
    // Setup the default options
    var options = new Options(Style.TEXT, "size5", "");

    // Build the expression contained in the tree
    var expression = buildExpression(tree, options);
    var body = makeSpan(["base", options.style.cls()], expression);

    // Add struts, which ensure that the top of the HTML element falls at the
    // height of the expression, and the bottom of the HTML element falls at the
    // depth of the expression.
    var topStrut = makeSpan(["strut"]);
    var bottomStrut = makeSpan(["strut", "bottom"]);

    topStrut.style.height = body.height + "em";
    bottomStrut.style.height = (body.height + body.depth) + "em";
    // We'd like to use `vertical-align: top` but in IE 9 this lowers the
    // baseline of the box to the bottom of this strut (instead staying in the
    // normal place) so we use an absolute value for vertical-align instead
    bottomStrut.style.verticalAlign = -body.depth + "em";

    // Wrap the struts and body together
    var katexNode = makeSpan(["katex"], [
        makeSpan(["katex-inner"], [topStrut, bottomStrut, body])
    ]);

    return katexNode;
};

module.exports = buildTree;

},{"./Options":3,"./ParseError":4,"./Style":6,"./buildCommon":7,"./delimiter":9,"./domTree":10,"./fontMetrics":11,"./utils":15}],9:[function(require,module,exports){
/**
 * This file deals with creating delimiters of various sizes. The TeXbook
 * discusses these routines on page 441-442, in the "Another subroutine sets box
 * x to a specified variable delimiter" paragraph.
 *
 * There are three main routines here. `makeSmallDelim` makes a delimiter in the
 * normal font, but in either text, script, or scriptscript style.
 * `makeLargeDelim` makes a delimiter in textstyle, but in one of the Size1,
 * Size2, Size3, or Size4 fonts. `makeStackedDelim` makes a delimiter out of
 * smaller pieces that are stacked on top of one another.
 *
 * The functions take a parameter `center`, which determines if the delimiter
 * should be centered around the axis.
 *
 * Then, there are three exposed functions. `sizedDelim` makes a delimiter in
 * one of the given sizes. This is used for things like `\bigl`.
 * `customSizedDelim` makes a delimiter with a given total height+depth. It is
 * called in places like `\sqrt`. `leftRightDelim` makes an appropriate
 * delimiter which surrounds an expression of a given height an depth. It is
 * used in `\left` and `\right`.
 */

var ParseError = require("./ParseError");
var Style = require("./Style");

var buildCommon = require("./buildCommon");
var fontMetrics = require("./fontMetrics");
var symbols = require("./symbols");
var utils = require("./utils");

var makeSpan = buildCommon.makeSpan;

/**
 * Get the metrics for a given symbol and font, after transformation (i.e.
 * after following replacement from symbols.js)
 */
var getMetrics = function(symbol, font) {
    if (symbols.math[symbol] && symbols.math[symbol].replace) {
        return fontMetrics.getCharacterMetrics(
            symbols.math[symbol].replace, font);
    } else {
        return fontMetrics.getCharacterMetrics(
            symbol, font);
    }
};

/**
 * Builds a symbol in the given font size (note size is an integer)
 */
var mathrmSize = function(value, size, mode) {
    return buildCommon.makeSymbol(value, "Size" + size + "-Regular", mode);
};

/**
 * Puts a delimiter span in a given style, and adds appropriate height, depth,
 * and maxFontSizes.
 */
var styleWrap = function(delim, toStyle, options) {
    var span = makeSpan(
        ["style-wrap", options.style.reset(), toStyle.cls()], [delim]);

    var multiplier = toStyle.sizeMultiplier / options.style.sizeMultiplier;

    span.height *= multiplier;
    span.depth *= multiplier;
    span.maxFontSize = toStyle.sizeMultiplier;

    return span;
};

/**
 * Makes a small delimiter. This is a delimiter that comes in the Main-Regular
 * font, but is restyled to either be in textstyle, scriptstyle, or
 * scriptscriptstyle.
 */
var makeSmallDelim = function(delim, style, center, options, mode) {
    var text = buildCommon.makeSymbol(delim, "Main-Regular", mode);

    var span = styleWrap(text, style, options);

    if (center) {
        var shift =
            (1 - options.style.sizeMultiplier / style.sizeMultiplier) *
            fontMetrics.metrics.axisHeight;

        span.style.top = shift + "em";
        span.height -= shift;
        span.depth += shift;
    }

    return span;
};

/**
 * Makes a large delimiter. This is a delimiter that comes in the Size1, Size2,
 * Size3, or Size4 fonts. It is always rendered in textstyle.
 */
var makeLargeDelim = function(delim, size, center, options, mode) {
    var inner = mathrmSize(delim, size, mode);

    var span = styleWrap(
        makeSpan(["delimsizing", "size" + size],
                 [inner], options.getColor()),
        Style.TEXT, options);

    if (center) {
        var shift = (1 - options.style.sizeMultiplier) *
            fontMetrics.metrics.axisHeight;

        span.style.top = shift + "em";
        span.height -= shift;
        span.depth += shift;
    }

    return span;
};

/**
 * Make an inner span with the given offset and in the given font. This is used
 * in `makeStackedDelim` to make the stacking pieces for the delimiter.
 */
var makeInner = function(symbol, font, mode) {
    var sizeClass;
    // Apply the correct CSS class to choose the right font.
    if (font === "Size1-Regular") {
        sizeClass = "delim-size1";
    } else if (font === "Size4-Regular") {
        sizeClass = "delim-size4";
    }

    var inner = makeSpan(
        ["delimsizinginner", sizeClass],
        [makeSpan([], [buildCommon.makeSymbol(symbol, font, mode)])]);

    // Since this will be passed into `makeVList` in the end, wrap the element
    // in the appropriate tag that VList uses.
    return {type: "elem", elem: inner};
};

/**
 * Make a stacked delimiter out of a given delimiter, with the total height at
 * least `heightTotal`. This routine is mentioned on page 442 of the TeXbook.
 */
var makeStackedDelim = function(delim, heightTotal, center, options, mode) {
    // There are four parts, the top, an optional middle, a repeated part, and a
    // bottom.
    var top, middle, repeat, bottom;
    top = repeat = bottom = delim;
    middle = null;
    // Also keep track of what font the delimiters are in
    var font = "Size1-Regular";

    // We set the parts and font based on the symbol. Note that we use
    // '\u23d0' instead of '|' and '\u2016' instead of '\\|' for the
    // repeats of the arrows
    if (delim === "\\uparrow") {
        repeat = bottom = "\u23d0";
    } else if (delim === "\\Uparrow") {
        repeat = bottom = "\u2016";
    } else if (delim === "\\downarrow") {
        top = repeat = "\u23d0";
    } else if (delim === "\\Downarrow") {
        top = repeat = "\u2016";
    } else if (delim === "\\updownarrow") {
        top = "\\uparrow";
        repeat = "\u23d0";
        bottom = "\\downarrow";
    } else if (delim === "\\Updownarrow") {
        top = "\\Uparrow";
        repeat = "\u2016";
        bottom = "\\Downarrow";
    } else if (delim === "[" || delim === "\\lbrack") {
        top = "\u23a1";
        repeat = "\u23a2";
        bottom = "\u23a3";
        font = "Size4-Regular";
    } else if (delim === "]" || delim === "\\rbrack") {
        top = "\u23a4";
        repeat = "\u23a5";
        bottom = "\u23a6";
        font = "Size4-Regular";
    } else if (delim === "\\lfloor") {
        repeat = top = "\u23a2";
        bottom = "\u23a3";
        font = "Size4-Regular";
    } else if (delim === "\\lceil") {
        top = "\u23a1";
        repeat = bottom = "\u23a2";
        font = "Size4-Regular";
    } else if (delim === "\\rfloor") {
        repeat = top = "\u23a5";
        bottom = "\u23a6";
        font = "Size4-Regular";
    } else if (delim === "\\rceil") {
        top = "\u23a4";
        repeat = bottom = "\u23a5";
        font = "Size4-Regular";
    } else if (delim === "(") {
        top = "\u239b";
        repeat = "\u239c";
        bottom = "\u239d";
        font = "Size4-Regular";
    } else if (delim === ")") {
        top = "\u239e";
        repeat = "\u239f";
        bottom = "\u23a0";
        font = "Size4-Regular";
    } else if (delim === "\\{" || delim === "\\lbrace") {
        top = "\u23a7";
        middle = "\u23a8";
        bottom = "\u23a9";
        repeat = "\u23aa";
        font = "Size4-Regular";
    } else if (delim === "\\}" || delim === "\\rbrace") {
        top = "\u23ab";
        middle = "\u23ac";
        bottom = "\u23ad";
        repeat = "\u23aa";
        font = "Size4-Regular";
    } else if (delim === "\\surd") {
        top = "\ue001";
        bottom = "\u23b7";
        repeat = "\ue000";
        font = "Size4-Regular";
    }

    // Get the metrics of the four sections
    var topMetrics = getMetrics(top, font);
    var topHeightTotal = topMetrics.height + topMetrics.depth;
    var repeatMetrics = getMetrics(repeat, font);
    var repeatHeightTotal = repeatMetrics.height + repeatMetrics.depth;
    var bottomMetrics = getMetrics(bottom, font);
    var bottomHeightTotal = bottomMetrics.height + bottomMetrics.depth;
    var middleMetrics, middleHeightTotal;
    if (middle !== null) {
        middleMetrics = getMetrics(middle, font);
        middleHeightTotal = middleMetrics.height + middleMetrics.depth;
    }

    // Calcuate the real height that the delimiter will have. It is at least the
    // size of the top, bottom, and optional middle combined.
    var realHeightTotal = topHeightTotal + bottomHeightTotal;
    if (middle !== null) {
        realHeightTotal += middleHeightTotal;
    }

    // Then add repeated pieces until we reach the specified height.
    while (realHeightTotal < heightTotal) {
        realHeightTotal += repeatHeightTotal;
        if (middle !== null) {
            // If there is a middle section, we need an equal number of pieces
            // on the top and bottom.
            realHeightTotal += repeatHeightTotal;
        }
    }

    // The center of the delimiter is placed at the center of the axis. Note
    // that in this context, "center" means that the delimiter should be
    // centered around the axis in the current style, while normally it is
    // centered around the axis in textstyle.
    var axisHeight = fontMetrics.metrics.axisHeight;
    if (center) {
        axisHeight *= options.style.sizeMultiplier;
    }
    // Calculate the depth
    var depth = realHeightTotal / 2 - axisHeight;

    // Now, we start building the pieces that will go into the vlist

    // Keep a list of the inner pieces
    var inners = [];

    // Add the bottom symbol
    inners.push(makeInner(bottom, font, mode));

    var i;
    if (middle === null) {
        // Calculate the number of repeated symbols we need
        var repeatHeight = realHeightTotal - topHeightTotal - bottomHeightTotal;
        var symbolCount = Math.ceil(repeatHeight / repeatHeightTotal);

        // Add that many symbols
        for (i = 0; i < symbolCount; i++) {
            inners.push(makeInner(repeat, font, mode));
        }
    } else {
        // When there is a middle bit, we need the middle part and two repeated
        // sections

        // Calculate the number of symbols needed for the top and bottom
        // repeated parts
        var topRepeatHeight =
            realHeightTotal / 2 - topHeightTotal - middleHeightTotal / 2;
        var topSymbolCount = Math.ceil(topRepeatHeight / repeatHeightTotal);

        var bottomRepeatHeight =
            realHeightTotal / 2 - topHeightTotal - middleHeightTotal / 2;
        var bottomSymbolCount =
            Math.ceil(bottomRepeatHeight / repeatHeightTotal);

        // Add the top repeated part
        for (i = 0; i < topSymbolCount; i++) {
            inners.push(makeInner(repeat, font, mode));
        }

        // Add the middle piece
        inners.push(makeInner(middle, font, mode));

        // Add the bottom repeated part
        for (i = 0; i < bottomSymbolCount; i++) {
            inners.push(makeInner(repeat, font, mode));
        }
    }

    // Add the top symbol
    inners.push(makeInner(top, font, mode));

    // Finally, build the vlist
    var inner = buildCommon.makeVList(inners, "bottom", depth, options);

    return styleWrap(
        makeSpan(["delimsizing", "mult"], [inner], options.getColor()),
        Style.TEXT, options);
};

// There are three kinds of delimiters, delimiters that stack when they become
// too large
var stackLargeDelimiters = [
    "(", ")", "[", "\\lbrack", "]", "\\rbrack",
    "\\{", "\\lbrace", "\\}", "\\rbrace",
    "\\lfloor", "\\rfloor", "\\lceil", "\\rceil",
    "\\surd"
];

// delimiters that always stack
var stackAlwaysDelimiters = [
    "\\uparrow", "\\downarrow", "\\updownarrow",
    "\\Uparrow", "\\Downarrow", "\\Updownarrow",
    "|", "\\|", "\\vert", "\\Vert"
];

// and delimiters that never stack
var stackNeverDelimiters = [
    "<", ">", "\\langle", "\\rangle", "/", "\\backslash"
];

// Metrics of the different sizes. Found by looking at TeX's output of
// $\bigl| // \Bigl| \biggl| \Biggl| \showlists$
// Used to create stacked delimiters of appropriate sizes in makeSizedDelim.
var sizeToMaxHeight = [0, 1.2, 1.8, 2.4, 3.0];

/**
 * Used to create a delimiter of a specific size, where `size` is 1, 2, 3, or 4.
 */
var makeSizedDelim = function(delim, size, options, mode) {
    // < and > turn into \langle and \rangle in delimiters
    if (delim === "<") {
        delim = "\\langle";
    } else if (delim === ">") {
        delim = "\\rangle";
    }

    // Sized delimiters are never centered.
    if (utils.contains(stackLargeDelimiters, delim) ||
        utils.contains(stackNeverDelimiters, delim)) {
        return makeLargeDelim(delim, size, false, options, mode);
    } else if (utils.contains(stackAlwaysDelimiters, delim)) {
        return makeStackedDelim(
            delim, sizeToMaxHeight[size], false, options, mode);
    } else {
        throw new ParseError("Illegal delimiter: '" + delim + "'");
    }
};

/**
 * There are three different sequences of delimiter sizes that the delimiters
 * follow depending on the kind of delimiter. This is used when creating custom
 * sized delimiters to decide whether to create a small, large, or stacked
 * delimiter.
 *
 * In real TeX, these sequences aren't explicitly defined, but are instead
 * defined inside the font metrics. Since there are only three sequences that
 * are possible for the delimiters that TeX defines, it is easier to just encode
 * them explicitly here.
 */

// Delimiters that never stack try small delimiters and large delimiters only
var stackNeverDelimiterSequence = [
    {type: "small", style: Style.SCRIPTSCRIPT},
    {type: "small", style: Style.SCRIPT},
    {type: "small", style: Style.TEXT},
    {type: "large", size: 1},
    {type: "large", size: 2},
    {type: "large", size: 3},
    {type: "large", size: 4}
];

// Delimiters that always stack try the small delimiters first, then stack
var stackAlwaysDelimiterSequence = [
    {type: "small", style: Style.SCRIPTSCRIPT},
    {type: "small", style: Style.SCRIPT},
    {type: "small", style: Style.TEXT},
    {type: "stack"}
];

// Delimiters that stack when large try the small and then large delimiters, and
// stack afterwards
var stackLargeDelimiterSequence = [
    {type: "small", style: Style.SCRIPTSCRIPT},
    {type: "small", style: Style.SCRIPT},
    {type: "small", style: Style.TEXT},
    {type: "large", size: 1},
    {type: "large", size: 2},
    {type: "large", size: 3},
    {type: "large", size: 4},
    {type: "stack"}
];

/**
 * Get the font used in a delimiter based on what kind of delimiter it is.
 */
var delimTypeToFont = function(type) {
    if (type.type === "small") {
        return "Main-Regular";
    } else if (type.type === "large") {
        return "Size" + type.size + "-Regular";
    } else if (type.type === "stack") {
        return "Size4-Regular";
    }
};

/**
 * Traverse a sequence of types of delimiters to decide what kind of delimiter
 * should be used to create a delimiter of the given height+depth.
 */
var traverseSequence = function(delim, height, sequence, options) {
    // Here, we choose the index we should start at in the sequences. In smaller
    // sizes (which correspond to larger numbers in style.size) we start earlier
    // in the sequence. Thus, scriptscript starts at index 3-3=0, script starts
    // at index 3-2=1, text starts at 3-1=2, and display starts at min(2,3-0)=2
    var start = Math.min(2, 3 - options.style.size);
    for (var i = start; i < sequence.length; i++) {
        if (sequence[i].type === "stack") {
            // This is always the last delimiter, so we just break the loop now.
            break;
        }

        var metrics = getMetrics(delim, delimTypeToFont(sequence[i]));
        var heightDepth = metrics.height + metrics.depth;

        // Small delimiters are scaled down versions of the same font, so we
        // account for the style change size.

        if (sequence[i].type === "small") {
            heightDepth *= sequence[i].style.sizeMultiplier;
        }

        // Check if the delimiter at this size works for the given height.
        if (heightDepth > height) {
            return sequence[i];
        }
    }

    // If we reached the end of the sequence, return the last sequence element.
    return sequence[sequence.length - 1];
};

/**
 * Make a delimiter of a given height+depth, with optional centering. Here, we
 * traverse the sequences, and create a delimiter that the sequence tells us to.
 */
var makeCustomSizedDelim = function(delim, height, center, options, mode) {
    if (delim === "<") {
        delim = "\\langle";
    } else if (delim === ">") {
        delim = "\\rangle";
    }

    // Decide what sequence to use
    var sequence;
    if (utils.contains(stackNeverDelimiters, delim)) {
        sequence = stackNeverDelimiterSequence;
    } else if (utils.contains(stackLargeDelimiters, delim)) {
        sequence = stackLargeDelimiterSequence;
    } else {
        sequence = stackAlwaysDelimiterSequence;
    }

    // Look through the sequence
    var delimType = traverseSequence(delim, height, sequence, options);

    // Depending on the sequence element we decided on, call the appropriate
    // function.
    if (delimType.type === "small") {
        return makeSmallDelim(delim, delimType.style, center, options, mode);
    } else if (delimType.type === "large") {
        return makeLargeDelim(delim, delimType.size, center, options, mode);
    } else if (delimType.type === "stack") {
        return makeStackedDelim(delim, height, center, options, mode);
    }
};

/**
 * Make a delimiter for use with `\left` and `\right`, given a height and depth
 * of an expression that the delimiters surround.
 */
var makeLeftRightDelim = function(delim, height, depth, options, mode) {
    // We always center \left/\right delimiters, so the axis is always shifted
    var axisHeight =
        fontMetrics.metrics.axisHeight * options.style.sizeMultiplier;

    // Taken from TeX source, tex.web, function make_left_right
    var delimiterFactor = 901;
    var delimiterExtend = 5.0 / fontMetrics.metrics.ptPerEm;

    var maxDistFromAxis = Math.max(
        height - axisHeight, depth + axisHeight);

    var totalHeight = Math.max(
        // In real TeX, calculations are done using integral values which are
        // 65536 per pt, or 655360 per em. So, the division here truncates in
        // TeX but doesn't here, producing different results. If we wanted to
        // exactly match TeX's calculation, we could do
        //   Math.floor(655360 * maxDistFromAxis / 500) *
        //    delimiterFactor / 655360
        // (To see the difference, compare
        //    x^{x^{\left(\rule{0.1em}{0.68em}\right)}}
        // in TeX and KaTeX)
        maxDistFromAxis / 500 * delimiterFactor,
        2 * maxDistFromAxis - delimiterExtend);

    // Finally, we defer to `makeCustomSizedDelim` with our calculated total
    // height
    return makeCustomSizedDelim(delim, totalHeight, true, options, mode);
};

module.exports = {
    sizedDelim: makeSizedDelim,
    customSizedDelim: makeCustomSizedDelim,
    leftRightDelim: makeLeftRightDelim
};

},{"./ParseError":4,"./Style":6,"./buildCommon":7,"./fontMetrics":11,"./symbols":14,"./utils":15}],10:[function(require,module,exports){
/**
 * These objects store the data about the DOM nodes we create, as well as some
 * extra data. They can then be transformed into real DOM nodes with the toNode
 * function or HTML markup using toMarkup. They are useful for both storing
 * extra properties on the nodes, as well as providing a way to easily work
 * with the DOM.
 */

var utils = require("./utils");

/**
 * Create an HTML className based on a list of classes. In addition to joining
 * with spaces, we also remove null or empty classes.
 */
var createClass = function(classes) {
    classes = classes.slice();
    for (var i = classes.length - 1; i >= 0; i--) {
        if (!classes[i]) {
            classes.splice(i, 1);
        }
    }

    return classes.join(" ");
};

/**
 * This node represents a span node, with a className, a list of children, and
 * an inline style. It also contains information about its height, depth, and
 * maxFontSize.
 */
function span(classes, children, height, depth, maxFontSize, style) {
    this.classes = classes || [];
    this.children = children || [];
    this.height = height || 0;
    this.depth = depth || 0;
    this.maxFontSize = maxFontSize || 0;
    this.style = style || {};
}

/**
 * Convert the span into an HTML node
 */
span.prototype.toNode = function() {
    var span = document.createElement("span");

    // Apply the class
    span.className = createClass(this.classes);

    // Apply inline styles
    for (var style in this.style) {
        if (this.style.hasOwnProperty(style)) {
            span.style[style] = this.style[style];
        }
    }

    // Append the children, also as HTML nodes
    for (var i = 0; i < this.children.length; i++) {
        span.appendChild(this.children[i].toNode());
    }

    return span;
};

/**
 * Convert the span into an HTML markup string
 */
span.prototype.toMarkup = function() {
    var markup = "<span";

    // Add the class
    if (this.classes.length) {
        markup += " class=\"";
        markup += utils.escape(createClass(this.classes));
        markup += "\"";
    }

    var styles = "";

    // Add the styles, after hyphenation
    for (var style in this.style) {
        if (this.style.hasOwnProperty(style)) {
            styles += utils.hyphenate(style) + ":" + this.style[style] + ";";
        }
    }

    if (styles) {
        markup += " style=\"" + utils.escape(styles) + "\"";
    }

    markup += ">";

    // Add the markup of the children, also as markup
    for (var i = 0; i < this.children.length; i++) {
        markup += this.children[i].toMarkup();
    }

    markup += "</span>";

    return markup;
};

/**
 * This node represents a document fragment, which contains elements, but when
 * placed into the DOM doesn't have any representation itself. Thus, it only
 * contains children and doesn't have any HTML properties. It also keeps track
 * of a height, depth, and maxFontSize.
 */
function documentFragment(children, height, depth, maxFontSize) {
    this.children = children || [];
    this.height = height || 0;
    this.depth = depth || 0;
    this.maxFontSize = maxFontSize || 0;
}

/**
 * Convert the fragment into a node
 */
documentFragment.prototype.toNode = function() {
    // Create a fragment
    var frag = document.createDocumentFragment();

    // Append the children
    for (var i = 0; i < this.children.length; i++) {
        frag.appendChild(this.children[i].toNode());
    }

    return frag;
};

/**
 * Convert the fragment into HTML markup
 */
documentFragment.prototype.toMarkup = function() {
    var markup = "";

    // Simply concatenate the markup for the children together
    for (var i = 0; i < this.children.length; i++) {
        markup += this.children[i].toMarkup();
    }

    return markup;
};

/**
 * A symbol node contains information about a single symbol. It either renders
 * to a single text node, or a span with a single text node in it, depending on
 * whether it has CSS classes, styles, or needs italic correction.
 */
function symbolNode(value, height, depth, italic, skew, classes, style) {
    this.value = value || "";
    this.height = height || 0;
    this.depth = depth || 0;
    this.italic = italic || 0;
    this.skew = skew || 0;
    this.classes = classes || [];
    this.style = style || {};
    this.maxFontSize = 0;
}

/**
 * Creates a text node or span from a symbol node. Note that a span is only
 * created if it is needed.
 */
symbolNode.prototype.toNode = function() {
    var node = document.createTextNode(this.value);
    var span = null;

    if (this.italic > 0) {
        span = document.createElement("span");
        span.style.marginRight = this.italic + "em";
    }

    if (this.classes.length > 0) {
        span = span || document.createElement("span");
        span.className = createClass(this.classes);
    }

    for (var style in this.style) {
        if (this.style.hasOwnProperty(style)) {
            span = span || document.createElement("span");
            span.style[style] = this.style[style];
        }
    }

    if (span) {
        span.appendChild(node);
        return span;
    } else {
        return node;
    }
};

/**
 * Creates markup for a symbol node.
 */
symbolNode.prototype.toMarkup = function() {
    // TODO(alpert): More duplication than I'd like from
    // span.prototype.toMarkup and symbolNode.prototype.toNode...
    var needsSpan = false;

    var markup = "<span";

    if (this.classes.length) {
        needsSpan = true;
        markup += " class=\"";
        markup += utils.escape(createClass(this.classes));
        markup += "\"";
    }

    var styles = "";

    if (this.italic > 0) {
        styles += "margin-right:" + this.italic + "em;";
    }
    for (var style in this.style) {
        if (this.style.hasOwnProperty(style)) {
            styles += utils.hyphenate(style) + ":" + this.style[style] + ";";
        }
    }

    if (styles) {
        needsSpan = true;
        markup += " style=\"" + utils.escape(styles) + "\"";
    }

    var escaped = utils.escape(this.value);
    if (needsSpan) {
        markup += ">";
        markup += escaped;
        markup += "</span>";
        return markup;
    } else {
        return escaped;
    }
};

module.exports = {
    span: span,
    documentFragment: documentFragment,
    symbolNode: symbolNode
};

},{"./utils":15}],11:[function(require,module,exports){
/* jshint unused:false */

var Style = require("./Style");

/**
 * This file contains metrics regarding fonts and individual symbols. The sigma
 * and xi variables, as well as the metricMap map contain data extracted from
 * TeX, TeX font metrics, and the TTF files. These data are then exposed via the
 * `metrics` variable and the getCharacterMetrics function.
 */

// These font metrics are extracted from TeX by using
// \font\a=cmmi10
// \showthe\fontdimenX\a
// where X is the corresponding variable number. These correspond to the font
// parameters of the symbol fonts. In TeX, there are actually three sets of
// dimensions, one for each of textstyle, scriptstyle, and scriptscriptstyle,
// but we only use the textstyle ones, and scale certain dimensions accordingly.
// See the TeXbook, page 441.
var sigma1 = 0.025;
var sigma2 = 0;
var sigma3 = 0;
var sigma4 = 0;
var sigma5 = 0.431;
var sigma6 = 1;
var sigma7 = 0;
var sigma8 = 0.677;
var sigma9 = 0.394;
var sigma10 = 0.444;
var sigma11 = 0.686;
var sigma12 = 0.345;
var sigma13 = 0.413;
var sigma14 = 0.363;
var sigma15 = 0.289;
var sigma16 = 0.150;
var sigma17 = 0.247;
var sigma18 = 0.386;
var sigma19 = 0.050;
var sigma20 = 2.390;
var sigma21 = 1.01;
var sigma21Script = 0.81;
var sigma21ScriptScript = 0.71;
var sigma22 = 0.250;

// These font metrics are extracted from TeX by using
// \font\a=cmex10
// \showthe\fontdimenX\a
// where X is the corresponding variable number. These correspond to the font
// parameters of the extension fonts (family 3). See the TeXbook, page 441.
var xi1 = 0;
var xi2 = 0;
var xi3 = 0;
var xi4 = 0;
var xi5 = 0.431;
var xi6 = 1;
var xi7 = 0;
var xi8 = 0.04;
var xi9 = 0.111;
var xi10 = 0.166;
var xi11 = 0.2;
var xi12 = 0.6;
var xi13 = 0.1;

// This value determines how large a pt is, for metrics which are defined in
// terms of pts.
// This value is also used in katex.less; if you change it make sure the values
// match.
var ptPerEm = 10.0;

/**
 * This is just a mapping from common names to real metrics
 */
var metrics = {
    xHeight: sigma5,
    quad: sigma6,
    num1: sigma8,
    num2: sigma9,
    num3: sigma10,
    denom1: sigma11,
    denom2: sigma12,
    sup1: sigma13,
    sup2: sigma14,
    sup3: sigma15,
    sub1: sigma16,
    sub2: sigma17,
    supDrop: sigma18,
    subDrop: sigma19,
    axisHeight: sigma22,
    defaultRuleThickness: xi8,
    bigOpSpacing1: xi9,
    bigOpSpacing2: xi10,
    bigOpSpacing3: xi11,
    bigOpSpacing4: xi12,
    bigOpSpacing5: xi13,
    ptPerEm: ptPerEm,

    // TODO(alpert): Missing parallel structure here. We should probably add
    // style-specific metrics for all of these.
    delim1: sigma20,
    getDelim2: function(style) {
        if (style.size === Style.TEXT.size) {
            return sigma21;
        } else if (style.size === Style.SCRIPT.size) {
            return sigma21Script;
        } else if (style.size === Style.SCRIPTSCRIPT.size) {
            return sigma21ScriptScript;
        }
        throw new Error("Unexpected style size: " + style.size);
    }
};

// This map contains a mapping from font name and character code to character
// metrics, including height, depth, italic correction, and skew (kern from the
// character to the corresponding \skewchar)
// This map is generated via `make metrics`. It should not be changed manually.
var metricMap = {"AMS-Regular":{"10003":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"10016":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"1008":{"depth":0.0,"height":0.43056,"italic":0.04028,"skew":0.0},"107":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"10731":{"depth":0.11111,"height":0.69224,"italic":0.0,"skew":0.0},"10846":{"depth":0.19444,"height":0.75583,"italic":0.0,"skew":0.0},"10877":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"10878":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"10885":{"depth":0.25583,"height":0.75583,"italic":0.0,"skew":0.0},"10886":{"depth":0.25583,"height":0.75583,"italic":0.0,"skew":0.0},"10887":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"10888":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"10889":{"depth":0.26167,"height":0.75726,"italic":0.0,"skew":0.0},"10890":{"depth":0.26167,"height":0.75726,"italic":0.0,"skew":0.0},"10891":{"depth":0.48256,"height":0.98256,"italic":0.0,"skew":0.0},"10892":{"depth":0.48256,"height":0.98256,"italic":0.0,"skew":0.0},"10901":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"10902":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"10933":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"10934":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"10935":{"depth":0.26167,"height":0.75726,"italic":0.0,"skew":0.0},"10936":{"depth":0.26167,"height":0.75726,"italic":0.0,"skew":0.0},"10937":{"depth":0.26167,"height":0.75726,"italic":0.0,"skew":0.0},"10938":{"depth":0.26167,"height":0.75726,"italic":0.0,"skew":0.0},"10949":{"depth":0.25583,"height":0.75583,"italic":0.0,"skew":0.0},"10950":{"depth":0.25583,"height":0.75583,"italic":0.0,"skew":0.0},"10955":{"depth":0.28481,"height":0.79383,"italic":0.0,"skew":0.0},"10956":{"depth":0.28481,"height":0.79383,"italic":0.0,"skew":0.0},"165":{"depth":0.0,"height":0.675,"italic":0.025,"skew":0.0},"174":{"depth":0.15559,"height":0.69224,"italic":0.0,"skew":0.0},"240":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"295":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"57350":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"57351":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"57352":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"57353":{"depth":0.0,"height":0.43056,"italic":0.04028,"skew":0.0},"57356":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"57357":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"57358":{"depth":0.41951,"height":0.91951,"italic":0.0,"skew":0.0},"57359":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"57360":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"57361":{"depth":0.41951,"height":0.91951,"italic":0.0,"skew":0.0},"57366":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"57367":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"57368":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"57369":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"57370":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"57371":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"65":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"66":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"67":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"68":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"69":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"70":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"71":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"710":{"depth":0.0,"height":0.825,"italic":0.0,"skew":0.0},"72":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"73":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"732":{"depth":0.0,"height":0.9,"italic":0.0,"skew":0.0},"74":{"depth":0.16667,"height":0.68889,"italic":0.0,"skew":0.0},"75":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"76":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"77":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"770":{"depth":0.0,"height":0.825,"italic":0.0,"skew":0.0},"771":{"depth":0.0,"height":0.9,"italic":0.0,"skew":0.0},"78":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"79":{"depth":0.16667,"height":0.68889,"italic":0.0,"skew":0.0},"80":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"81":{"depth":0.16667,"height":0.68889,"italic":0.0,"skew":0.0},"82":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8245":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"83":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"84":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8463":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8487":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8498":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"85":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8502":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8503":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8504":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8513":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8592":{"depth":-0.03598,"height":0.46402,"italic":0.0,"skew":0.0},"8594":{"depth":-0.03598,"height":0.46402,"italic":0.0,"skew":0.0},"86":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8602":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8603":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8606":{"depth":0.01354,"height":0.52239,"italic":0.0,"skew":0.0},"8608":{"depth":0.01354,"height":0.52239,"italic":0.0,"skew":0.0},"8610":{"depth":0.01354,"height":0.52239,"italic":0.0,"skew":0.0},"8611":{"depth":0.01354,"height":0.52239,"italic":0.0,"skew":0.0},"8619":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"8620":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"8621":{"depth":-0.13313,"height":0.37788,"italic":0.0,"skew":0.0},"8622":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8624":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8625":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8630":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"8631":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"8634":{"depth":0.08198,"height":0.58198,"italic":0.0,"skew":0.0},"8635":{"depth":0.08198,"height":0.58198,"italic":0.0,"skew":0.0},"8638":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"8639":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"8642":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"8643":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"8644":{"depth":0.1808,"height":0.675,"italic":0.0,"skew":0.0},"8646":{"depth":0.1808,"height":0.675,"italic":0.0,"skew":0.0},"8647":{"depth":0.1808,"height":0.675,"italic":0.0,"skew":0.0},"8648":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"8649":{"depth":0.1808,"height":0.675,"italic":0.0,"skew":0.0},"8650":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"8651":{"depth":0.01354,"height":0.52239,"italic":0.0,"skew":0.0},"8652":{"depth":0.01354,"height":0.52239,"italic":0.0,"skew":0.0},"8653":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8654":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8655":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8666":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"8667":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"8669":{"depth":-0.13313,"height":0.37788,"italic":0.0,"skew":0.0},"87":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8705":{"depth":0.0,"height":0.825,"italic":0.0,"skew":0.0},"8708":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8709":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"8717":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"8722":{"depth":-0.03598,"height":0.46402,"italic":0.0,"skew":0.0},"8724":{"depth":0.08198,"height":0.69224,"italic":0.0,"skew":0.0},"8726":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"8733":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8736":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8737":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8738":{"depth":0.03517,"height":0.52239,"italic":0.0,"skew":0.0},"8739":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"8740":{"depth":0.25142,"height":0.74111,"italic":0.0,"skew":0.0},"8741":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"8742":{"depth":0.25142,"height":0.74111,"italic":0.0,"skew":0.0},"8756":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8757":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8764":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8765":{"depth":-0.13313,"height":0.37788,"italic":0.0,"skew":0.0},"8769":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8770":{"depth":-0.03625,"height":0.46375,"italic":0.0,"skew":0.0},"8774":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8776":{"depth":-0.01688,"height":0.48312,"italic":0.0,"skew":0.0},"8778":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"8782":{"depth":0.06062,"height":0.54986,"italic":0.0,"skew":0.0},"8783":{"depth":0.06062,"height":0.54986,"italic":0.0,"skew":0.0},"8785":{"depth":0.08198,"height":0.58198,"italic":0.0,"skew":0.0},"8786":{"depth":0.08198,"height":0.58198,"italic":0.0,"skew":0.0},"8787":{"depth":0.08198,"height":0.58198,"italic":0.0,"skew":0.0},"8790":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8791":{"depth":0.22958,"height":0.72958,"italic":0.0,"skew":0.0},"8796":{"depth":0.08198,"height":0.91667,"italic":0.0,"skew":0.0},"88":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8806":{"depth":0.25583,"height":0.75583,"italic":0.0,"skew":0.0},"8807":{"depth":0.25583,"height":0.75583,"italic":0.0,"skew":0.0},"8808":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"8809":{"depth":0.25142,"height":0.75726,"italic":0.0,"skew":0.0},"8812":{"depth":0.25583,"height":0.75583,"italic":0.0,"skew":0.0},"8814":{"depth":0.20576,"height":0.70576,"italic":0.0,"skew":0.0},"8815":{"depth":0.20576,"height":0.70576,"italic":0.0,"skew":0.0},"8816":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8817":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8818":{"depth":0.22958,"height":0.72958,"italic":0.0,"skew":0.0},"8819":{"depth":0.22958,"height":0.72958,"italic":0.0,"skew":0.0},"8822":{"depth":0.1808,"height":0.675,"italic":0.0,"skew":0.0},"8823":{"depth":0.1808,"height":0.675,"italic":0.0,"skew":0.0},"8828":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"8829":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"8830":{"depth":0.22958,"height":0.72958,"italic":0.0,"skew":0.0},"8831":{"depth":0.22958,"height":0.72958,"italic":0.0,"skew":0.0},"8832":{"depth":0.20576,"height":0.70576,"italic":0.0,"skew":0.0},"8833":{"depth":0.20576,"height":0.70576,"italic":0.0,"skew":0.0},"8840":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8841":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8842":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"8843":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"8847":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"8848":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"8858":{"depth":0.08198,"height":0.58198,"italic":0.0,"skew":0.0},"8859":{"depth":0.08198,"height":0.58198,"italic":0.0,"skew":0.0},"8861":{"depth":0.08198,"height":0.58198,"italic":0.0,"skew":0.0},"8862":{"depth":0.0,"height":0.675,"italic":0.0,"skew":0.0},"8863":{"depth":0.0,"height":0.675,"italic":0.0,"skew":0.0},"8864":{"depth":0.0,"height":0.675,"italic":0.0,"skew":0.0},"8865":{"depth":0.0,"height":0.675,"italic":0.0,"skew":0.0},"8872":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8873":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8874":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8876":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8877":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8878":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8879":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8882":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"8883":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"8884":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"8885":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"8888":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"8890":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.0},"8891":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"8892":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"89":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8901":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"8903":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"8905":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"8906":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0},"8907":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8908":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8909":{"depth":-0.03598,"height":0.46402,"italic":0.0,"skew":0.0},"8910":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"8911":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"8912":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"8913":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"8914":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"8915":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"8916":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8918":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8919":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8920":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"8921":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"8922":{"depth":0.38569,"height":0.88569,"italic":0.0,"skew":0.0},"8923":{"depth":0.38569,"height":0.88569,"italic":0.0,"skew":0.0},"8926":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"8927":{"depth":0.13667,"height":0.63667,"italic":0.0,"skew":0.0},"8928":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8929":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8934":{"depth":0.23222,"height":0.74111,"italic":0.0,"skew":0.0},"8935":{"depth":0.23222,"height":0.74111,"italic":0.0,"skew":0.0},"8936":{"depth":0.23222,"height":0.74111,"italic":0.0,"skew":0.0},"8937":{"depth":0.23222,"height":0.74111,"italic":0.0,"skew":0.0},"8938":{"depth":0.20576,"height":0.70576,"italic":0.0,"skew":0.0},"8939":{"depth":0.20576,"height":0.70576,"italic":0.0,"skew":0.0},"8940":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8941":{"depth":0.30274,"height":0.79383,"italic":0.0,"skew":0.0},"8994":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"8995":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"90":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"9416":{"depth":0.15559,"height":0.69224,"italic":0.0,"skew":0.0},"9484":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"9488":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"9492":{"depth":0.0,"height":0.37788,"italic":0.0,"skew":0.0},"9496":{"depth":0.0,"height":0.37788,"italic":0.0,"skew":0.0},"9585":{"depth":0.19444,"height":0.68889,"italic":0.0,"skew":0.0},"9586":{"depth":0.19444,"height":0.74111,"italic":0.0,"skew":0.0},"9632":{"depth":0.0,"height":0.675,"italic":0.0,"skew":0.0},"9633":{"depth":0.0,"height":0.675,"italic":0.0,"skew":0.0},"9650":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"9651":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"9654":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"9660":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"9661":{"depth":0.0,"height":0.54986,"italic":0.0,"skew":0.0},"9664":{"depth":0.03517,"height":0.54986,"italic":0.0,"skew":0.0},"9674":{"depth":0.11111,"height":0.69224,"italic":0.0,"skew":0.0},"9733":{"depth":0.19444,"height":0.69224,"italic":0.0,"skew":0.0},"989":{"depth":0.08167,"height":0.58167,"italic":0.0,"skew":0.0}},"Main-Bold":{"100":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"101":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"102":{"depth":0.0,"height":0.69444,"italic":0.10903,"skew":0.0},"10216":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"10217":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"103":{"depth":0.19444,"height":0.44444,"italic":0.01597,"skew":0.0},"104":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"105":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"106":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"107":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"108":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"10815":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"109":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"10927":{"depth":0.19667,"height":0.69667,"italic":0.0,"skew":0.0},"10928":{"depth":0.19667,"height":0.69667,"italic":0.0,"skew":0.0},"110":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"111":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"112":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"113":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"114":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"115":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"116":{"depth":0.0,"height":0.63492,"italic":0.0,"skew":0.0},"117":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"118":{"depth":0.0,"height":0.44444,"italic":0.01597,"skew":0.0},"119":{"depth":0.0,"height":0.44444,"italic":0.01597,"skew":0.0},"120":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"121":{"depth":0.19444,"height":0.44444,"italic":0.01597,"skew":0.0},"122":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"123":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"124":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"125":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"126":{"depth":0.35,"height":0.34444,"italic":0.0,"skew":0.0},"168":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"172":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"175":{"depth":0.0,"height":0.59611,"italic":0.0,"skew":0.0},"176":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"177":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"180":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"215":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"247":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"305":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"33":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"34":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"35":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"36":{"depth":0.05556,"height":0.75,"italic":0.0,"skew":0.0},"37":{"depth":0.05556,"height":0.75,"italic":0.0,"skew":0.0},"38":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"39":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"40":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"41":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"42":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"43":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"44":{"depth":0.19444,"height":0.15556,"italic":0.0,"skew":0.0},"45":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"46":{"depth":0.0,"height":0.15556,"italic":0.0,"skew":0.0},"47":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"48":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"49":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"50":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"51":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"52":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"53":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"54":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"55":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"56":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"567":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"57":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"58":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"59":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"60":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"61":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"62":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"63":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"64":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"65":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"66":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"67":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"68":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"69":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"70":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"71":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"710":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"711":{"depth":0.0,"height":0.63194,"italic":0.0,"skew":0.0},"713":{"depth":0.0,"height":0.59611,"italic":0.0,"skew":0.0},"714":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"715":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"72":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"728":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"729":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"73":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"730":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"732":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"74":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"75":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"76":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"768":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"769":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"77":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"770":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"771":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"772":{"depth":0.0,"height":0.59611,"italic":0.0,"skew":0.0},"774":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"775":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"776":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"778":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"779":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"78":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"780":{"depth":0.0,"height":0.63194,"italic":0.0,"skew":0.0},"79":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"80":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"81":{"depth":0.19444,"height":0.68611,"italic":0.0,"skew":0.0},"82":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"8211":{"depth":0.0,"height":0.44444,"italic":0.03194,"skew":0.0},"8212":{"depth":0.0,"height":0.44444,"italic":0.03194,"skew":0.0},"8216":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8217":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8220":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8221":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8224":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8225":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"824":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8242":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"83":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"84":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"8407":{"depth":0.0,"height":0.72444,"italic":0.15486,"skew":0.0},"8463":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8465":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8467":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8472":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"8476":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"85":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"8501":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8592":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8593":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8594":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8595":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8596":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8597":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8598":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8599":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"86":{"depth":0.0,"height":0.68611,"italic":0.01597,"skew":0.0},"8600":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8601":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8636":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8637":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8640":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8641":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8656":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8657":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8658":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8659":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8660":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8661":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"87":{"depth":0.0,"height":0.68611,"italic":0.01597,"skew":0.0},"8704":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8706":{"depth":0.0,"height":0.69444,"italic":0.06389,"skew":0.0},"8707":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8709":{"depth":0.05556,"height":0.75,"italic":0.0,"skew":0.0},"8711":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"8712":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"8715":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"8722":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"8723":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"8725":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8726":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8727":{"depth":-0.02778,"height":0.47222,"italic":0.0,"skew":0.0},"8728":{"depth":-0.02639,"height":0.47361,"italic":0.0,"skew":0.0},"8729":{"depth":-0.02639,"height":0.47361,"italic":0.0,"skew":0.0},"8730":{"depth":0.18,"height":0.82,"italic":0.0,"skew":0.0},"8733":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"8734":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"8736":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8739":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8741":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8743":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8744":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8745":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8746":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8747":{"depth":0.19444,"height":0.69444,"italic":0.12778,"skew":0.0},"8764":{"depth":-0.10889,"height":0.39111,"italic":0.0,"skew":0.0},"8768":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8771":{"depth":0.00222,"height":0.50222,"italic":0.0,"skew":0.0},"8776":{"depth":0.02444,"height":0.52444,"italic":0.0,"skew":0.0},"8781":{"depth":0.00222,"height":0.50222,"italic":0.0,"skew":0.0},"88":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"8801":{"depth":0.00222,"height":0.50222,"italic":0.0,"skew":0.0},"8804":{"depth":0.19667,"height":0.69667,"italic":0.0,"skew":0.0},"8805":{"depth":0.19667,"height":0.69667,"italic":0.0,"skew":0.0},"8810":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"8811":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"8826":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"8827":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"8834":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"8835":{"depth":0.08556,"height":0.58556,"italic":0.0,"skew":0.0},"8838":{"depth":0.19667,"height":0.69667,"italic":0.0,"skew":0.0},"8839":{"depth":0.19667,"height":0.69667,"italic":0.0,"skew":0.0},"8846":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8849":{"depth":0.19667,"height":0.69667,"italic":0.0,"skew":0.0},"8850":{"depth":0.19667,"height":0.69667,"italic":0.0,"skew":0.0},"8851":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8852":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8853":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"8854":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"8855":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"8856":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"8857":{"depth":0.13333,"height":0.63333,"italic":0.0,"skew":0.0},"8866":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8867":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8868":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8869":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"89":{"depth":0.0,"height":0.68611,"italic":0.02875,"skew":0.0},"8900":{"depth":-0.02639,"height":0.47361,"italic":0.0,"skew":0.0},"8901":{"depth":-0.02639,"height":0.47361,"italic":0.0,"skew":0.0},"8902":{"depth":-0.02778,"height":0.47222,"italic":0.0,"skew":0.0},"8968":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8969":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8970":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8971":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8994":{"depth":-0.13889,"height":0.36111,"italic":0.0,"skew":0.0},"8995":{"depth":-0.13889,"height":0.36111,"italic":0.0,"skew":0.0},"90":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"91":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"915":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"916":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"92":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"920":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"923":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"926":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"928":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"93":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"931":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"933":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"934":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"936":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"937":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"94":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"95":{"depth":0.31,"height":0.13444,"italic":0.03194,"skew":0.0},"96":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"9651":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"9657":{"depth":-0.02778,"height":0.47222,"italic":0.0,"skew":0.0},"9661":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"9667":{"depth":-0.02778,"height":0.47222,"italic":0.0,"skew":0.0},"97":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"9711":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"98":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"9824":{"depth":0.12963,"height":0.69444,"italic":0.0,"skew":0.0},"9825":{"depth":0.12963,"height":0.69444,"italic":0.0,"skew":0.0},"9826":{"depth":0.12963,"height":0.69444,"italic":0.0,"skew":0.0},"9827":{"depth":0.12963,"height":0.69444,"italic":0.0,"skew":0.0},"9837":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"9838":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"9839":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"99":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0}},"Main-Italic":{"100":{"depth":0.0,"height":0.69444,"italic":0.10333,"skew":0.0},"101":{"depth":0.0,"height":0.43056,"italic":0.07514,"skew":0.0},"102":{"depth":0.19444,"height":0.69444,"italic":0.21194,"skew":0.0},"103":{"depth":0.19444,"height":0.43056,"italic":0.08847,"skew":0.0},"104":{"depth":0.0,"height":0.69444,"italic":0.07671,"skew":0.0},"105":{"depth":0.0,"height":0.65536,"italic":0.1019,"skew":0.0},"106":{"depth":0.19444,"height":0.65536,"italic":0.14467,"skew":0.0},"107":{"depth":0.0,"height":0.69444,"italic":0.10764,"skew":0.0},"108":{"depth":0.0,"height":0.69444,"italic":0.10333,"skew":0.0},"109":{"depth":0.0,"height":0.43056,"italic":0.07671,"skew":0.0},"110":{"depth":0.0,"height":0.43056,"italic":0.07671,"skew":0.0},"111":{"depth":0.0,"height":0.43056,"italic":0.06312,"skew":0.0},"112":{"depth":0.19444,"height":0.43056,"italic":0.06312,"skew":0.0},"113":{"depth":0.19444,"height":0.43056,"italic":0.08847,"skew":0.0},"114":{"depth":0.0,"height":0.43056,"italic":0.10764,"skew":0.0},"115":{"depth":0.0,"height":0.43056,"italic":0.08208,"skew":0.0},"116":{"depth":0.0,"height":0.61508,"italic":0.09486,"skew":0.0},"117":{"depth":0.0,"height":0.43056,"italic":0.07671,"skew":0.0},"118":{"depth":0.0,"height":0.43056,"italic":0.10764,"skew":0.0},"119":{"depth":0.0,"height":0.43056,"italic":0.10764,"skew":0.0},"120":{"depth":0.0,"height":0.43056,"italic":0.12042,"skew":0.0},"121":{"depth":0.19444,"height":0.43056,"italic":0.08847,"skew":0.0},"122":{"depth":0.0,"height":0.43056,"italic":0.12292,"skew":0.0},"126":{"depth":0.35,"height":0.31786,"italic":0.11585,"skew":0.0},"163":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"305":{"depth":0.0,"height":0.43056,"italic":0.07671,"skew":0.0},"33":{"depth":0.0,"height":0.69444,"italic":0.12417,"skew":0.0},"34":{"depth":0.0,"height":0.69444,"italic":0.06961,"skew":0.0},"35":{"depth":0.19444,"height":0.69444,"italic":0.06616,"skew":0.0},"37":{"depth":0.05556,"height":0.75,"italic":0.13639,"skew":0.0},"38":{"depth":0.0,"height":0.69444,"italic":0.09694,"skew":0.0},"39":{"depth":0.0,"height":0.69444,"italic":0.12417,"skew":0.0},"40":{"depth":0.25,"height":0.75,"italic":0.16194,"skew":0.0},"41":{"depth":0.25,"height":0.75,"italic":0.03694,"skew":0.0},"42":{"depth":0.0,"height":0.75,"italic":0.14917,"skew":0.0},"43":{"depth":0.05667,"height":0.56167,"italic":0.03694,"skew":0.0},"44":{"depth":0.19444,"height":0.10556,"italic":0.0,"skew":0.0},"45":{"depth":0.0,"height":0.43056,"italic":0.02826,"skew":0.0},"46":{"depth":0.0,"height":0.10556,"italic":0.0,"skew":0.0},"47":{"depth":0.25,"height":0.75,"italic":0.16194,"skew":0.0},"48":{"depth":0.0,"height":0.64444,"italic":0.13556,"skew":0.0},"49":{"depth":0.0,"height":0.64444,"italic":0.13556,"skew":0.0},"50":{"depth":0.0,"height":0.64444,"italic":0.13556,"skew":0.0},"51":{"depth":0.0,"height":0.64444,"italic":0.13556,"skew":0.0},"52":{"depth":0.19444,"height":0.64444,"italic":0.13556,"skew":0.0},"53":{"depth":0.0,"height":0.64444,"italic":0.13556,"skew":0.0},"54":{"depth":0.0,"height":0.64444,"italic":0.13556,"skew":0.0},"55":{"depth":0.19444,"height":0.64444,"italic":0.13556,"skew":0.0},"56":{"depth":0.0,"height":0.64444,"italic":0.13556,"skew":0.0},"567":{"depth":0.19444,"height":0.43056,"italic":0.03736,"skew":0.0},"57":{"depth":0.0,"height":0.64444,"italic":0.13556,"skew":0.0},"58":{"depth":0.0,"height":0.43056,"italic":0.0582,"skew":0.0},"59":{"depth":0.19444,"height":0.43056,"italic":0.0582,"skew":0.0},"61":{"depth":-0.13313,"height":0.36687,"italic":0.06616,"skew":0.0},"63":{"depth":0.0,"height":0.69444,"italic":0.1225,"skew":0.0},"64":{"depth":0.0,"height":0.69444,"italic":0.09597,"skew":0.0},"65":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"66":{"depth":0.0,"height":0.68333,"italic":0.10257,"skew":0.0},"67":{"depth":0.0,"height":0.68333,"italic":0.14528,"skew":0.0},"68":{"depth":0.0,"height":0.68333,"italic":0.09403,"skew":0.0},"69":{"depth":0.0,"height":0.68333,"italic":0.12028,"skew":0.0},"70":{"depth":0.0,"height":0.68333,"italic":0.13305,"skew":0.0},"71":{"depth":0.0,"height":0.68333,"italic":0.08722,"skew":0.0},"72":{"depth":0.0,"height":0.68333,"italic":0.16389,"skew":0.0},"73":{"depth":0.0,"height":0.68333,"italic":0.15806,"skew":0.0},"74":{"depth":0.0,"height":0.68333,"italic":0.14028,"skew":0.0},"75":{"depth":0.0,"height":0.68333,"italic":0.14528,"skew":0.0},"76":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"768":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"769":{"depth":0.0,"height":0.69444,"italic":0.09694,"skew":0.0},"77":{"depth":0.0,"height":0.68333,"italic":0.16389,"skew":0.0},"770":{"depth":0.0,"height":0.69444,"italic":0.06646,"skew":0.0},"771":{"depth":0.0,"height":0.66786,"italic":0.11585,"skew":0.0},"772":{"depth":0.0,"height":0.56167,"italic":0.10333,"skew":0.0},"774":{"depth":0.0,"height":0.69444,"italic":0.10806,"skew":0.0},"775":{"depth":0.0,"height":0.66786,"italic":0.11752,"skew":0.0},"776":{"depth":0.0,"height":0.66786,"italic":0.10474,"skew":0.0},"778":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"779":{"depth":0.0,"height":0.69444,"italic":0.1225,"skew":0.0},"78":{"depth":0.0,"height":0.68333,"italic":0.16389,"skew":0.0},"780":{"depth":0.0,"height":0.62847,"italic":0.08295,"skew":0.0},"79":{"depth":0.0,"height":0.68333,"italic":0.09403,"skew":0.0},"80":{"depth":0.0,"height":0.68333,"italic":0.10257,"skew":0.0},"81":{"depth":0.19444,"height":0.68333,"italic":0.09403,"skew":0.0},"82":{"depth":0.0,"height":0.68333,"italic":0.03868,"skew":0.0},"8211":{"depth":0.0,"height":0.43056,"italic":0.09208,"skew":0.0},"8212":{"depth":0.0,"height":0.43056,"italic":0.09208,"skew":0.0},"8216":{"depth":0.0,"height":0.69444,"italic":0.12417,"skew":0.0},"8217":{"depth":0.0,"height":0.69444,"italic":0.12417,"skew":0.0},"8220":{"depth":0.0,"height":0.69444,"italic":0.1685,"skew":0.0},"8221":{"depth":0.0,"height":0.69444,"italic":0.06961,"skew":0.0},"83":{"depth":0.0,"height":0.68333,"italic":0.11972,"skew":0.0},"84":{"depth":0.0,"height":0.68333,"italic":0.13305,"skew":0.0},"8463":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"85":{"depth":0.0,"height":0.68333,"italic":0.16389,"skew":0.0},"86":{"depth":0.0,"height":0.68333,"italic":0.18361,"skew":0.0},"87":{"depth":0.0,"height":0.68333,"italic":0.18361,"skew":0.0},"88":{"depth":0.0,"height":0.68333,"italic":0.15806,"skew":0.0},"89":{"depth":0.0,"height":0.68333,"italic":0.19383,"skew":0.0},"90":{"depth":0.0,"height":0.68333,"italic":0.14528,"skew":0.0},"91":{"depth":0.25,"height":0.75,"italic":0.1875,"skew":0.0},"915":{"depth":0.0,"height":0.68333,"italic":0.13305,"skew":0.0},"916":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"920":{"depth":0.0,"height":0.68333,"italic":0.09403,"skew":0.0},"923":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"926":{"depth":0.0,"height":0.68333,"italic":0.15294,"skew":0.0},"928":{"depth":0.0,"height":0.68333,"italic":0.16389,"skew":0.0},"93":{"depth":0.25,"height":0.75,"italic":0.10528,"skew":0.0},"931":{"depth":0.0,"height":0.68333,"italic":0.12028,"skew":0.0},"933":{"depth":0.0,"height":0.68333,"italic":0.11111,"skew":0.0},"934":{"depth":0.0,"height":0.68333,"italic":0.05986,"skew":0.0},"936":{"depth":0.0,"height":0.68333,"italic":0.11111,"skew":0.0},"937":{"depth":0.0,"height":0.68333,"italic":0.10257,"skew":0.0},"94":{"depth":0.0,"height":0.69444,"italic":0.06646,"skew":0.0},"95":{"depth":0.31,"height":0.12056,"italic":0.09208,"skew":0.0},"97":{"depth":0.0,"height":0.43056,"italic":0.07671,"skew":0.0},"98":{"depth":0.0,"height":0.69444,"italic":0.06312,"skew":0.0},"99":{"depth":0.0,"height":0.43056,"italic":0.05653,"skew":0.0}},"Main-Regular":{"32":{"depth":-0.0,"height":0.0,"italic":0,"skew":0},"160":{"depth":-0.0,"height":0.0,"italic":0,"skew":0},"8230":{"depth":-0.0,"height":0.12,"italic":0,"skew":0},"8773":{"depth":-0.022,"height":0.589,"italic":0,"skew":0},"8800":{"depth":0.215,"height":0.716,"italic":0,"skew":0},"8942":{"depth":0.03,"height":0.9,"italic":0,"skew":0},"8943":{"depth":-0.19,"height":0.31,"italic":0,"skew":0},"8945":{"depth":-0.1,"height":0.82,"italic":0,"skew":0},"100":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"101":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"102":{"depth":0.0,"height":0.69444,"italic":0.07778,"skew":0.0},"10216":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"10217":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"103":{"depth":0.19444,"height":0.43056,"italic":0.01389,"skew":0.0},"104":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"105":{"depth":0.0,"height":0.66786,"italic":0.0,"skew":0.0},"106":{"depth":0.19444,"height":0.66786,"italic":0.0,"skew":0.0},"107":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"108":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"10815":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"109":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"10927":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"10928":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"110":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"111":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"112":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.0},"113":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.0},"114":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"115":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"116":{"depth":0.0,"height":0.61508,"italic":0.0,"skew":0.0},"117":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"118":{"depth":0.0,"height":0.43056,"italic":0.01389,"skew":0.0},"119":{"depth":0.0,"height":0.43056,"italic":0.01389,"skew":0.0},"120":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"121":{"depth":0.19444,"height":0.43056,"italic":0.01389,"skew":0.0},"122":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"123":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"124":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"125":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"126":{"depth":0.35,"height":0.31786,"italic":0.0,"skew":0.0},"168":{"depth":0.0,"height":0.66786,"italic":0.0,"skew":0.0},"172":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"175":{"depth":0.0,"height":0.56778,"italic":0.0,"skew":0.0},"176":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"177":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"180":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"215":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"247":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"305":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"33":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"34":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"35":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"36":{"depth":0.05556,"height":0.75,"italic":0.0,"skew":0.0},"37":{"depth":0.05556,"height":0.75,"italic":0.0,"skew":0.0},"38":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"39":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"40":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"41":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"42":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"43":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"44":{"depth":0.19444,"height":0.10556,"italic":0.0,"skew":0.0},"45":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"46":{"depth":0.0,"height":0.10556,"italic":0.0,"skew":0.0},"47":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"48":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"49":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"50":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"51":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"52":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"53":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"54":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"55":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"56":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"567":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.0},"57":{"depth":0.0,"height":0.64444,"italic":0.0,"skew":0.0},"58":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"59":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.0},"60":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"61":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"62":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"63":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"64":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"65":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"66":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"67":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"68":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"69":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"70":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"71":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"710":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"711":{"depth":0.0,"height":0.62847,"italic":0.0,"skew":0.0},"713":{"depth":0.0,"height":0.56778,"italic":0.0,"skew":0.0},"714":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"715":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"72":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"728":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"729":{"depth":0.0,"height":0.66786,"italic":0.0,"skew":0.0},"73":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"730":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"732":{"depth":0.0,"height":0.66786,"italic":0.0,"skew":0.0},"74":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"75":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"76":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"768":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"769":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"77":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"770":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"771":{"depth":0.0,"height":0.66786,"italic":0.0,"skew":0.0},"772":{"depth":0.0,"height":0.56778,"italic":0.0,"skew":0.0},"774":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"775":{"depth":0.0,"height":0.66786,"italic":0.0,"skew":0.0},"776":{"depth":0.0,"height":0.66786,"italic":0.0,"skew":0.0},"778":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"779":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"78":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"780":{"depth":0.0,"height":0.62847,"italic":0.0,"skew":0.0},"79":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"80":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"81":{"depth":0.19444,"height":0.68333,"italic":0.0,"skew":0.0},"82":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"8211":{"depth":0.0,"height":0.43056,"italic":0.02778,"skew":0.0},"8212":{"depth":0.0,"height":0.43056,"italic":0.02778,"skew":0.0},"8216":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8217":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8220":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8221":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8224":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8225":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"824":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8242":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"83":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"84":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"8407":{"depth":0.0,"height":0.71444,"italic":0.15382,"skew":0.0},"8463":{"depth":0.0,"height":0.68889,"italic":0.0,"skew":0.0},"8465":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8467":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.11111},"8472":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.11111},"8476":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"85":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"8501":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8592":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8593":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8594":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8595":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8596":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8597":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8598":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8599":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"86":{"depth":0.0,"height":0.68333,"italic":0.01389,"skew":0.0},"8600":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8601":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8636":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8637":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8640":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8641":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8656":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8657":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8658":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8659":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8660":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8661":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"87":{"depth":0.0,"height":0.68333,"italic":0.01389,"skew":0.0},"8704":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8706":{"depth":0.0,"height":0.69444,"italic":0.05556,"skew":0.08334},"8707":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8709":{"depth":0.05556,"height":0.75,"italic":0.0,"skew":0.0},"8711":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"8712":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8715":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8722":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"8723":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"8725":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8726":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8727":{"depth":-0.03472,"height":0.46528,"italic":0.0,"skew":0.0},"8728":{"depth":-0.05555,"height":0.44445,"italic":0.0,"skew":0.0},"8729":{"depth":-0.05555,"height":0.44445,"italic":0.0,"skew":0.0},"8730":{"depth":0.2,"height":0.8,"italic":0.0,"skew":0.0},"8733":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"8734":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"8736":{"depth":0.0,"height":0.69224,"italic":0.0,"skew":0.0},"8739":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8741":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8743":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8744":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8745":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8746":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8747":{"depth":0.19444,"height":0.69444,"italic":0.11111,"skew":0.0},"8764":{"depth":-0.13313,"height":0.36687,"italic":0.0,"skew":0.0},"8768":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"8771":{"depth":-0.03625,"height":0.46375,"italic":0.0,"skew":0.0},"8776":{"depth":-0.01688,"height":0.48312,"italic":0.0,"skew":0.0},"8781":{"depth":-0.03625,"height":0.46375,"italic":0.0,"skew":0.0},"88":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"8801":{"depth":-0.03625,"height":0.46375,"italic":0.0,"skew":0.0},"8804":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"8805":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"8810":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8811":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8826":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8827":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8834":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8835":{"depth":0.0391,"height":0.5391,"italic":0.0,"skew":0.0},"8838":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"8839":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"8846":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8849":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"8850":{"depth":0.13597,"height":0.63597,"italic":0.0,"skew":0.0},"8851":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8852":{"depth":0.0,"height":0.55556,"italic":0.0,"skew":0.0},"8853":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"8854":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"8855":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"8856":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"8857":{"depth":0.08333,"height":0.58333,"italic":0.0,"skew":0.0},"8866":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8867":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8868":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"8869":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"89":{"depth":0.0,"height":0.68333,"italic":0.025,"skew":0.0},"8900":{"depth":-0.05555,"height":0.44445,"italic":0.0,"skew":0.0},"8901":{"depth":-0.05555,"height":0.44445,"italic":0.0,"skew":0.0},"8902":{"depth":-0.03472,"height":0.46528,"italic":0.0,"skew":0.0},"8968":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8969":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8970":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8971":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"8994":{"depth":-0.14236,"height":0.35764,"italic":0.0,"skew":0.0},"8995":{"depth":-0.14236,"height":0.35764,"italic":0.0,"skew":0.0},"90":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"91":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"915":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"916":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"92":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"920":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"923":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"926":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"928":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"93":{"depth":0.25,"height":0.75,"italic":0.0,"skew":0.0},"931":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"933":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"934":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"936":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"937":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.0},"94":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"95":{"depth":0.31,"height":0.12056,"italic":0.02778,"skew":0.0},"96":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"9651":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"9657":{"depth":-0.03472,"height":0.46528,"italic":0.0,"skew":0.0},"9661":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"9667":{"depth":-0.03472,"height":0.46528,"italic":0.0,"skew":0.0},"97":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"9711":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"98":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"9824":{"depth":0.12963,"height":0.69444,"italic":0.0,"skew":0.0},"9825":{"depth":0.12963,"height":0.69444,"italic":0.0,"skew":0.0},"9826":{"depth":0.12963,"height":0.69444,"italic":0.0,"skew":0.0},"9827":{"depth":0.12963,"height":0.69444,"italic":0.0,"skew":0.0},"9837":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"9838":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"9839":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"99":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0}},"Math-BoldItalic":{"100":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"1009":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"101":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"1013":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"102":{"depth":0.19444,"height":0.69444,"italic":0.11042,"skew":0.0},"103":{"depth":0.19444,"height":0.44444,"italic":0.03704,"skew":0.0},"104":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"105":{"depth":0.0,"height":0.69326,"italic":0.0,"skew":0.0},"106":{"depth":0.19444,"height":0.69326,"italic":0.0622,"skew":0.0},"107":{"depth":0.0,"height":0.69444,"italic":0.01852,"skew":0.0},"108":{"depth":0.0,"height":0.69444,"italic":0.0088,"skew":0.0},"109":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"110":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"111":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"112":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"113":{"depth":0.19444,"height":0.44444,"italic":0.03704,"skew":0.0},"114":{"depth":0.0,"height":0.44444,"italic":0.03194,"skew":0.0},"115":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"116":{"depth":0.0,"height":0.63492,"italic":0.0,"skew":0.0},"117":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"118":{"depth":0.0,"height":0.44444,"italic":0.03704,"skew":0.0},"119":{"depth":0.0,"height":0.44444,"italic":0.02778,"skew":0.0},"120":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"121":{"depth":0.19444,"height":0.44444,"italic":0.03704,"skew":0.0},"122":{"depth":0.0,"height":0.44444,"italic":0.04213,"skew":0.0},"47":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"65":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"66":{"depth":0.0,"height":0.68611,"italic":0.04835,"skew":0.0},"67":{"depth":0.0,"height":0.68611,"italic":0.06979,"skew":0.0},"68":{"depth":0.0,"height":0.68611,"italic":0.03194,"skew":0.0},"69":{"depth":0.0,"height":0.68611,"italic":0.05451,"skew":0.0},"70":{"depth":0.0,"height":0.68611,"italic":0.15972,"skew":0.0},"71":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"72":{"depth":0.0,"height":0.68611,"italic":0.08229,"skew":0.0},"73":{"depth":0.0,"height":0.68611,"italic":0.07778,"skew":0.0},"74":{"depth":0.0,"height":0.68611,"italic":0.10069,"skew":0.0},"75":{"depth":0.0,"height":0.68611,"italic":0.06979,"skew":0.0},"76":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"77":{"depth":0.0,"height":0.68611,"italic":0.11424,"skew":0.0},"78":{"depth":0.0,"height":0.68611,"italic":0.11424,"skew":0.0},"79":{"depth":0.0,"height":0.68611,"italic":0.03194,"skew":0.0},"80":{"depth":0.0,"height":0.68611,"italic":0.15972,"skew":0.0},"81":{"depth":0.19444,"height":0.68611,"italic":0.0,"skew":0.0},"82":{"depth":0.0,"height":0.68611,"italic":0.00421,"skew":0.0},"83":{"depth":0.0,"height":0.68611,"italic":0.05382,"skew":0.0},"84":{"depth":0.0,"height":0.68611,"italic":0.15972,"skew":0.0},"85":{"depth":0.0,"height":0.68611,"italic":0.11424,"skew":0.0},"86":{"depth":0.0,"height":0.68611,"italic":0.25555,"skew":0.0},"87":{"depth":0.0,"height":0.68611,"italic":0.15972,"skew":0.0},"88":{"depth":0.0,"height":0.68611,"italic":0.07778,"skew":0.0},"89":{"depth":0.0,"height":0.68611,"italic":0.25555,"skew":0.0},"90":{"depth":0.0,"height":0.68611,"italic":0.06979,"skew":0.0},"915":{"depth":0.0,"height":0.68611,"italic":0.15972,"skew":0.0},"916":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"920":{"depth":0.0,"height":0.68611,"italic":0.03194,"skew":0.0},"923":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"926":{"depth":0.0,"height":0.68611,"italic":0.07458,"skew":0.0},"928":{"depth":0.0,"height":0.68611,"italic":0.08229,"skew":0.0},"931":{"depth":0.0,"height":0.68611,"italic":0.05451,"skew":0.0},"933":{"depth":0.0,"height":0.68611,"italic":0.15972,"skew":0.0},"934":{"depth":0.0,"height":0.68611,"italic":0.0,"skew":0.0},"936":{"depth":0.0,"height":0.68611,"italic":0.11653,"skew":0.0},"937":{"depth":0.0,"height":0.68611,"italic":0.04835,"skew":0.0},"945":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"946":{"depth":0.19444,"height":0.69444,"italic":0.03403,"skew":0.0},"947":{"depth":0.19444,"height":0.44444,"italic":0.06389,"skew":0.0},"948":{"depth":0.0,"height":0.69444,"italic":0.03819,"skew":0.0},"949":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"950":{"depth":0.19444,"height":0.69444,"italic":0.06215,"skew":0.0},"951":{"depth":0.19444,"height":0.44444,"italic":0.03704,"skew":0.0},"952":{"depth":0.0,"height":0.69444,"italic":0.03194,"skew":0.0},"953":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"954":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"955":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"956":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"957":{"depth":0.0,"height":0.44444,"italic":0.06898,"skew":0.0},"958":{"depth":0.19444,"height":0.69444,"italic":0.03021,"skew":0.0},"959":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"960":{"depth":0.0,"height":0.44444,"italic":0.03704,"skew":0.0},"961":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"962":{"depth":0.09722,"height":0.44444,"italic":0.07917,"skew":0.0},"963":{"depth":0.0,"height":0.44444,"italic":0.03704,"skew":0.0},"964":{"depth":0.0,"height":0.44444,"italic":0.13472,"skew":0.0},"965":{"depth":0.0,"height":0.44444,"italic":0.03704,"skew":0.0},"966":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"967":{"depth":0.19444,"height":0.44444,"italic":0.0,"skew":0.0},"968":{"depth":0.19444,"height":0.69444,"italic":0.03704,"skew":0.0},"969":{"depth":0.0,"height":0.44444,"italic":0.03704,"skew":0.0},"97":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0},"977":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"98":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"981":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"982":{"depth":0.0,"height":0.44444,"italic":0.03194,"skew":0.0},"99":{"depth":0.0,"height":0.44444,"italic":0.0,"skew":0.0}},"Math-Italic":{"100":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.16667},"1009":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.08334},"101":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"1013":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"102":{"depth":0.19444,"height":0.69444,"italic":0.10764,"skew":0.16667},"103":{"depth":0.19444,"height":0.43056,"italic":0.03588,"skew":0.02778},"104":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"105":{"depth":0.0,"height":0.65952,"italic":0.0,"skew":0.0},"106":{"depth":0.19444,"height":0.65952,"italic":0.05724,"skew":0.0},"107":{"depth":0.0,"height":0.69444,"italic":0.03148,"skew":0.0},"108":{"depth":0.0,"height":0.69444,"italic":0.01968,"skew":0.08334},"109":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"110":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"111":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"112":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.08334},"113":{"depth":0.19444,"height":0.43056,"italic":0.03588,"skew":0.08334},"114":{"depth":0.0,"height":0.43056,"italic":0.02778,"skew":0.05556},"115":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"116":{"depth":0.0,"height":0.61508,"italic":0.0,"skew":0.08334},"117":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.02778},"118":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.02778},"119":{"depth":0.0,"height":0.43056,"italic":0.02691,"skew":0.08334},"120":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.02778},"121":{"depth":0.19444,"height":0.43056,"italic":0.03588,"skew":0.05556},"122":{"depth":0.0,"height":0.43056,"italic":0.04398,"skew":0.05556},"47":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.0},"65":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.13889},"66":{"depth":0.0,"height":0.68333,"italic":0.05017,"skew":0.08334},"67":{"depth":0.0,"height":0.68333,"italic":0.07153,"skew":0.08334},"68":{"depth":0.0,"height":0.68333,"italic":0.02778,"skew":0.05556},"69":{"depth":0.0,"height":0.68333,"italic":0.05764,"skew":0.08334},"70":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.08334},"71":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.08334},"72":{"depth":0.0,"height":0.68333,"italic":0.08125,"skew":0.05556},"73":{"depth":0.0,"height":0.68333,"italic":0.07847,"skew":0.11111},"74":{"depth":0.0,"height":0.68333,"italic":0.09618,"skew":0.16667},"75":{"depth":0.0,"height":0.68333,"italic":0.07153,"skew":0.05556},"76":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.02778},"77":{"depth":0.0,"height":0.68333,"italic":0.10903,"skew":0.08334},"78":{"depth":0.0,"height":0.68333,"italic":0.10903,"skew":0.08334},"79":{"depth":0.0,"height":0.68333,"italic":0.02778,"skew":0.08334},"80":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.08334},"81":{"depth":0.19444,"height":0.68333,"italic":0.0,"skew":0.08334},"82":{"depth":0.0,"height":0.68333,"italic":0.00773,"skew":0.08334},"83":{"depth":0.0,"height":0.68333,"italic":0.05764,"skew":0.08334},"84":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.08334},"85":{"depth":0.0,"height":0.68333,"italic":0.10903,"skew":0.02778},"86":{"depth":0.0,"height":0.68333,"italic":0.22222,"skew":0.0},"87":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.0},"88":{"depth":0.0,"height":0.68333,"italic":0.07847,"skew":0.08334},"89":{"depth":0.0,"height":0.68333,"italic":0.22222,"skew":0.0},"90":{"depth":0.0,"height":0.68333,"italic":0.07153,"skew":0.08334},"915":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.08334},"916":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.16667},"920":{"depth":0.0,"height":0.68333,"italic":0.02778,"skew":0.08334},"923":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.16667},"926":{"depth":0.0,"height":0.68333,"italic":0.07569,"skew":0.08334},"928":{"depth":0.0,"height":0.68333,"italic":0.08125,"skew":0.05556},"931":{"depth":0.0,"height":0.68333,"italic":0.05764,"skew":0.08334},"933":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.05556},"934":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.08334},"936":{"depth":0.0,"height":0.68333,"italic":0.11,"skew":0.05556},"937":{"depth":0.0,"height":0.68333,"italic":0.05017,"skew":0.08334},"945":{"depth":0.0,"height":0.43056,"italic":0.0037,"skew":0.02778},"946":{"depth":0.19444,"height":0.69444,"italic":0.05278,"skew":0.08334},"947":{"depth":0.19444,"height":0.43056,"italic":0.05556,"skew":0.0},"948":{"depth":0.0,"height":0.69444,"italic":0.03785,"skew":0.05556},"949":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.08334},"950":{"depth":0.19444,"height":0.69444,"italic":0.07378,"skew":0.08334},"951":{"depth":0.19444,"height":0.43056,"italic":0.03588,"skew":0.05556},"952":{"depth":0.0,"height":0.69444,"italic":0.02778,"skew":0.08334},"953":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"954":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"955":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"956":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.02778},"957":{"depth":0.0,"height":0.43056,"italic":0.06366,"skew":0.02778},"958":{"depth":0.19444,"height":0.69444,"italic":0.04601,"skew":0.11111},"959":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"960":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.0},"961":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.08334},"962":{"depth":0.09722,"height":0.43056,"italic":0.07986,"skew":0.08334},"963":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.0},"964":{"depth":0.0,"height":0.43056,"italic":0.1132,"skew":0.02778},"965":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.02778},"966":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.08334},"967":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.05556},"968":{"depth":0.19444,"height":0.69444,"italic":0.03588,"skew":0.11111},"969":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.0},"97":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"977":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.08334},"98":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"981":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.08334},"982":{"depth":0.0,"height":0.43056,"italic":0.02778,"skew":0.0},"99":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556}},"Math-Regular":{"100":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.16667},"1009":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.08334},"101":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"1013":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"102":{"depth":0.19444,"height":0.69444,"italic":0.10764,"skew":0.16667},"103":{"depth":0.19444,"height":0.43056,"italic":0.03588,"skew":0.02778},"104":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"105":{"depth":0.0,"height":0.65952,"italic":0.0,"skew":0.0},"106":{"depth":0.19444,"height":0.65952,"italic":0.05724,"skew":0.0},"107":{"depth":0.0,"height":0.69444,"italic":0.03148,"skew":0.0},"108":{"depth":0.0,"height":0.69444,"italic":0.01968,"skew":0.08334},"109":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"110":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"111":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"112":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.08334},"113":{"depth":0.19444,"height":0.43056,"italic":0.03588,"skew":0.08334},"114":{"depth":0.0,"height":0.43056,"italic":0.02778,"skew":0.05556},"115":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"116":{"depth":0.0,"height":0.61508,"italic":0.0,"skew":0.08334},"117":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.02778},"118":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.02778},"119":{"depth":0.0,"height":0.43056,"italic":0.02691,"skew":0.08334},"120":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.02778},"121":{"depth":0.19444,"height":0.43056,"italic":0.03588,"skew":0.05556},"122":{"depth":0.0,"height":0.43056,"italic":0.04398,"skew":0.05556},"65":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.13889},"66":{"depth":0.0,"height":0.68333,"italic":0.05017,"skew":0.08334},"67":{"depth":0.0,"height":0.68333,"italic":0.07153,"skew":0.08334},"68":{"depth":0.0,"height":0.68333,"italic":0.02778,"skew":0.05556},"69":{"depth":0.0,"height":0.68333,"italic":0.05764,"skew":0.08334},"70":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.08334},"71":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.08334},"72":{"depth":0.0,"height":0.68333,"italic":0.08125,"skew":0.05556},"73":{"depth":0.0,"height":0.68333,"italic":0.07847,"skew":0.11111},"74":{"depth":0.0,"height":0.68333,"italic":0.09618,"skew":0.16667},"75":{"depth":0.0,"height":0.68333,"italic":0.07153,"skew":0.05556},"76":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.02778},"77":{"depth":0.0,"height":0.68333,"italic":0.10903,"skew":0.08334},"78":{"depth":0.0,"height":0.68333,"italic":0.10903,"skew":0.08334},"79":{"depth":0.0,"height":0.68333,"italic":0.02778,"skew":0.08334},"80":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.08334},"81":{"depth":0.19444,"height":0.68333,"italic":0.0,"skew":0.08334},"82":{"depth":0.0,"height":0.68333,"italic":0.00773,"skew":0.08334},"83":{"depth":0.0,"height":0.68333,"italic":0.05764,"skew":0.08334},"84":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.08334},"85":{"depth":0.0,"height":0.68333,"italic":0.10903,"skew":0.02778},"86":{"depth":0.0,"height":0.68333,"italic":0.22222,"skew":0.0},"87":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.0},"88":{"depth":0.0,"height":0.68333,"italic":0.07847,"skew":0.08334},"89":{"depth":0.0,"height":0.68333,"italic":0.22222,"skew":0.0},"90":{"depth":0.0,"height":0.68333,"italic":0.07153,"skew":0.08334},"915":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.08334},"916":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.16667},"920":{"depth":0.0,"height":0.68333,"italic":0.02778,"skew":0.08334},"923":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.16667},"926":{"depth":0.0,"height":0.68333,"italic":0.07569,"skew":0.08334},"928":{"depth":0.0,"height":0.68333,"italic":0.08125,"skew":0.05556},"931":{"depth":0.0,"height":0.68333,"italic":0.05764,"skew":0.08334},"933":{"depth":0.0,"height":0.68333,"italic":0.13889,"skew":0.05556},"934":{"depth":0.0,"height":0.68333,"italic":0.0,"skew":0.08334},"936":{"depth":0.0,"height":0.68333,"italic":0.11,"skew":0.05556},"937":{"depth":0.0,"height":0.68333,"italic":0.05017,"skew":0.08334},"945":{"depth":0.0,"height":0.43056,"italic":0.0037,"skew":0.02778},"946":{"depth":0.19444,"height":0.69444,"italic":0.05278,"skew":0.08334},"947":{"depth":0.19444,"height":0.43056,"italic":0.05556,"skew":0.0},"948":{"depth":0.0,"height":0.69444,"italic":0.03785,"skew":0.05556},"949":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.08334},"950":{"depth":0.19444,"height":0.69444,"italic":0.07378,"skew":0.08334},"951":{"depth":0.19444,"height":0.43056,"italic":0.03588,"skew":0.05556},"952":{"depth":0.0,"height":0.69444,"italic":0.02778,"skew":0.08334},"953":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"954":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"955":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"956":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.02778},"957":{"depth":0.0,"height":0.43056,"italic":0.06366,"skew":0.02778},"958":{"depth":0.19444,"height":0.69444,"italic":0.04601,"skew":0.11111},"959":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556},"960":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.0},"961":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.08334},"962":{"depth":0.09722,"height":0.43056,"italic":0.07986,"skew":0.08334},"963":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.0},"964":{"depth":0.0,"height":0.43056,"italic":0.1132,"skew":0.02778},"965":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.02778},"966":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.08334},"967":{"depth":0.19444,"height":0.43056,"italic":0.0,"skew":0.05556},"968":{"depth":0.19444,"height":0.69444,"italic":0.03588,"skew":0.11111},"969":{"depth":0.0,"height":0.43056,"italic":0.03588,"skew":0.0},"97":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.0},"977":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.08334},"98":{"depth":0.0,"height":0.69444,"italic":0.0,"skew":0.0},"981":{"depth":0.19444,"height":0.69444,"italic":0.0,"skew":0.08334},"982":{"depth":0.0,"height":0.43056,"italic":0.02778,"skew":0.0},"99":{"depth":0.0,"height":0.43056,"italic":0.0,"skew":0.05556}},"Size1-Regular":{"8748":{"depth":0.306,"height":0.805,"italic":0.19445,"skew":0.0},"8749":{"depth":0.306,"height":0.805,"italic":0.19445,"skew":0.0},"10216":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"10217":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"10752":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"10753":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"10754":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"10756":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"10758":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"123":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"125":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"40":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"41":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"47":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"710":{"depth":0.0,"height":0.72222,"italic":0.0,"skew":0.0},"732":{"depth":0.0,"height":0.72222,"italic":0.0,"skew":0.0},"770":{"depth":0.0,"height":0.72222,"italic":0.0,"skew":0.0},"771":{"depth":0.0,"height":0.72222,"italic":0.0,"skew":0.0},"8214":{"depth":-0.00099,"height":0.601,"italic":0.0,"skew":0.0},"8593":{"depth":1e-05,"height":0.6,"italic":0.0,"skew":0.0},"8595":{"depth":1e-05,"height":0.6,"italic":0.0,"skew":0.0},"8657":{"depth":1e-05,"height":0.6,"italic":0.0,"skew":0.0},"8659":{"depth":1e-05,"height":0.6,"italic":0.0,"skew":0.0},"8719":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"8720":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"8721":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"8730":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"8739":{"depth":-0.00599,"height":0.606,"italic":0.0,"skew":0.0},"8741":{"depth":-0.00599,"height":0.606,"italic":0.0,"skew":0.0},"8747":{"depth":0.30612,"height":0.805,"italic":0.19445,"skew":0.0},"8750":{"depth":0.30612,"height":0.805,"italic":0.19445,"skew":0.0},"8896":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"8897":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"8898":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"8899":{"depth":0.25001,"height":0.75,"italic":0.0,"skew":0.0},"8968":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"8969":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"8970":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"8971":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"91":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"9168":{"depth":-0.00099,"height":0.601,"italic":0.0,"skew":0.0},"92":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0},"93":{"depth":0.35001,"height":0.85,"italic":0.0,"skew":0.0}},"Size2-Regular":{"8748":{"depth":0.862,"height":1.36,"italic":0.44445,"skew":0.0},"8749":{"depth":0.862,"height":1.36,"italic":0.44445,"skew":0.0},"10216":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"10217":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"10752":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"10753":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"10754":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"10756":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"10758":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"123":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"125":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"40":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"41":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"47":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"710":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"732":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"770":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"771":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"8719":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"8720":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"8721":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"8730":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"8747":{"depth":0.86225,"height":1.36,"italic":0.44445,"skew":0.0},"8750":{"depth":0.86225,"height":1.36,"italic":0.44445,"skew":0.0},"8896":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"8897":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"8898":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"8899":{"depth":0.55001,"height":1.05,"italic":0.0,"skew":0.0},"8968":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"8969":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"8970":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"8971":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"91":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"92":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"93":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0}},"Size3-Regular":{"10216":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"10217":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"123":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"125":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"40":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"41":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"47":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"710":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"732":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"770":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"771":{"depth":0.0,"height":0.75,"italic":0.0,"skew":0.0},"8730":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"8968":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"8969":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"8970":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"8971":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"91":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"92":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0},"93":{"depth":0.95003,"height":1.45,"italic":0.0,"skew":0.0}},"Size4-Regular":{"10216":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"10217":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"123":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"125":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"40":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"41":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"47":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"57344":{"depth":-0.00499,"height":0.605,"italic":0.0,"skew":0.0},"57345":{"depth":-0.00499,"height":0.605,"italic":0.0,"skew":0.0},"57680":{"depth":0.0,"height":0.12,"italic":0.0,"skew":0.0},"57681":{"depth":0.0,"height":0.12,"italic":0.0,"skew":0.0},"57682":{"depth":0.0,"height":0.12,"italic":0.0,"skew":0.0},"57683":{"depth":0.0,"height":0.12,"italic":0.0,"skew":0.0},"710":{"depth":0.0,"height":0.825,"italic":0.0,"skew":0.0},"732":{"depth":0.0,"height":0.825,"italic":0.0,"skew":0.0},"770":{"depth":0.0,"height":0.825,"italic":0.0,"skew":0.0},"771":{"depth":0.0,"height":0.825,"italic":0.0,"skew":0.0},"8730":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"8968":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"8969":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"8970":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"8971":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"91":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"9115":{"depth":0.64502,"height":1.155,"italic":0.0,"skew":0.0},"9116":{"depth":1e-05,"height":0.6,"italic":0.0,"skew":0.0},"9117":{"depth":0.64502,"height":1.155,"italic":0.0,"skew":0.0},"9118":{"depth":0.64502,"height":1.155,"italic":0.0,"skew":0.0},"9119":{"depth":1e-05,"height":0.6,"italic":0.0,"skew":0.0},"9120":{"depth":0.64502,"height":1.155,"italic":0.0,"skew":0.0},"9121":{"depth":0.64502,"height":1.155,"italic":0.0,"skew":0.0},"9122":{"depth":-0.00099,"height":0.601,"italic":0.0,"skew":0.0},"9123":{"depth":0.64502,"height":1.155,"italic":0.0,"skew":0.0},"9124":{"depth":0.64502,"height":1.155,"italic":0.0,"skew":0.0},"9125":{"depth":-0.00099,"height":0.601,"italic":0.0,"skew":0.0},"9126":{"depth":0.64502,"height":1.155,"italic":0.0,"skew":0.0},"9127":{"depth":1e-05,"height":0.9,"italic":0.0,"skew":0.0},"9128":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"9129":{"depth":0.90001,"height":0.0,"italic":0.0,"skew":0.0},"9130":{"depth":0.0,"height":0.3,"italic":0.0,"skew":0.0},"9131":{"depth":1e-05,"height":0.9,"italic":0.0,"skew":0.0},"9132":{"depth":0.65002,"height":1.15,"italic":0.0,"skew":0.0},"9133":{"depth":0.90001,"height":0.0,"italic":0.0,"skew":0.0},"9143":{"depth":0.88502,"height":0.915,"italic":0.0,"skew":0.0},"92":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0},"93":{"depth":1.25003,"height":1.75,"italic":0.0,"skew":0.0}}};

/**
 * This function is a convience function for looking up information in the
 * metricMap table. It takes a character as a string, and a style
 */
var getCharacterMetrics = function(character, style) {
    return metricMap[style][character.charCodeAt(0)];
};

module.exports = {
    metrics: metrics,
    getCharacterMetrics: getCharacterMetrics
};

},{"./Style":6}],12:[function(require,module,exports){
var utils = require("./utils");
var ParseError = require("./ParseError");

// This file contains a list of functions that we parse. The functions map
// contains the following data:

/*
 * Keys are the name of the functions to parse
 * The data contains the following keys:
 *  - numArgs: The number of arguments the function takes.
 *  - argTypes: (optional) An array corresponding to each argument of the
 *              function, giving the type of argument that should be parsed. Its
 *              length should be equal to `numArgs + numOptionalArgs`. Valid
 *              types:
 *               - "size": A size-like thing, such as "1em" or "5ex"
 *               - "color": An html color, like "#abc" or "blue"
 *               - "original": The same type as the environment that the
 *                             function being parsed is in (e.g. used for the
 *                             bodies of functions like \color where the first
 *                             argument is special and the second argument is
 *                             parsed normally)
 *              Other possible types (probably shouldn't be used)
 *               - "text": Text-like (e.g. \text)
 *               - "math": Normal math
 *              If undefined, this will be treated as an appropriate length
 *              array of "original" strings
 *  - greediness: (optional) The greediness of the function to use ungrouped
 *                arguments.
 *
 *                E.g. if you have an expression
 *                  \sqrt \frac 1 2
 *                since \frac has greediness=2 vs \sqrt's greediness=1, \frac
 *                will use the two arguments '1' and '2' as its two arguments,
 *                then that whole function will be used as the argument to
 *                \sqrt. On the other hand, the expressions
 *                  \frac \frac 1 2 3
 *                and
 *                  \frac \sqrt 1 2
 *                will fail because \frac and \frac have equal greediness
 *                and \sqrt has a lower greediness than \frac respectively. To
 *                make these parse, we would have to change them to:
 *                  \frac {\frac 1 2} 3
 *                and
 *                  \frac {\sqrt 1} 2
 *
 *                The default value is `1`
 *  - allowedInText: (optional) Whether or not the function is allowed inside
 *                   text mode (default false)
 *  - numOptionalArgs: (optional) The number of optional arguments the function
 *                     should parse. If the optional arguments aren't found,
 *                     `null` will be passed to the handler in their place.
 *                     (default 0)
 *  - handler: The function that is called to handle this function and its
 *             arguments. The arguments are:
 *              - func: the text of the function
 *              - [args]: the next arguments are the arguments to the function,
 *                        of which there are numArgs of them
 *              - positions: the positions in the overall string of the function
 *                           and the arguments. Should only be used to produce
 *                           error messages
 *             The function should return an object with the following keys:
 *              - type: The type of element that this is. This is then used in
 *                      buildTree to determine which function should be called
 *                      to build this node into a DOM node
 *             Any other data can be added to the object, which will be passed
 *             in to the function in buildTree as `group.value`.
 */

var functions = {
    // A normal square root
    "\\sqrt": {
        numArgs: 1,
        numOptionalArgs: 1,
        handler: function(func, optional, body, positions) {
            if (optional != null) {
                throw new ParseError(
                    "Optional arguments to \\sqrt aren't supported yet",
                    this.lexer, positions[1] - 1);
            }

            return {
                type: "sqrt",
                body: body
            };
        }
    },

    // Some non-mathy text
    "\\text": {
        numArgs: 1,
        argTypes: ["text"],
        greediness: 2,
        handler: function(func, body) {
            // Since the corresponding buildTree function expects a list of
            // elements, we normalize for different kinds of arguments
            // TODO(emily): maybe this should be done somewhere else
            var inner;
            if (body.type === "ordgroup") {
                inner = body.value;
            } else {
                inner = [body];
            }

            return {
                type: "text",
                body: inner
            };
        }
    },

    // A two-argument custom color
    "\\color": {
        numArgs: 2,
        allowedInText: true,
        argTypes: ["color", "original"],
        handler: function(func, color, body) {
            // Normalize the different kinds of bodies (see \text above)
            var inner;
            if (body.type === "ordgroup") {
                inner = body.value;
            } else {
                inner = [body];
            }

            return {
                type: "color",
                color: color.value,
                value: inner
            };
        }
    },

    // An overline
    "\\overline": {
        numArgs: 1,
        handler: function(func, body) {
            return {
                type: "overline",
                body: body
            };
        }
    },

    // A box of the width and height
    "\\rule": {
        numArgs: 2,
        numOptionalArgs: 1,
        argTypes: ["size", "size", "size"],
        handler: function(func, shift, width, height) {
            return {
                type: "rule",
                shift: shift && shift.value,
                width: width.value,
                height: height.value
            };
        }
    },

    // A KaTeX logo
    "\\KaTeX": {
        numArgs: 0,
        handler: function(func) {
            return {
                type: "katex"
            };
        }
    }
};

// Extra data needed for the delimiter handler down below
var delimiterSizes = {
    "\\bigl" : {type: "open",    size: 1},
    "\\Bigl" : {type: "open",    size: 2},
    "\\biggl": {type: "open",    size: 3},
    "\\Biggl": {type: "open",    size: 4},
    "\\bigr" : {type: "close",   size: 1},
    "\\Bigr" : {type: "close",   size: 2},
    "\\biggr": {type: "close",   size: 3},
    "\\Biggr": {type: "close",   size: 4},
    "\\bigm" : {type: "rel",     size: 1},
    "\\Bigm" : {type: "rel",     size: 2},
    "\\biggm": {type: "rel",     size: 3},
    "\\Biggm": {type: "rel",     size: 4},
    "\\big"  : {type: "textord", size: 1},
    "\\Big"  : {type: "textord", size: 2},
    "\\bigg" : {type: "textord", size: 3},
    "\\Bigg" : {type: "textord", size: 4}
};

var delimiters = [
    "(", ")", "[", "\\lbrack", "]", "\\rbrack",
    "\\{", "\\lbrace", "\\}", "\\rbrace",
    "\\lfloor", "\\rfloor", "\\lceil", "\\rceil",
    "<", ">", "\\langle", "\\rangle",
    "/", "\\backslash",
    "|", "\\vert", "\\|", "\\Vert",
    "\\uparrow", "\\Uparrow",
    "\\downarrow", "\\Downarrow",
    "\\updownarrow", "\\Updownarrow",
    "."
];

/*
 * This is a list of functions which each have the same function but have
 * different names so that we don't have to duplicate the data a bunch of times.
 * Each element in the list is an object with the following keys:
 *  - funcs: A list of function names to be associated with the data
 *  - data: An objecty with the same data as in each value of the `function`
 *          table above
 */
var duplicatedFunctions = [
    // Single-argument color functions
    {
        funcs: [
            "\\blue", "\\orange", "\\pink", "\\red",
            "\\green", "\\gray", "\\purple"
        ],
        data: {
            numArgs: 1,
            allowedInText: true,
            handler: function(func, body) {
                var atoms;
                if (body.type === "ordgroup") {
                    atoms = body.value;
                } else {
                    atoms = [body];
                }

                return {
                    type: "color",
                    color: "katex-" + func.slice(1),
                    value: atoms
                };
            }
        }
    },

    // There are 2 flags for operators; whether they produce limits in
    // displaystyle, and whether they are symbols and should grow in
    // displaystyle. These four groups cover the four possible choices.

    // No limits, not symbols
    {
        funcs: [
            "\\arcsin", "\\arccos", "\\arctan", "\\arg", "\\cos", "\\cosh",
            "\\cot", "\\coth", "\\csc", "\\deg", "\\dim", "\\exp", "\\hom",
            "\\ker", "\\lg", "\\ln", "\\log", "\\sec", "\\sin", "\\sinh",
            "\\tan","\\tanh"
        ],
        data: {
            numArgs: 0,
            handler: function(func) {
                return {
                    type: "op",
                    limits: false,
                    symbol: false,
                    body: func
                };
            }
        }
    },

    // Limits, not symbols
    {
        funcs: [
            "\\det", "\\gcd", "\\inf", "\\lim", "\\liminf", "\\limsup", "\\max",
            "\\min", "\\Pr", "\\sup"
        ],
        data: {
            numArgs: 0,
            handler: function(func) {
                return {
                    type: "op",
                    limits: true,
                    symbol: false,
                    body: func
                };
            }
        }
    },

    // No limits, symbols
    {
        funcs: [
            "\\int", "\\iint", "\\iiint", "\\oint"
        ],
        data: {
            numArgs: 0,
            handler: function(func) {
                return {
                    type: "op",
                    limits: false,
                    symbol: true,
                    body: func
                };
            }
        }
    },

    // Limits, symbols
    {
        funcs: [
            "\\coprod", "\\bigvee", "\\bigwedge", "\\biguplus", "\\bigcap",
            "\\bigcup", "\\intop", "\\prod", "\\sum", "\\bigotimes",
            "\\bigoplus", "\\bigodot", "\\bigsqcup", "\\smallint"
        ],
        data: {
            numArgs: 0,
            handler: function(func) {
                return {
                    type: "op",
                    limits: true,
                    symbol: true,
                    body: func
                };
            }
        }
    },

    // Fractions
    {
        funcs: [
            "\\dfrac", "\\frac", "\\tfrac",
            "\\dbinom", "\\binom", "\\tbinom"
        ],
        data: {
            numArgs: 2,
            greediness: 2,
            handler: function(func, numer, denom) {
                var hasBarLine;
                var leftDelim = null;
                var rightDelim = null;
                var size = "auto";

                switch (func) {
                    case "\\dfrac":
                    case "\\frac":
                    case "\\tfrac":
                        hasBarLine = true;
                        break;
                    case "\\dbinom":
                    case "\\binom":
                    case "\\tbinom":
                        hasBarLine = false;
                        leftDelim = "(";
                        rightDelim = ")";
                        break;
                    default:
                        throw new Error("Unrecognized genfrac command");
                }

                switch (func) {
                    case "\\dfrac":
                    case "\\dbinom":
                        size = "display";
                        break;
                    case "\\tfrac":
                    case "\\tbinom":
                        size = "text";
                        break;
                }

                return {
                    type: "genfrac",
                    numer: numer,
                    denom: denom,
                    hasBarLine: hasBarLine,
                    leftDelim: leftDelim,
                    rightDelim: rightDelim,
                    size: size
                };
            }
        }
    },

    // Left and right overlap functions
    {
        funcs: ["\\llap", "\\rlap"],
        data: {
            numArgs: 1,
            allowedInText: true,
            handler: function(func, body) {
                return {
                    type: func.slice(1),
                    body: body
                };
            }
        }
    },

    // Delimiter functions
    {
        funcs: [
            "\\bigl", "\\Bigl", "\\biggl", "\\Biggl",
            "\\bigr", "\\Bigr", "\\biggr", "\\Biggr",
            "\\bigm", "\\Bigm", "\\biggm", "\\Biggm",
            "\\big",  "\\Big",  "\\bigg",  "\\Bigg",
            "\\left", "\\right"
        ],
        data: {
            numArgs: 1,
            handler: function(func, delim, positions) {
                if (!utils.contains(delimiters, delim.value)) {
                    throw new ParseError(
                        "Invalid delimiter: '" + delim.value + "' after '" +
                            func + "'",
                        this.lexer, positions[1]);
                }

                // left and right are caught somewhere in Parser.js, which is
                // why this data doesn't match what is in buildTree
                if (func === "\\left" || func === "\\right") {
                    return {
                        type: "leftright",
                        value: delim.value
                    };
                } else {
                    return {
                        type: "delimsizing",
                        size: delimiterSizes[func].size,
                        delimType: delimiterSizes[func].type,
                        value: delim.value
                    };
                }
            }
        }
    },

    // Sizing functions (handled in Parser.js explicitly, hence no handler)
    {
        funcs: [
            "\\tiny", "\\scriptsize", "\\footnotesize", "\\small",
            "\\normalsize", "\\large", "\\Large", "\\LARGE", "\\huge", "\\Huge"
        ],
        data: {
            numArgs: 0
        }
    },

    // Style changing functions (handled in Parser.js explicitly, hence no
    // handler)
    {
        funcs: [
            "\\displaystyle", "\\textstyle", "\\scriptstyle",
            "\\scriptscriptstyle"
        ],
        data: {
            numArgs: 0
        }
    },

    // Accents
    {
        funcs: [
            "\\acute", "\\grave", "\\ddot", "\\tilde", "\\bar", "\\breve",
            "\\check", "\\hat", "\\vec", "\\dot"
            // We don't support expanding accents yet
            // "\\widetilde", "\\widehat"
        ],
        data: {
            numArgs: 1,
            handler: function(func, base) {
                return {
                    type: "accent",
                    accent: func,
                    base: base
                };
            }
        }
    },

    // Infix generalized fractions
    {
        funcs: ["\\over", "\\choose"],
        data: {
            numArgs: 0,
            handler: function (func) {
                var replaceWith;
                switch (func) {
                    case "\\over":
                        replaceWith = "\\frac";
                        break;
                    case "\\choose":
                        replaceWith = "\\binom";
                        break;
                    default:
                        throw new Error("Unrecognized infix genfrac command");
                }
                return {
                    type: "infix",
                    replaceWith: replaceWith
                };
            }
        }
    }
];

var addFuncsWithData = function(funcs, data) {
    for (var i = 0; i < funcs.length; i++) {
        functions[funcs[i]] = data;
    }
};

// Add all of the functions in duplicatedFunctions to the functions map
for (var i = 0; i < duplicatedFunctions.length; i++) {
    addFuncsWithData(duplicatedFunctions[i].funcs, duplicatedFunctions[i].data);
}

// Returns the greediness of a given function. Since greediness is optional, we
// use this function to put in the default value if it is undefined.
var getGreediness = function(func) {
    if (functions[func].greediness === undefined) {
        return 1;
    } else {
        return functions[func].greediness;
    }
};

// Set default values of functions
for (var f in functions) {
    if (functions.hasOwnProperty(f)) {
        var func = functions[f];

        functions[f] = {
            numArgs: func.numArgs,
            argTypes: func.argTypes,
            greediness: (func.greediness === undefined) ? 1 : func.greediness,
            allowedInText: func.allowedInText ? func.allowedInText : false,
            numOptionalArgs: (func.numOptionalArgs === undefined) ? 0 :
                func.numOptionalArgs,
            handler: func.handler
        };
    }
}

module.exports = {
    funcs: functions,
    getGreediness: getGreediness
};

},{"./ParseError":4,"./utils":15}],13:[function(require,module,exports){
/**
 * Provides a single function for parsing an expression using a Parser
 * TODO(emily): Remove this
 */

var Parser = require("./Parser");

/**
 * Parses an expression using a Parser, then returns the parsed result.
 */
var parseTree = function(toParse) {
    var parser = new Parser(toParse);

    return parser.parse();
};

module.exports = parseTree;

},{"./Parser":5}],14:[function(require,module,exports){
/**
 * This file holds a list of all no-argument functions and single-character
 * symbols (like 'a' or ';').
 *
 * For each of the symbols, there are three properties they can have:
 * - font (required): the font to be used for this symbol. Either "main" (the
     normal font), or "ams" (the ams fonts).
 * - group (required): the ParseNode group type the symbol should have (i.e.
     "textord", "mathord", etc).
 * - replace (optional): the character that this symbol or function should be
 *   replaced with (i.e. "\phi" has a replace value of "\u03d5", the phi
 *   character in the main font).
 *
 * The outermost map in the table indicates what mode the symbols should be
 * accepted in (e.g. "math" or "text").
 */

var symbols = {
    "math": {
        "`": {
            font: "main",
            group: "textord",
            replace: "\u2018"
        },
        "\\$": {
            font: "main",
            group: "textord",
            replace: "$"
        },
        "\\%": {
            font: "main",
            group: "textord",
            replace: "%"
        },
        "\\_": {
            font: "main",
            group: "textord",
            replace: "_"
        },
        "\\angle": {
            font: "main",
            group: "textord",
            replace: "\u2220"
        },
        "\\infty": {
            font: "main",
            group: "textord",
            replace: "\u221e"
        },
        "\\prime": {
            font: "main",
            group: "textord",
            replace: "\u2032"
        },
        "\\triangle": {
            font: "main",
            group: "textord",
            replace: "\u25b3"
        },
        "\\Gamma": {
            font: "main",
            group: "textord",
            replace: "\u0393"
        },
        "\\Delta": {
            font: "main",
            group: "textord",
            replace: "\u0394"
        },
        "\\Theta": {
            font: "main",
            group: "textord",
            replace: "\u0398"
        },
        "\\Lambda": {
            font: "main",
            group: "textord",
            replace: "\u039b"
        },
        "\\Xi": {
            font: "main",
            group: "textord",
            replace: "\u039e"
        },
        "\\Pi": {
            font: "main",
            group: "textord",
            replace: "\u03a0"
        },
        "\\Sigma": {
            font: "main",
            group: "textord",
            replace: "\u03a3"
        },
        "\\Upsilon": {
            font: "main",
            group: "textord",
            replace: "\u03a5"
        },
        "\\Phi": {
            font: "main",
            group: "textord",
            replace: "\u03a6"
        },
        "\\Psi": {
            font: "main",
            group: "textord",
            replace: "\u03a8"
        },
        "\\Omega": {
            font: "main",
            group: "textord",
            replace: "\u03a9"
        },
        "\\neg": {
            font: "main",
            group: "textord",
            replace: "\u00ac"
        },
        "\\lnot": {
            font: "main",
            group: "textord",
            replace: "\u00ac"
        },
        "\\top": {
            font: "main",
            group: "textord",
            replace: "\u22a4"
        },
        "\\bot": {
            font: "main",
            group: "textord",
            replace: "\u22a5"
        },
        "\\emptyset": {
            font: "main",
            group: "textord",
            replace: "\u2205"
        },
        "\\varnothing": {
            font: "ams",
            group: "textord",
            replace: "\u2205"
        },
        "\\alpha": {
            font: "main",
            group: "mathord",
            replace: "\u03b1"
        },
        "\\beta": {
            font: "main",
            group: "mathord",
            replace: "\u03b2"
        },
        "\\gamma": {
            font: "main",
            group: "mathord",
            replace: "\u03b3"
        },
        "\\delta": {
            font: "main",
            group: "mathord",
            replace: "\u03b4"
        },
        "\\epsilon": {
            font: "main",
            group: "mathord",
            replace: "\u03f5"
        },
        "\\zeta": {
            font: "main",
            group: "mathord",
            replace: "\u03b6"
        },
        "\\eta": {
            font: "main",
            group: "mathord",
            replace: "\u03b7"
        },
        "\\theta": {
            font: "main",
            group: "mathord",
            replace: "\u03b8"
        },
        "\\iota": {
            font: "main",
            group: "mathord",
            replace: "\u03b9"
        },
        "\\kappa": {
            font: "main",
            group: "mathord",
            replace: "\u03ba"
        },
        "\\lambda": {
            font: "main",
            group: "mathord",
            replace: "\u03bb"
        },
        "\\mu": {
            font: "main",
            group: "mathord",
            replace: "\u03bc"
        },
        "\\nu": {
            font: "main",
            group: "mathord",
            replace: "\u03bd"
        },
        "\\xi": {
            font: "main",
            group: "mathord",
            replace: "\u03be"
        },
        "\\omicron": {
            font: "main",
            group: "mathord",
            replace: "o"
        },
        "\\pi": {
            font: "main",
            group: "mathord",
            replace: "\u03c0"
        },
        "\\rho": {
            font: "main",
            group: "mathord",
            replace: "\u03c1"
        },
        "\\sigma": {
            font: "main",
            group: "mathord",
            replace: "\u03c3"
        },
        "\\tau": {
            font: "main",
            group: "mathord",
            replace: "\u03c4"
        },
        "\\upsilon": {
            font: "main",
            group: "mathord",
            replace: "\u03c5"
        },
        "\\phi": {
            font: "main",
            group: "mathord",
            replace: "\u03d5"
        },
        "\\chi": {
            font: "main",
            group: "mathord",
            replace: "\u03c7"
        },
        "\\psi": {
            font: "main",
            group: "mathord",
            replace: "\u03c8"
        },
        "\\omega": {
            font: "main",
            group: "mathord",
            replace: "\u03c9"
        },
        "\\varepsilon": {
            font: "main",
            group: "mathord",
            replace: "\u03b5"
        },
        "\\vartheta": {
            font: "main",
            group: "mathord",
            replace: "\u03d1"
        },
        "\\varpi": {
            font: "main",
            group: "mathord",
            replace: "\u03d6"
        },
        "\\varrho": {
            font: "main",
            group: "mathord",
            replace: "\u03f1"
        },
        "\\varsigma": {
            font: "main",
            group: "mathord",
            replace: "\u03c2"
        },
        "\\varphi": {
            font: "main",
            group: "mathord",
            replace: "\u03c6"
        },
        "*": {
            font: "main",
            group: "bin",
            replace: "\u2217"
        },
        "+": {
            font: "main",
            group: "bin"
        },
        "-": {
            font: "main",
            group: "bin",
            replace: "\u2212"
        },
        "\\cdot": {
            font: "main",
            group: "bin",
            replace: "\u22c5"
        },
        "\\circ": {
            font: "main",
            group: "bin",
            replace: "\u2218"
        },
        "\\div": {
            font: "main",
            group: "bin",
            replace: "\u00f7"
        },
        "\\pm": {
            font: "main",
            group: "bin",
            replace: "\u00b1"
        },
        "\\times": {
            font: "main",
            group: "bin",
            replace: "\u00d7"
        },
        "\\cap": {
            font: "main",
            group: "bin",
            replace: "\u2229"
        },
        "\\cup": {
            font: "main",
            group: "bin",
            replace: "\u222a"
        },
        "\\setminus": {
            font: "main",
            group: "bin",
            replace: "\u2216"
        },
        "\\land": {
            font: "main",
            group: "bin",
            replace: "\u2227"
        },
        "\\lor": {
            font: "main",
            group: "bin",
            replace: "\u2228"
        },
        "\\wedge": {
            font: "main",
            group: "bin",
            replace: "\u2227"
        },
        "\\vee": {
            font: "main",
            group: "bin",
            replace: "\u2228"
        },
        "\\surd": {
            font: "main",
            group: "textord",
            replace: "\u221a"
        },
        "(": {
            font: "main",
            group: "open"
        },
        "[": {
            font: "main",
            group: "open"
        },
        "\\langle": {
            font: "main",
            group: "open",
            replace: "\u27e8"
        },
        "\\lvert": {
            font: "main",
            group: "open",
            replace: "\u2223"
        },
        ")": {
            font: "main",
            group: "close"
        },
        "]": {
            font: "main",
            group: "close"
        },
        "?": {
            font: "main",
            group: "close"
        },
        "!": {
            font: "main",
            group: "close"
        },
        "\\rangle": {
            font: "main",
            group: "close",
            replace: "\u27e9"
        },
        "\\rvert": {
            font: "main",
            group: "close",
            replace: "\u2223"
        },
        "=": {
            font: "main",
            group: "rel"
        },
        "<": {
            font: "main",
            group: "rel"
        },
        ">": {
            font: "main",
            group: "rel"
        },
        ":": {
            font: "main",
            group: "rel"
        },
        "\\approx": {
            font: "main",
            group: "rel",
            replace: "\u2248"
        },
        "\\cong": {
            font: "main",
            group: "rel",
            replace: "\u2245"
        },
        "\\ge": {
            font: "main",
            group: "rel",
            replace: "\u2265"
        },
        "\\geq": {
            font: "main",
            group: "rel",
            replace: "\u2265"
        },
        "\\gets": {
            font: "main",
            group: "rel",
            replace: "\u2190"
        },
        "\\in": {
            font: "main",
            group: "rel",
            replace: "\u2208"
        },
        "\\notin": {
            font: "main",
            group: "rel",
            replace: "\u2209"
        },
        "\\subset": {
            font: "main",
            group: "rel",
            replace: "\u2282"
        },
        "\\supset": {
            font: "main",
            group: "rel",
            replace: "\u2283"
        },
        "\\subseteq": {
            font: "main",
            group: "rel",
            replace: "\u2286"
        },
        "\\supseteq": {
            font: "main",
            group: "rel",
            replace: "\u2287"
        },
        "\\nsubseteq": {
            font: "ams",
            group: "rel",
            replace: "\u2288"
        },
        "\\nsupseteq": {
            font: "ams",
            group: "rel",
            replace: "\u2289"
        },
        "\\models": {
            font: "main",
            group: "rel",
            replace: "\u22a8"
        },
        "\\leftarrow": {
            font: "main",
            group: "rel",
            replace: "\u2190"
        },
        "\\le": {
            font: "main",
            group: "rel",
            replace: "\u2264"
        },
        "\\leq": {
            font: "main",
            group: "rel",
            replace: "\u2264"
        },
        "\\ne": {
            font: "main",
            group: "rel",
            replace: "\u2260"
        },
        "\\neq": {
            font: "main",
            group: "rel",
            replace: "\u2260"
        },
        "\\rightarrow": {
            font: "main",
            group: "rel",
            replace: "\u2192"
        },
        "\\to": {
            font: "main",
            group: "rel",
            replace: "\u2192"
        },
        "\\ngeq": {
            font: "ams",
            group: "rel",
            replace: "\u2271"
        },
        "\\nleq": {
            font: "ams",
            group: "rel",
            replace: "\u2270"
        },
        "\\!": {
            font: "main",
            group: "spacing"
        },
        "\\ ": {
            font: "main",
            group: "spacing",
            replace: "\u00a0"
        },
        "~": {
            font: "main",
            group: "spacing",
            replace: "\u00a0"
        },
        "\\,": {
            font: "main",
            group: "spacing"
        },
        "\\:": {
            font: "main",
            group: "spacing"
        },
        "\\;": {
            font: "main",
            group: "spacing"
        },
        "\\enspace": {
            font: "main",
            group: "spacing"
        },
        "\\qquad": {
            font: "main",
            group: "spacing"
        },
        "\\quad": {
            font: "main",
            group: "spacing"
        },
        "\\space": {
            font: "main",
            group: "spacing",
            replace: "\u00a0"
        },
        ",": {
            font: "main",
            group: "punct"
        },
        ";": {
            font: "main",
            group: "punct"
        },
        "\\colon": {
            font: "main",
            group: "punct",
            replace: ":"
        },
        "\\barwedge": {
            font: "ams",
            group: "textord",
            replace: "\u22bc"
        },
        "\\veebar": {
            font: "ams",
            group: "textord",
            replace: "\u22bb"
        },
        "\\odot": {
            font: "main",
            group: "textord",
            replace: "\u2299"
        },
        "\\oplus": {
            font: "main",
            group: "textord",
            replace: "\u2295"
        },
        "\\otimes": {
            font: "main",
            group: "textord",
            replace: "\u2297"
        },
        "\\partial":{
            font: "main",
            group: "textord",
            replace: "\u2202"
        },
        "\\oslash": {
            font: "main",
            group: "textord",
            replace: "\u2298"
        },
        "\\circledcirc": {
            font: "ams",
            group: "textord",
            replace: "\u229a"
        },
        "\\boxdot": {
            font: "ams",
            group: "textord",
            replace: "\u22a1"
        },
        "\\bigtriangleup": {
            font: "main",
            group: "textord",
            replace: "\u25b3"
        },
        "\\bigtriangledown": {
            font: "main",
            group: "textord",
            replace: "\u25bd"
        },
        "\\dagger": {
            font: "main",
            group: "textord",
            replace: "\u2020"
        },
        "\\diamond": {
            font: "main",
            group: "textord",
            replace: "\u22c4"
        },
        "\\star": {
            font: "main",
            group: "textord",
            replace: "\u22c6"
        },
        "\\triangleleft": {
            font: "main",
            group: "textord",
            replace: "\u25c3"
        },
        "\\triangleright": {
            font: "main",
            group: "textord",
            replace: "\u25b9"
        },
        "\\{": {
            font: "main",
            group: "open",
            replace: "{"
        },
        "\\}": {
            font: "main",
            group: "close",
            replace: "}"
        },
        "\\lbrace": {
            font: "main",
            group: "open",
            replace: "{"
        },
        "\\rbrace": {
            font: "main",
            group: "close",
            replace: "}"
        },
        "\\lbrack": {
            font: "main",
            group: "open",
            replace: "["
        },
        "\\rbrack": {
            font: "main",
            group: "close",
            replace: "]"
        },
        "\\lfloor": {
            font: "main",
            group: "open",
            replace: "\u230a"
        },
        "\\rfloor": {
            font: "main",
            group: "close",
            replace: "\u230b"
        },
        "\\lceil": {
            font: "main",
            group: "open",
            replace: "\u2308"
        },
        "\\rceil": {
            font: "main",
            group: "close",
            replace: "\u2309"
        },
        "\\backslash": {
            font: "main",
            group: "textord",
            replace: "\\"
        },
        "|": {
            font: "main",
            group: "textord",
            replace: "\u2223"
        },
        "\\vert": {
            font: "main",
            group: "textord",
            replace: "\u2223"
        },
        "\\|": {
            font: "main",
            group: "textord",
            replace: "\u2225"
        },
        "\\Vert": {
            font: "main",
            group: "textord",
            replace: "\u2225"
        },
        "\\uparrow": {
            font: "main",
            group: "textord",
            replace: "\u2191"
        },
        "\\Uparrow": {
            font: "main",
            group: "textord",
            replace: "\u21d1"
        },
        "\\downarrow": {
            font: "main",
            group: "textord",
            replace: "\u2193"
        },
        "\\Downarrow": {
            font: "main",
            group: "textord",
            replace: "\u21d3"
        },
        "\\updownarrow": {
            font: "main",
            group: "textord",
            replace: "\u2195"
        },
        "\\Updownarrow": {
            font: "main",
            group: "textord",
            replace: "\u21d5"
        },
        "\\coprod": {
            font: "math",
            group: "op",
            replace: "\u2210"
        },
        "\\bigvee": {
            font: "math",
            group: "op",
            replace: "\u22c1"
        },
        "\\bigwedge": {
            font: "math",
            group: "op",
            replace: "\u22c0"
        },
        "\\biguplus": {
            font: "math",
            group: "op",
            replace: "\u2a04"
        },
        "\\bigcap": {
            font: "math",
            group: "op",
            replace: "\u22c2"
        },
        "\\bigcup": {
            font: "math",
            group: "op",
            replace: "\u22c3"
        },
        "\\int": {
            font: "math",
            group: "op",
            replace: "\u222b"
        },
        "\\intop": {
            font: "math",
            group: "op",
            replace: "\u222b"
        },
        "\\iint": {
            font: "math",
            group: "op",
            replace: "\u222c"
        },
        "\\iiint": {
            font: "math",
            group: "op",
            replace: "\u222d"
        },
        "\\prod": {
            font: "math",
            group: "op",
            replace: "\u220f"
        },
        "\\sum": {
            font: "math",
            group: "op",
            replace: "\u2211"
        },
        "\\bigotimes": {
            font: "math",
            group: "op",
            replace: "\u2a02"
        },
        "\\bigoplus": {
            font: "math",
            group: "op",
            replace: "\u2a01"
        },
        "\\bigodot": {
            font: "math",
            group: "op",
            replace: "\u2a00"
        },
        "\\oint": {
            font: "math",
            group: "op",
            replace: "\u222e"
        },
        "\\bigsqcup": {
            font: "math",
            group: "op",
            replace: "\u2a06"
        },
        "\\smallint": {
            font: "math",
            group: "op",
            replace: "\u222b"
        },
        "\\ldots": {
            font: "main",
            group: "punct",
            replace: "\u2026"
        },
        "\\cdots": {
            font: "main",
            group: "inner",
            replace: "\u22ef"
        },
        "\\ddots": {
            font: "main",
            group: "inner",
            replace: "\u22f1"
        },
        "\\vdots": {
            font: "main",
            group: "textord",
            replace: "\u22ee"
        },
        "\\acute": {
            font: "main",
            group: "accent",
            replace: "\u00b4"
        },
        "\\grave": {
            font: "main",
            group: "accent",
            replace: "\u0060"
        },
        "\\ddot": {
            font: "main",
            group: "accent",
            replace: "\u00a8"
        },
        "\\tilde": {
            font: "main",
            group: "accent",
            replace: "\u007e"
        },
        "\\bar": {
            font: "main",
            group: "accent",
            replace: "\u00af"
        },
        "\\breve": {
            font: "main",
            group: "accent",
            replace: "\u02d8"
        },
        "\\check": {
            font: "main",
            group: "accent",
            replace: "\u02c7"
        },
        "\\hat": {
            font: "main",
            group: "accent",
            replace: "\u005e"
        },
        "\\vec": {
            font: "main",
            group: "accent",
            replace: "\u20d7"
        },
        "\\dot": {
            font: "main",
            group: "accent",
            replace: "\u02d9"
        }
    },
    "text": {
        "\\ ": {
            font: "main",
            group: "spacing",
            replace: "\u00a0"
        },
        " ": {
            font: "main",
            group: "spacing",
            replace: "\u00a0"
        },
        "~": {
            font: "main",
            group: "spacing",
            replace: "\u00a0"
        }
    }
};

// There are lots of symbols which are the same, so we add them in afterwards.

// All of these are textords in math mode
var mathTextSymbols = "0123456789/@.\"";
for (var i = 0; i < mathTextSymbols.length; i++) {
    var ch = mathTextSymbols.charAt(i);
    symbols.math[ch] = {
        font: "main",
        group: "textord"
    };
}

// All of these are textords in text mode
var textSymbols = "0123456789`!@*()-=+[]'\";:?/.,";
for (var i = 0; i < textSymbols.length; i++) {
    var ch = textSymbols.charAt(i);
    symbols.text[ch] = {
        font: "main",
        group: "textord"
    };
}

// All of these are textords in text mode, and mathords in math mode
var letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
for (var i = 0; i < letters.length; i++) {
    var ch = letters.charAt(i);
    symbols.math[ch] = {
        font: "main",
        group: "mathord"
    };
    symbols.text[ch] = {
        font: "main",
        group: "textord"
    };
}

module.exports = symbols;

},{}],15:[function(require,module,exports){
/**
 * This file contains a list of utility functions which are useful in other
 * files.
 */

/**
 * Provide an `indexOf` function which works in IE8, but defers to native if
 * possible.
 */
var nativeIndexOf = Array.prototype.indexOf;
var indexOf = function(list, elem) {
    if (list == null) {
        return -1;
    }
    if (nativeIndexOf && list.indexOf === nativeIndexOf) {
        return list.indexOf(elem);
    }
    var i = 0, l = list.length;
    for (; i < l; i++) {
        if (list[i] === elem) {
            return i;
        }
    }
    return -1;
};

/**
 * Return whether an element is contained in a list
 */
var contains = function(list, elem) {
    return indexOf(list, elem) !== -1;
};

// hyphenate and escape adapted from Facebook's React under Apache 2 license

var uppercase = /([A-Z])/g;
var hyphenate = function(str) {
    return str.replace(uppercase, "-$1").toLowerCase();
};

var ESCAPE_LOOKUP = {
  "&": "&amp;",
  ">": "&gt;",
  "<": "&lt;",
  "\"": "&quot;",
  "'": "&#x27;"
};

var ESCAPE_REGEX = /[&><"']/g;

function escaper(match) {
  return ESCAPE_LOOKUP[match];
}

/**
 * Escapes text to prevent scripting attacks.
 *
 * @param {*} text Text value to escape.
 * @return {string} An escaped string.
 */
function escape(text) {
  return ("" + text).replace(ESCAPE_REGEX, escaper);
}

/**
 * A function to set the text content of a DOM element in all supported
 * browsers. Note that we don't define this if there is no document.
 */
var setTextContent;
if (typeof document !== "undefined") {
    var testNode = document.createElement("span");
    if ("textContent" in testNode) {
        setTextContent = function(node, text) {
            node.textContent = text;
        };
    } else {
        setTextContent = function(node, text) {
            node.innerText = text;
        };
    }
}

/**
 * A function to clear a node.
 */
function clearNode(node) {
    setTextContent(node, "");
}

module.exports = {
    contains: contains,
    escape: escape,
    hyphenate: hyphenate,
    indexOf: indexOf,
    setTextContent: setTextContent,
    clearNode: clearNode
};

},{}]},{},[1])
(1)
});
;