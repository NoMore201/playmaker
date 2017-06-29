NPM=/usr/bin/env npm
DIR=node_modules
PACKAGES=backbone font-awesome
JS_FILES=$(DIR)/backbone/backbone-min.js \
		 $(DIR)/jquery/dist/jquery.min.js \
		 $(DIR)/underscore/underscore-min.js \
		 $(DIR)/bootstrap/dist/js/bootstrap.min.js \
CSS_FILES=$(DIR)/font-awesome/css/font-awesome.min.css \
		  $(DIR)/bootstrap/dist/css/bootstrap.min.css
FONTS=$(DIR)/font-awesome/fonts/*
DEST_JS=static/js
DEST_CSS=static/css
DEST_FONTS=static/fonts


install: dependencies
	install -D -m 644  $(JS_FILES) -t $(DEST_JS)
	install -D -m 644 $(CSS_FILES) -t $(DEST_CSS)
	install -D -m 644 $(FONTS) -t $(DEST_FONTS)

dependencies:
	$(NPM) install $(PACKAGES)

clean:
	rm -rf $(DIR)

.PHONY : dependencies install
