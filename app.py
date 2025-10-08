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
active_players = {} 
secret_number = random.randint(1, 100)
game_stats = {'total_guesses': 0, 'current_round': 1}

def broadcast_players():
    player_list = [p['username'] for p in active_players.values()]
    emit('player_list', {
        'players': player_list, 
        'count': len(player_list),
        'round': game_stats['current_round']
    }, room=ROOM)

def broadcast_game_state():
    emit('game_state', {
        'total_players': len(active_players),
        'total_guesses': game_stats['total_guesses'],
        'current_round': game_stats['current_round']
    }, room=ROOM)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_player')
def join_player(data):
    username = data.get('username', f'Player{random.randint(1000,9999)}')

    existing_usernames = [p['username'] for p in active_players.values()]
    if username in existing_usernames:
        username = f"{username}_{random.randint(100,999)}"
    
    active_players[request.sid] = {
        'username': username,
        'joined_at': datetime.now()
    }
    
    join_room(ROOM)
    emit('game_message', {'msg': f"🎮 {username} joined the game!"}, room=ROOM)
    emit('game_message', {'msg': f"Welcome {username}! Guess a number between 1-100. Current round: {game_stats['current_round']}"})
    
    broadcast_players()
    broadcast_game_state()

@socketio.on('make_guess')
def make_guess(data):
    global secret_number
    
    if request.sid not in active_players:
        emit('game_message', {'msg': "❌ Please join the game first!"})
        return
        
    username = active_players[request.sid]['username']
    
    try:
        guess = int(data.get('guess', -1))
        if guess < 1 or guess > 100:
            emit('game_message', {'msg': "❌ Please guess a number between 1 and 100!"})
            return
    except (ValueError, TypeError):
        emit('game_message', {'msg': "❌ Please enter a valid number!"})
        return
    
    ts = datetime.now()
    game_stats['total_guesses'] += 1
    
    if guess == secret_number:
        result = f"🎉 {username} guessed {guess} - CORRECT! The number was {secret_number}!"
        winner_msg = f"🏆 {username} wins Round {game_stats['current_round']}! Starting new round..."
        
       
        game_stats['current_round'] += 1
        secret_number = random.randint(1, 100)
        
        emit('game_message', {'msg': result}, room=ROOM)
        emit('game_message', {'msg': winner_msg}, room=ROOM)
        emit('game_message', {'msg': f"🎲 New round {game_stats['current_round']} started! Guess the new number (1-100)"}, room=ROOM)
        
    elif guess < secret_number:
        result = f"📉 {username} guessed {guess} - Too low!"
        emit('game_message', {'msg': result}, room=ROOM)
    else:
        result = f"📈 {username} guessed {guess} - Too high!"
        emit('game_message', {'msg': result}, room=ROOM)
    
  
    history_coll.insert_one({
        'user': username, 
        'guess': guess, 
        'result': result, 
        'ts': ts,
        'round': game_stats['current_round']
    })
    
    broadcast_game_state()

@socketio.on('connect')
def handle_connect():
    join_room(ROOM)
    print(f'Client connected: {request.sid}')
    
   
    recent = list(history_coll.find().sort('ts', -1).limit(10))
    for h in reversed(recent):
        emit('game_message', {
            'msg': h['result'], 
            'ts': h['ts'].isoformat() if isinstance(h.get('ts'), datetime) else str(h.get('ts'))
        })
    
    emit('game_message', {'msg': f"🎮 Connected! Current round: {game_stats['current_round']}. Join the game to start playing!"})

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in active_players:
        username = active_players[request.sid]['username']
        del active_players[request.sid]
        emit('game_message', {'msg': f"👋 {username} left the game"}, room=ROOM)
        broadcast_players()
        broadcast_game_state()
    print(f'Client disconnected: {request.sid}')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
