import os
import random
from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://anayanil698_db_user:GXRPih0HppmF9v8x@cluster0.hkypwcl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'randomkey')
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

client = MongoClient(MONGODB_URI)
db = client['guessthenumber']
history_coll = db.history

ROOM = 'main'
players = {}
secret_number = random.randint(1, 100)

def broadcast_players():
    emit('player_list', list(players.values()), room=ROOM)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_player')
def join_player(data):
    username = data.get('username', f'Player{random.randint(1000,9999)}')
    players[request.sid] = username
    join_room(ROOM)
    emit('game_message', {'msg': f"{username} joined the game!"}, room=ROOM)
    broadcast_players()
    emit('game_message', {'msg': "Welcome! Guess a number 1-100."})

@socketio.on('make_guess')
def make_guess(data):
    global secret_number
    username = players.get(request.sid, f'Player{random.randint(1000,9999)}')
    try:
        guess = int(data.get('guess', -1))
    except:
        return
    ts = datetime.now()
    if guess == secret_number:
        result = f"{username} guessed {guess}: 🎉 Correct! Number was {secret_number}. New round started!"
        secret_number = random.randint(1, 100)
    elif guess < secret_number:
        result = f"{username} guessed {guess}: Too low!"
    else:
        result = f"{username} guessed {guess}: Too high!"
    emit('game_message', {'msg': result}, room=ROOM)
    history_coll.insert_one({'user': username, 'guess': guess, 'result': result, 'ts': ts})

@socketio.on('connect')
def handle_connect():
    join_room(ROOM)
    recent = list(history_coll.find().sort('ts', -1).limit(8))
    for h in reversed(recent):
        emit('game_message', {'msg': h['result'], 'ts': h['ts'].isoformat()})

@socketio.on('disconnect')
def handle_disconnect():
    username = players.pop(request.sid, None)
    if username:
        emit('game_message', {'msg': f"{username} left the game."}, room=ROOM)
        broadcast_players()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
