# this script runs every two seconds and displays information on a webpage about the current song/ad

import requests
import urllib.parse
import time
import os
import comtypes

from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, redirect, request, jsonify, session, render_template, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/me/player/currently-playing'


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # login to spotify account
    print('LOGGIN IN')
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': 'user-read-private user-read-email user-read-currently-playing',
        'redirect_uri': REDIRECT_URI
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # callback after login redirect url
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args: 
        # send post request to get token info for session
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect(url_for('get_currently_playing'))
    

@app.route('/currently-playing')
def get_currently_playing():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))
    
    return render_template('currently_playing.html')

@app.route('/currently-playing-data')
def currently_playing_data():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))
    
    # fetches data from spotify api
    print('GETTING CURRENTLY PLAYING DATA')
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    try: 
        response = requests.get(API_BASE_URL, headers=headers)
        currently_playing = response.json()
        cur_type = currently_playing['currently_playing_type']

        # adjust volume based on what's being played
        if cur_type == 'track':
            volume('track')
        if cur_type == 'ad':
            volume('ad')

        return jsonify(currently_playing)
    except Exception as e: 
        return jsonify({'error': str(e)}), 500


@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        redirect(url_for('login'))

    if datetime.now().timestamp() > session['expires_at']:
        print('GETTING REFRESH TOKEN')
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect(url_for('get_currently_playing'))
    
def volume(action):
    comtypes.CoInitialize()
    sessions = AudioUtilities.GetAllSessions()

    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)

        if action == 'ad':
            if session.Process and session.Process.name() == "Spotify.exe":
                volume.SetMute(1, None)    
        if action == 'track':
            if session.Process and session.Process.name() == "Spotify.exe":
                volume.SetMute(0, None)    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug = True)
