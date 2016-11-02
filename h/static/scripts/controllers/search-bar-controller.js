'use strict';

var Controller = require('../base/controller');
var LozengeController = require('./lozenge-controller');
var AutosuggestDropdownController = require('./autosuggest-dropdown-controller');
var SearchTextParser = require('../util/search-text-parser');

/**
 * Controller for the search bar.
 */
class SearchBarController extends Controller {
  constructor(element) {
    super(element);

    this._input = this.refs.searchBarInput;
    this._lozengeContainer = this.refs.searchBarLozenges;

    let explanationList = [
      {
        title: 'user:',
        explanation: 'search by username',
      },
      {
        title: 'tag:',
        explanation: 'search for annotations with a tag',
      },
      {
        title: 'url:',
        explanation: 'see all annotations on a page',
      },
      {
        title: 'group:',
        explanation: 'show annotations created in a group you are a member of',
      },
    ];

    var selectFacet = facet => {
      this._input.value = facet;

      setTimeout(()=>{
        this._input.focus();
      }, 0);
    };


    var getTrimmedInputValue = () => {
      return this._input.value.trim();
    };

    new AutosuggestDropdownController( this._input, {

      list: explanationList,

      header: 'Narrow your search',

      classNames: {
        container: 'search-bar__dropdown-menu-container',
        header: 'search-bar__dropdown-menu-header',
        list: 'search-bar__dropdown-menu',
        item: 'search-bar__dropdown-menu-item',
        activeItem: 'js-search-bar-dropdown-menu-item--active',
      },

      renderListItem: (listItem)=>{

        let itemContents = `<span class="search-bar__dropdown-menu-title"> ${listItem.title} </span>`;

        if (listItem.explanation){
          itemContents += `<span class="search-bar__dropdown-menu-explanation"> ${listItem.explanation} </span>`;
        }

        return itemContents;
      },

      listFilter: function(list, currentInput){

        currentInput = (currentInput || '').trim();

        return list.filter((item)=>{

          if (!currentInput){
            return item;
          } else if (currentInput.indexOf(':') > -1) {
            return false;
          }
          return item.title.toLowerCase().indexOf(currentInput) >= 0;

        }).sort((a,b)=>{

          // this sort functions intention is to
          // sort partial matches as lower index match
          // value first. Then let natural sort of the
          // original list take effect if they have equal
          // index values or there is no current input value

          if (!currentInput){
            return 0;
          }

          let aIndex = a.title.indexOf(currentInput);
          let bIndex = b.title.indexOf(currentInput);

          if (aIndex > bIndex){
            return 1;
          } else if (aIndex < bIndex){
            return -1;
          }
          return 0;
        });
      },

      onSelect: (itemSelected)=>{
        selectFacet(itemSelected.title);
      },

    });


    /**
     * Insert a hidden <input> into the search <form>.
     *
     * The value of the hidden <input> is a search string constructed from
     * the lozenges plus any text currently in the visible <input>.
     *
     * The name="q" attribute is moved from the visible <input> on to the
     * hidden <input> so that when the <form> is submitted it's the value of
     * the _hidden_ input, not the visible one, that is submitted as the
     * q parameter.
     *
     */
    var insertHiddenInput = () => {
      var hiddenInput = document.createElement('input');
      hiddenInput.type = 'hidden';

      Array.from(this._lozengeContainer.querySelectorAll('.js-lozenge__content')).forEach((loz) => {
        hiddenInput.value = hiddenInput.value + loz.textContent + ' ';
      });
      hiddenInput.value = hiddenInput.value + getTrimmedInputValue();

      // When JavaScript isn't enabled this._input is submitted to the server
      // as the q param. With JavaScript we submit hiddenInput instead.
      hiddenInput.name = this._input.name;
      this._input.removeAttribute('name');

      this.refs.searchBarForm.appendChild(hiddenInput);
    };

    /**
     * Submit the user's search query to the server.
     *
     * We build a search query out of the lozenges plus any text in
     * this._input. To avoid a potential flash of text if we were to update
     * this._input with the search terms from the lozenge before submitting it,
     * we update a hidden input and submit that instead.
     */
    var submitForm = () => {
      insertHiddenInput();
      this.refs.searchBarForm.submit();
    };

    /**
     * Creates a lozenge and sets the content string to the
     * content provided and executes the delete callback when
     * the lozenge is deleted.
     *
     * @param {string} content The search term
     */
    var addLozenge = content => {
      var deleteCallback = () => {
        Array.from(this._lozengeContainer.querySelectorAll('.js-lozenge')).forEach(function(loz) {
          loz.classList.add('is-disabled');
        });
        submitForm();
      };

      new LozengeController(
        this._lozengeContainer,
        {
          content: content,
          deleteCallback: deleteCallback,
        }
      );
    };

    /**
     * Create lozenges for the search query terms already in the input field on
     * page load.
     */
    var lozengifyInput = () => {
      var {lozengeValues, incompleteInputValue} = SearchTextParser.getLozengeValues(this._input.value);
      lozengeValues.forEach(addLozenge);
      this._input.value = incompleteInputValue;
      this._input.style.visibility = 'visible';
    };

    /**
     * Setup listener keys with the handlers provided for each
     * of them.
     *
     * @param {Event} The event.
     * @param {Object} The function to execute when
     * the event fires for each listener key.
     */
    var setupListenerKeys = (event, handlers) => {
      var handler = handlers[event.keyCode];
      if (handler) {
        handler(event);
      }
    };

    /**
     * Setup the space key as the  listener for
     * creating a lozenge.
     *
     * @param {Event} The event to listen for.
     */
    var setupLozengeListenerKeys = event => {
      const SPACE_KEY_CODE = 32;
      const ENTER_KEY_CODE = 13;

      var handleSpaceKey = () => {
        var word = getTrimmedInputValue();
        if (SearchTextParser.shouldLozengify(word)) {
          addLozenge(word);
          // Clear the input after the lozenge is created and
          // appended to the container element.
          event.preventDefault();
          this._input.value = '';
        }
      };

      var handleEnterKey = (event) => {
        submitForm();
        event.preventDefault();
      };

      var handlers = {};
      handlers[SPACE_KEY_CODE] = handleSpaceKey;
      handlers[ENTER_KEY_CODE] = handleEnterKey;

      setupListenerKeys(event, handlers);
    };

    this._input.addEventListener('keydown', setupLozengeListenerKeys);

    lozengifyInput();
  }
}

module.exports = SearchBarController;
