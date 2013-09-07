from dropbox.client import DropboxOAuth2Flow, DropboxClient
from secrets import *
from flask import Flask, render_template, session
app = Flask(__name__)

def get_dropbox_auth_flow(web_app_session):
    return DropboxOAuth2Flow(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_APP_REDIRECT,
                             web_app_session, "dropbox-auth-csrf-token")

def dropbox_auth_start(web_app_session, request):
    authorize_url = get_dropbox_auth_flow(web_app_session).start()
    redirect_to(authorize_url)

# URL handler for root
@app.route('/')
def start():
    dropbox_auth_start(session, None)

# URL handler for /dropbox-auth-finish
@app.route('/dropbox-auth-finish')
def dropbox_auth_finish(web_app_session, request):
    try:
        access_token, user_id, url_state = \
                get_dropbox_auth_flow(web_app_session).finish(request.query_params)
    except DropboxOAuth2Flow.BadRequestException, e:
        http_status(400)
    except DropboxOAuth2Flow.BadStateException, e:
        # Start the auth flow again.
        redirect_to("/dropbox-auth-start")
    except DropboxOAuth2Flow.CsrfException, e:
        http_status(403)
    except DropboxOAuth2Flow.NotApprovedException, e:
        flash('Not approved?  Why not, bro?')
        return redirect_to("/home")
    except DropboxOAuth2Flow.ProviderException, e:
        logger.log("Auth error: %s" % (e,))
        http_status(403)

    redirect_to('/success')

@app.route('/success')
def success():
    return "HOLY SHIT"


if __name__ == '__main__':
    app.run(debug=True)
