from dropbox.client import DropboxOAuth2Flow, DropboxClient
from dropbox.rest import ErrorResponse
from secrets import *
from flask import Flask, render_template, session, redirect, abort, url_for, request, jsonify
from rq import Queue
from worker import conn
from util import human_readable, update_progress, walk, get_metadata, get_job_from_key

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

q = Queue(connection=conn, default_timeout=600)

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

    return redirect(url_for('display'))

@app.route('/display')
def display():
    if 'access_token' not in session:
        abort(400)

    if 'job' in session:
        job = get_job_from_key(session['job'], conn)
        # Only rely on a previous result if the same user is logged in (same access_token)
        if job is not None and session['access_token'] == job.meta['access_token']:
            return render_template('display.html', username=session['username'], quota=session['quota'], used=session['used'])

    try:
        client = DropboxClient(session['access_token'])
    except ErrorResponse, e:
        abort(401)

    account = client.account_info()
    session['username'] = account['display_name']
    quota = float(account['quota_info']['quota'])
    shared = float(account['quota_info']['shared'])
    normal = float(account['quota_info']['normal'])
    total_bytes = int(normal + shared)
    session['used'] = human_readable(normal + shared)
    session['quota'] = human_readable(quota)

    job = q.enqueue(walk, client, get_metadata(client, '/'), 0, total_bytes)
    job.meta['access_token'] = session['access_token'];
    job.save()
    update_progress(job, 0, "/")
    session['job'] = job.key

    return render_template('display.html', username=session['username'], quota=session['quota'], used=session['used'])

@app.route('/display_result')
def display_result():
    if 'job' not in session:
        return jsonify(ready=False, progress=0)

    job = get_job_from_key(session['job'], conn)
    if job is None:
        abort(400)

    if job.result is None:
        return jsonify(ready=False, current=job.meta['current'], progress=job.meta['progress'])

    data, bytes_read = job.result
    return jsonify(ready=True, result=data)


if __name__ == '__main__':
    app.debug = True
    app.run()
