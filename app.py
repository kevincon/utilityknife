from dropbox import Dropbox
from dropbox import DropboxOAuth2Flow
from dropbox.oauth import NotApprovedException, ProviderException, CsrfException, BadStateException, BadRequestException
from flask import Flask, render_template, session, redirect, abort, url_for, request, jsonify
from rq import Queue
from secrets import *
from util import human_readable, update_progress, walk_entire_dropbox, get_job_from_key
from worker import conn

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

q = Queue(connection=conn, default_timeout=3600)

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
            raise NotApprovedException
        oauth_result = get_dropbox_auth_flow(session).finish(request.args)
    except BadRequestException:
        abort(400)
    except BadStateException:
        # Start the auth flow again.
        return redirect("/dropbox-auth-start")
    except CsrfException:
        print 'csrf exception'
        abort(403)
    except NotApprovedException:
        return redirect("/")
    except ProviderException:
        print 'provider exception'
        abort(403)

    session['access_token'] = oauth_result.access_token

    return redirect(url_for('display'))

def get_allocated_from_allocation(allocation):
    if allocation.is_individual():
        return allocation.get_individual().allocated
    elif allocation.is_team():
        return allocation.get_team().allocated
    else:
        raise Exception("Unknown allocation type: %s", allocation)

def get_space_usage_info(space_usage):
    allocation = space_usage.allocation
    allocated = get_allocated_from_allocation(allocation)
    return float(allocated), float(space_usage.used)

@app.route('/display')
def display():
    if 'access_token' not in session:
        abort(400)

    access_token = session['access_token']
    if 'job' in session:
        job = get_job_from_key(session['job'], conn)
        # Only rely on a previous result if the same user is logged in (same access_token)
        if job is not None and access_token == job.meta.get('access_token', None):
            return render_template('display.html', username=session['username'], quota=session['quota'], used=session['used'])

    try:
        client = Dropbox(access_token)
    except Exception:
        abort(401)

    account = client.users_get_current_account()
    session['username'] = account.name.display_name

    space_usage = client.users_get_space_usage()
    allocated, used = get_space_usage_info(space_usage)
    total_bytes = used
    session['used'] = human_readable(used)
    session['quota'] = human_readable(allocated)

    job = q.enqueue(walk_entire_dropbox, access_token, total_bytes)
    job.meta['access_token'] = access_token
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
    app.run()
