# Icon Fonts

The icon fonts for H were created with [icomoon](https://icomoon.io/app). The source file which contains the SVG definitions of the icons is `fonts/selection.json`.

The icons used are from the _Icomoon Free_ and [_Material Icons_](https://www.google.com/design/icons/) libraries which are both pre-installed in the icomoon app.

## Adding New Icons

To add new icons, you'll need to load `selection.json` into the icomoon app,
add the relevant icons and then use the app's _Generate Font_ facility.

 1. Go to the [icomoon app](https://icomoon.io/app) and import `selection.json`
    as a new project.
 2. Search for icons or import the ones you want to add from another source and
    add them to the 'h' set.
 3. Select the _Download JSON_ option for the 'h' set to download an updated `selection.json`
    file.
 4. Look for the new entry in the "selection" section at the bottom of the file.
    The new entry will be the one without a name. Add a "name" attribute to this item.
    The name attribute will be used in the CSS class name for the icon (eg. `h-icon-twitter`)
 5. Re-import the JSON file into icomoon
 6. Ensure all icons in the 'h' set are selected, then go to the 'Generate Font' tab in icomoon
    and click the 'Download' button which appears _within_ the tab.
 7. From the downloaded archive:
  * Extract `fonts/h.woff` -> `./fonts/h.woff`
  * Extract `style.css` -> `./icomoon.css`.
  * Edit `icomoon.css` to keep only the _WOFF_ format font as that is [supported](http://caniuse.com/#feat=woff) by our target browsers (IE >= 10).
 8. Commit the updated `selection.json`, `fonts/h.eot` and `icomoon.css` files to the repository.
