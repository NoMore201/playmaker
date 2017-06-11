from ext_libs.googleplay_api.googleplay import GooglePlayAPI
from ext_libs.googleplay_api.googleplay import config
from flask import Flask, render_template
import json

# application setup
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
service = GooglePlayAPI("3d716411bf8bc802", "en_US", True)
service.login(None, None, config.AUTH_TOKEN)


@app.route('/')
def render_page():
    return render_template('index.html')


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
               'version': result.details.appDetails.versionCode}
        all_apps.append(app)
    return json.dumps(all_apps)


if __name__ == '__main__':
    app.run()
