from flask import Flask, render_template, request, redirect, session, url_for
from textblob import TextBlob
import tweepy
import sqlite3
from datetime import datetime

# Flask app setup
app = Flask(__name__)
app.secret_key = 'bbaabbaabbaabbaa5566556677887788'

# Twitter API credentials
API_KEY = 'ym5pAXCbSPf3do9jVnucjoRG6'
API_SECRET_KEY = 'uuRxGhlL7KRnmhDMbHD7oIEpGe9yEgxXW9YvCN84EhcjapMv7d'
CALLBACK_URL = 'https://twritterhunteranalysis.vercel.app/auth/twitter/callback'

# Tweepy OAuth setup
auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY, CALLBACK_URL)

# Helper function for sentiment analysis
def analyze_sentiment(tweet):
    analysis = TextBlob(tweet)
    if analysis.sentiment.polarity > 0:
        return 'Positive'
    elif analysis.sentiment.polarity == 0:
        return 'Neutral'
    else:
        return 'Negative'

# Database setup function
def init_db():
    with sqlite3.connect('twitterhunter.db') as conn:
        cursor = conn.cursor()
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                username TEXT NOT NULL,
                date_time TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

# Routes
@app.route('/')
def landing():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    username = session.get('username', 'Guest')
    return render_template('index.html', username=username)

@app.route('/auth/twitter')
def twitter_auth():
    try:
        redirect_url = auth.get_authorization_url()
        session['request_token'] = auth.request_token
        return redirect(redirect_url)
    except tweepy.TweepError as e:
        return f"Error during authentication: {e}"

@app.route('/auth/twitter/callback')
def twitter_callback():
    token = request.args.get('oauth_token')
    verifier = request.args.get('oauth_verifier')

    if 'request_token' not in session or token != session['request_token']['oauth_token']:
        return 'Invalid token. Please try again.'

    try:
        auth.request_token = session.pop('request_token')
        auth.get_access_token(verifier)

        api = tweepy.API(auth)
        user = api.verify_credentials()

        if user:
            session['username'] = user.name
            return redirect(url_for('home'))
        else:
            return 'Failed to fetch user details from Twitter. Try again.'
    except tweepy.TweepError as e:
        return f"Error during callback: {e}"

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('index11'))

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'username' in session:
        tweet = request.form['tweet']
        sentiment = analyze_sentiment(tweet)
        date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = session['username']

        with sqlite3.connect('twitterhunter.db') as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                INSERT INTO history (tweet, sentiment, username, date_time)
                VALUES (?, ?, ?, ?)
            ''', (tweet, sentiment, username, date_time))
            conn.commit()

        return render_template('index11.html', username=username, tweet=tweet, sentiment=sentiment)
    return redirect(url_for('index'))

@app.route('/history', methods=['GET', 'POST'])
def history():
    search_query = request.form.get('search', '') if request.method == 'POST' else ''
    with sqlite3.connect('twitterhunter.db') as conn:
        cursor = conn.cursor()
        if search_query:
            cursor.execute('''
                SELECT tweet, sentiment, username, date_time 
                FROM history 
                WHERE tweet LIKE ? OR sentiment LIKE ? OR username LIKE ?
                ORDER BY date_time DESC
            ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        else:
            cursor.execute('''
                SELECT tweet, sentiment, username, date_time 
                FROM history 
                ORDER BY date_time DESC
            ''')
        results = cursor.fetchall()
    return render_template('history.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
