from dropbox.client import DropboxOAuth2Flow, DropboxClient
from secrets import *
from flask import Flask, render_template, session, redirect, abort, url_for, request
from os.path import basename
import json
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

def get_dropbox_auth_flow(web_app_session):
    return DropboxOAuth2Flow(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_APP_REDIRECT,
                             web_app_session, "dropbox-auth-csrf-token")

def dropbox_auth_start(web_app_session):
    authorize_url = get_dropbox_auth_flow(web_app_session).start()
    return redirect(authorize_url)

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/start')
def start():
    return dropbox_auth_start(session)

@app.route('/dropbox-auth-finish')
def dropbox_auth_finish():
    try:
        error = request.args.get('error')
        if error is not None:
            raise DropboxOAuth2Flow.NotApprovedException()

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
    account = client.account_info()
    username = account['display_name']
    quota = float(account['quota_info']['quota'])
    shared = float(account['quota_info']['shared'])
    normal = float(account['quota_info']['normal'])
    used = human_readable(normal + shared)
    quota = human_readable(quota)
    return render_template('display.html', json_data=data, username=username, quota=quota, used=used)

def human_readable(bytes):
    if bytes < 1024:
        return "%.0f Bytes" % bytes;
    elif bytes < 1048576:
        return "%.2f KB" % (bytes / 1024)
    elif bytes < 1073741824:
        return "%.2f MB" % (bytes / 1048576)
    else:
        return "%.2f GB" % (bytes / 1073741824)

def walk(client, metadata):
    dir_path = basename(metadata['path'])
    bytes = metadata['bytes']
    result = {'name':basename(dir_path), 'children':[], 'value':bytes}
    for dir_entry in metadata['contents']:
        path = dir_entry['path']
        dir_entry_bytes = dir_entry['bytes']
        if dir_entry_bytes is 0:
            result['children'].append(walk(client, client.metadata(path)))
        else:
            child = {'name':basename(path), 'value':dir_entry_bytes}
            result['children'].append(child)
    #empty directories? do we care?
    if len(result['children']) is 0:
        _ = result.pop('children', None)
    return result

if __name__ == '__main__':
    app.run()
