default: clean data.js

annotator.json: annotator.po
	po2json annotator.po annotator.json

data.js: annotator.json
	echo "var annotator_locale_data = " > data.js
	cat annotator.json >> data.js
	rm -f annotator.json

clean:
	rm -f *.js*
