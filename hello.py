from dropbox.client import DropboxOAuth2Flow, DropboxClient
from secrets import *
from flask import Flask, render_template, session, redirect, abort, url_for, request
from os.path import basename
import json
app = Flask(__name__)

def get_dropbox_auth_flow(web_app_session):
    return DropboxOAuth2Flow(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_APP_REDIRECT,
                             web_app_session, "dropbox-auth-csrf-token")

def dropbox_auth_start(web_app_session):
    authorize_url = get_dropbox_auth_flow(web_app_session).start()
    return redirect(authorize_url)

# URL handler for root
@app.route('/')
def start():
    return dropbox_auth_start(session)

# URL handler for /dropbox-auth-finish
@app.route('/dropbox-auth-finish')
def dropbox_auth_finish():
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        access_token, user_id, url_state = \
                get_dropbox_auth_flow(session).finish({'code':code, 'state':state})
    except DropboxOAuth2Flow.BadRequestException, e:
        abort(400)
    except DropboxOAuth2Flow.BadStateException, e:
        # Start the auth flow again.
        return redirect("/dropbox-auth-start")
    except DropboxOAuth2Flow.CsrfException, e:
        print 'csrf exception'
        abort(403)
    except DropboxOAuth2Flow.NotApprovedException, e:
        return redirect("/")
    except DropboxOAuth2Flow.ProviderException, e:
        print 'provider exception'
        abort(403)

    session['access_token'] = access_token

    return redirect(url_for('success'))

@app.route('/success')
def success():
    client = DropboxClient(session['access_token'])
    data = walk(client, client.metadata('/'))
    return render_template('display.html', json_data=data)


def walk(client, metadata):
    dir_path = basename(metadata['path'])
    result = {'name':basename(dir_path), 'children':[]}
    for dir_entry in metadata['contents']:
        path = dir_entry['path']
        bytes = dir_entry['bytes']
        if bytes is 0:
            result['children'].append(walk(client, client.metadata(path)))
        else:
            child = {'name':basename(path), 'value':bytes}
            result['children'].append(child)
    #empty directories? do we care?
    if len(result['children']) is 0:
        _ = result.pop('children', None)
    return result

@app.route('/display')
def display():
    # Load the flare.json file and pass it into the template.
    json_data = ""
    with open('dropbox.json', 'r') as f:
        json_data = json.load(f)
    return render_template('display.html', json_data=json_data)

if __name__ == '__main__':
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.debug = True
    app.run()
