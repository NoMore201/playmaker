from googleplay_api.googleplay import GooglePlayAPI, LoginError
from flask import Flask, render_template
import json
import configparser
import urllib.request
from urllib.error import URLError

# parse config file
config = configparser.ConfigParser()
config.read('config.ini')


def get_token():
    print('Retrieving token from %s' % config['Main']['tokenurl'])
    r = urllib.request.urlopen(config['Main']['tokenurl'])
    token = r.read().decode('utf-8')
    config['Main']['token'] = token
    with open('config.ini', 'w') as cfgfile:
        config.write(cfgfile)
    return token


# application setup
app = Flask(__name__)
service = GooglePlayAPI(config['Main']['id'], "en_US", True)
try:
    if config['Main']['token'] == '':
        try:
            token = get_token()
        except URLError:
            print('Failed to fetch url')
            print('Try using credentials')
            quit()
        service.login(None, None, token)
    else:
        service.login(None, None, config['Main']['token'])
except LoginError:
    print("Unable to login")
    quit()


@app.route('/')
def render_home():
    return render_template('index.html')


@app.route('/search')
def render_search():
    return render_template('search.html')


@app.route('/config')
def render_config():
    return render_template('config.html')


@app.route('/gplay/search', methods=['POST'])
def search_app():
    all_apps = []
    test = service.search('telegram', 6, None).doc
    if len(test) > 0:
        test = test[0].child
    else:
        return "[]"
    for result in test:
        if result.offer[0].checkoutFlowRequired:
            continue
        app = {'title': result.title,
               'developer': result.creator,
               'version': result.details.appDetails.versionCode,
               'numDownloads': result.details.appDetails.numDownloads,
               'uploadDate': result.details.appDetails.uploadDate,
               'stars': '%.2f' % result.aggregateRating.starRating}
        all_apps.append(app)
    return json.dumps(all_apps)


if __name__ == '__main__':
    app.run()
