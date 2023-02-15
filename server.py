"""Python Flask WebApp Auth0 integration example
"""

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import *
import psycopg2
import os


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


@app.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/api/results")
def results():
    # Connect to the database and retrieve the survey results
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cur = conn.cursor()

    order = "ASC" if request.args.get("reverse") != "true" else "DESC"
    cur.execute(f"SELECT * FROM survey_responses ORDER BY id {order}")
    results = cur.fetchall()

    # Convert the results to a list of dictionaries
    results_list = [
        {
            "id": r[0],
            "customer": r[1],
            "breeder": r[2],
            "rating": r[3],
            "recommend": r[4],
            "comments": r[5],
        }
        for r in results
    ]

    # Close the database connection
    cur.close()
    conn.close()

    # Return the results as JSON
    return jsonify(results_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
