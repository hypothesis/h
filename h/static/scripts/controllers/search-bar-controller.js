import escapeHtml from 'escape-html';

import { Controller } from '../base/controller';
import { cloneTemplate } from '../util/dom';
import { getLozengeValues, shouldLozengify } from '../util/search-text-parser';
import * as stringUtil from '../util/string';

import { AutosuggestDropdownController } from './autosuggest-dropdown-controller';
import { LozengeController } from './lozenge-controller';

const FACET_TYPE = 'FACET';
const TAG_TYPE = 'TAG';
const GROUP_TYPE = 'GROUP';
const MAX_SUGGESTIONS = 5;

/**
 * Normalize a string for use in comparisons of user input with a suggestion.
 * This causes differences in unicode composition and combining characters/accents to be ignored.
 */
const normalizeStr = function (str) {
  return stringUtil.fold(stringUtil.normalize(str));
};

/**
 * Controller for the search bar.
 */
export class SearchBarController extends Controller {
  constructor(element, options = {}) {
    super(element, options);

    if (!options.lozengeTemplate) {
      options.lozengeTemplate = document.querySelector('#lozenge-template');
    }

    this._input = this.refs.searchBarInput;
    this._lozengeContainer = this.refs.searchBarLozenges;

    /**
     * the suggestionsMap pulls in the available lists - either
     *  static or dynamic living in the dom - into one mapping
     *  lists of all suggestion values.
     */
    this._suggestionsMap = (() => {
      const explanationList = [
        {
          matchOn: 'user',
          title: 'user:',
          explanation: 'search by username',
        },
        {
          matchOn: 'tag',
          title: 'tag:',
          explanation: 'search for annotations with a tag',
        },
        {
          matchOn: 'url',
          title: 'url:',
          explanation: `search by URL<br>for domain level search
            add trailing /* eg. example.com/*`,
        },
        {
          matchOn: 'group',
          title: 'group:',
          explanation: 'show annotations associated with a group',
        },
      ].map(item => {
        return Object.assign(item, { type: FACET_TYPE });
      });

      // tagSuggestions are made available by the scoped template data.
      // see search.html.jinja2 for definition
      const tagSuggestionJSON = document.querySelector('.js-tag-suggestions');
      let tagSuggestions = [];

      if (tagSuggestionJSON) {
        try {
          tagSuggestions = JSON.parse(tagSuggestionJSON.innerHTML.trim());
        } catch (e) {
          console.error('Could not parse .js-tag-suggestions JSON content', e);
        }
      }

      const tagsList = (tagSuggestions || []).map(item => {
        return Object.assign(item, {
          type: TAG_TYPE,
          title: item.tag, // make safe
          matchOn: normalizeStr(item.tag),
          usageCount: item.count || 0,
        });
      });

      // groupSuggestions are made available by the scoped template data.
      // see search.html.jinja2 for definition
      const groupSuggestionJSON = document.querySelector(
        '.js-group-suggestions',
      );
      let groupSuggestions = [];

      if (groupSuggestionJSON) {
        try {
          groupSuggestions = JSON.parse(groupSuggestionJSON.innerHTML.trim());
        } catch (e) {
          console.error(
            'Could not parse .js-group-suggestions JSON content',
            e,
          );
        }
      }

      const groupsList = (groupSuggestions || []).map(item => {
        return Object.assign(item, {
          type: GROUP_TYPE,
          title: item.name, // make safe
          matchOn: normalizeStr(item.name),
          pubid: item.pubid,
          name: item.name,
          relationship: item.relationship,
        });
      });

      return explanationList.concat(tagsList, groupsList);
    })();

    const getTrimmedInputValue = () => {
      return this._input.value.trim();
    };

    /**
     * given a lozenge set for a group, like "group:value", match the value
     *  against our group suggestions list to find a match on either pubid
     *  or the group name. The result will be an object to identify what
     *  is the search input term to use and what value can be displayed
     *  to the user. If there is no match, the input and display will be
     *  the original input value.
     *
     *  @param {String} groupLoz - ex: "group:value"
     *  @returns {Object} represents the values to display and use for inputVal
     *    {
     *      display: {String}, // like group:"friendly name"
     *      input: {String}    // like group:pid1234
     *    }
     */
    const getInputAndDisplayValsForGroup = groupLoz => {
      let groupVal = groupLoz.substr(groupLoz.indexOf(':') + 1).trim();
      let inputVal = groupVal.trim();
      let displayVal = groupVal;
      const wrapQuotesIfNeeded = function (str) {
        return str.indexOf(' ') > -1 ? `"${str}"` : str;
      };

      // remove quotes from value
      if (groupVal[0] === '"' || groupVal[0] === "'") {
        groupVal = groupVal.substr(1);
      }
      if (
        groupVal[groupVal.length - 1] === '"' ||
        groupVal[groupVal.length - 1] === "'"
      ) {
        groupVal = groupVal.slice(0, -1);
      }

      const matchVal = normalizeStr(groupVal).toLowerCase();

      // NOTE: We are pushing a pubid to lowercase here. These ids are created by us
      // in a random generation case-sensistive style. Theoretically, that means
      // casting to lower could cause overlaps of values like 'Abc' and 'aBC' - making
      // them equal to us. Since that is very unlikely to occur for one user's group
      // set, the convenience of being defensive about bad input/urls is more valuable
      // than the risk of overlap.
      const matchByPubid = this._suggestionsMap.find(item => {
        return (
          item.type === GROUP_TYPE && item.pubid.toLowerCase() === matchVal
        );
      });

      if (matchByPubid) {
        inputVal = matchByPubid.pubid;
        displayVal = wrapQuotesIfNeeded(matchByPubid.name);
      } else {
        const matchByName = this._suggestionsMap.find(item => {
          return (
            item.type === GROUP_TYPE && item.matchOn.toLowerCase() === matchVal
          );
        });
        if (matchByName) {
          inputVal = matchByName.pubid;
          displayVal = wrapQuotesIfNeeded(matchByName.name);
        }
      }

      return {
        input: 'group:' + inputVal,
        display: 'group:' + displayVal,
      };
    };

    /**
     * Insert a hidden <input> with an empty value into the search <form>.
     *
     * The name="q" attribute is moved from the visible <input> on to the
     * hidden <input> so that when the <form> is submitted it's the value of
     * the _hidden_ input, not the visible one, that is submitted as the
     * q parameter.
     *
     */
    const insertHiddenInput = () => {
      const hiddenInput = document.createElement('input');
      hiddenInput.type = 'hidden';

      // When JavaScript isn't enabled this._input is submitted to the server
      // as the q param. With JavaScript we submit hiddenInput instead.
      hiddenInput.name = this._input.name;
      this._input.removeAttribute('name');

      this.refs.searchBarForm.appendChild(hiddenInput);
      return hiddenInput;
    };

    /** Return the controllers for all of the displayed lozenges. */
    const lozenges = () => {
      const lozElements = Array.from(
        this.element.querySelectorAll('.js-lozenge'),
      );
      return lozElements.map(el => el.controllers[0]);
    };

    /**
     * Update the value of the hidden input.
     *
     * Update the value of the hidden input based on the contents of any
     * lozenges and any remaining text in the visible input.
     *
     * This should be called whenever a lozenge is added to or removed from
     * the DOM, and whenever the text in the visible input changes.
     *
     */
    const updateHiddenInput = () => {
      let newValue = '';
      lozenges().forEach(loz => {
        let inputValue = loz.inputValue();
        if (inputValue.indexOf('group:') === 0) {
          inputValue = getInputAndDisplayValsForGroup(inputValue).input;
        }
        newValue = newValue + inputValue + ' ';
      });
      this._hiddenInput.value = (newValue + getTrimmedInputValue()).trim();
    };

    /**
     * Creates a lozenge and sets the content string to the
     * content provided and executes the delete callback when
     * the lozenge is deleted.
     *
     * @param {string} content The search term
     */
    const addLozenge = content => {
      const lozengeEl = cloneTemplate(this.options.lozengeTemplate);
      const currentLozenges = this.element.querySelectorAll('.lozenge');
      if (currentLozenges.length > 0) {
        this._lozengeContainer.insertBefore(
          lozengeEl,
          currentLozenges[currentLozenges.length - 1].nextSibling,
        );
      } else {
        this._lozengeContainer.insertBefore(
          lozengeEl,
          this._lozengeContainer.firstChild,
        );
      }

      const deleteCallback = () => {
        lozengeEl.remove();
        lozenges().forEach(ctrl => ctrl.setState({ disabled: true }));
        updateHiddenInput();
        this.refs.searchBarForm.submit();
      };

      // groups have extra logic to show one value
      // but have their input/search value be different
      // make sure we grab the right value to display
      if (content.indexOf('group:') === 0) {
        content = getInputAndDisplayValsForGroup(content).display;
      }

      new LozengeController(lozengeEl, {
        content,
        deleteCallback,
      });
    };

    /**
     * Create lozenges for the search query terms already in the input field on
     * page load and update lozenges that are already in the lozenges container
     * so they are hooked up with the proper event handling
     */
    const lozengifyInput = () => {
      const { lozengeValues, incompleteInputValue } = getLozengeValues(
        this._input.value,
      );

      lozengeValues.forEach(addLozenge);
      this._input.value = incompleteInputValue;
      this._input.style.visibility = 'visible';
      updateHiddenInput();
    };

    const onInputKeyDown = event => {
      const SPACE_KEY_CODE = 32;

      if (event.keyCode === SPACE_KEY_CODE) {
        const word = getTrimmedInputValue();
        if (shouldLozengify(word)) {
          event.preventDefault();
          addLozenge(word);
          this._input.value = '';
          updateHiddenInput();
        }
      }
    };

    this._hiddenInput = insertHiddenInput(this.refs.searchBarForm);

    this._suggestionsHandler = new AutosuggestDropdownController(this._input, {
      list: this._suggestionsMap,

      header: 'Narrow your search:',

      classNames: {
        container: 'search-bar__dropdown-menu-container',
        header: 'search-bar__dropdown-menu-header',
        list: 'search-bar__dropdown-menu',
        item: 'search-bar__dropdown-menu-item',
        activeItem: 'js-search-bar-dropdown-menu-item--active',
      },

      renderListItem: listItem => {
        let itemContents = `<span class="search-bar__dropdown-menu-title"> ${escapeHtml(
          listItem.title,
        )} </span>`;
        if (listItem.type === GROUP_TYPE && listItem.relationship) {
          itemContents += `<span class="search-bar__dropdown-menu-relationship"> ${escapeHtml(
            listItem.relationship,
          )} </span>`;
        }

        if (listItem.explanation) {
          itemContents += `<span class="search-bar__dropdown-menu-explanation"> ${listItem.explanation} </span>`;
        }

        return itemContents;
      },

      listFilter: (list, currentInput) => {
        currentInput = (currentInput || '').trim();

        let typeFilter = FACET_TYPE;
        const inputLower = currentInput.toLowerCase();
        if (inputLower.indexOf('tag:') === 0) {
          typeFilter = TAG_TYPE;
        } else if (inputLower.indexOf('group:') === 0) {
          typeFilter = GROUP_TYPE;
        }

        let inputFilter = normalizeStr(currentInput);

        if (typeFilter === TAG_TYPE || typeFilter === GROUP_TYPE) {
          inputFilter = inputFilter.substr(inputFilter.indexOf(':') + 1);

          // remove the initial quote for comparisons if it exists
          if (inputFilter[0] === "'" || inputFilter[0] === '"') {
            inputFilter = inputFilter.substr(1);
          }
        }

        if (this.state.suggestionsType !== typeFilter) {
          this.setState({
            suggestionsType: typeFilter,
          });
        }

        return list
          .filter(item => {
            return (
              item.type === typeFilter &&
              item.matchOn.toLowerCase().indexOf(inputFilter.toLowerCase()) >= 0
            );
          })
          .sort((a, b) => {
            // this sort functions intention is to
            // sort partial matches as lower index match
            // value first. Then let natural sort of the
            // original list take effect if they have equal
            // index values or there is no current input value

            if (inputFilter) {
              const aIndex = a.matchOn.indexOf(inputFilter);
              const bIndex = b.matchOn.indexOf(inputFilter);

              // match score
              if (aIndex > bIndex) {
                return 1;
              } else if (aIndex < bIndex) {
                return -1;
              }
            }

            // If we are filtering on tags, we need to arrange
            // by popularity
            if (typeFilter === TAG_TYPE) {
              if (a.usageCount > b.usageCount) {
                return -1;
              } else if (a.usageCount < b.usageCount) {
                return 1;
              }
            }

            return 0;
          })
          .slice(0, MAX_SUGGESTIONS);
      },

      onSelect: itemSelected => {
        if (
          itemSelected.type === TAG_TYPE ||
          itemSelected.type === GROUP_TYPE
        ) {
          const prefix = itemSelected.type === TAG_TYPE ? 'tag:' : 'group:';

          let valSelection = itemSelected.title;

          // wrap multi word phrases with quotes to keep
          // autosuggestions consistent with what user needs to do
          if (valSelection.indexOf(' ') > -1) {
            valSelection = `"${valSelection}"`;
          }

          addLozenge(prefix + valSelection);

          this._input.value = '';
        } else {
          this._input.value = itemSelected.title;
          setTimeout(() => {
            this._input.focus();
          }, 0);
        }
        updateHiddenInput();
      },
    });

    this._input.addEventListener('keydown', onInputKeyDown);
    this._input.addEventListener('input', updateHiddenInput);
    lozengifyInput();
  }

  update(newState, prevState) {
    if (!this._suggestionsHandler) {
      return;
    }

    if (newState.suggestionsType !== prevState.suggestionsType) {
      if (newState.suggestionsType === TAG_TYPE) {
        this._suggestionsHandler.setHeader('Popular tags:');
      } else if (newState.suggestionsType === GROUP_TYPE) {
        this._suggestionsHandler.setHeader('Your groups:');
      } else {
        this._suggestionsHandler.setHeader('Narrow your search:');
      }
    }
  }
}
