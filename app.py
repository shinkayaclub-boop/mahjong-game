from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from game_logic import MahjongGame, Player
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret!')
# Render用: eventletを使用
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

games = {} 

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_game')
def on_join(data):
    room = 'default_room'
    username = data.get('username', 'Guest')
    
    join_room(room)
    
    # Initialize game if not exists
    if room not in games:
        games[room] = MahjongGame()
    
    game = games[room]
    
    # 1. Check if Reconnecting (Same name?)
    existing_player = next((p for p in game.players if p.name == username), None)
    
    if existing_player:
        # Update SID and rejoin
        print(f"Player {username} reconnecting. Updating SID from {existing_player.session_id} to {request.sid}")
        existing_player.session_id = request.sid
        # Send current state to Re-connector
        emit('game_state_update', game.get_public_state(), room=request.sid)
        # Also send private hand if game started
        if game.game_started:
             emit('hand_update', {
                 'hand': [t.to_dict() for t in existing_player.hand],
                 'drawn_tile': None,
                 'my_turn': (game.get_current_player().session_id == request.sid)
             }, room=request.sid)

    # 2. Add New Player if space
    elif len(game.players) < 4:
        player = Player(username, request.sid)
        game.add_player(player)
        emit('player_joined', {'username': username, 'current_players': len(game.players)}, room=room)
        
        # BROADCAST STATE IMMEDIATELY so users see the table
        broadcast_game_state(room, game)

@socketio.on('add_bots')
def on_add_bots(data):
    room = 'default_room'
    if room not in games: return
    game = games[room]
    
    current_count = len(game.players)
    needed = 4 - current_count
    
    if needed > 0:
        for i in range(1, needed + 1):
            bot_name = f"CPU-{current_count + i}"
            bot_sid = f"bot_sid_{current_count + i}"
            bot = Player(bot_name, bot_sid)
            game.add_player(bot)
            emit('player_joined', {'username': bot_name, 'current_players': len(game.players)}, room=room)
            
            # Broadcast state so they appear on table immediately (waiting)
            broadcast_game_state(room, game)

@socketio.on('start_manual_game')
def on_start_manual_game(data):
    print("Received start_manual_game request")
    room = 'default_room'
    if room not in games:
        print("ERROR: Room not found in games dict")
        emit('error_message', {'msg': 'Game session not found. Please reload.'})
        return
        
    game = games[room]
    print(f"Game found. Players: {len(game.players)}, Started: {game.game_started}")
    
    if len(game.players) == 4 and not game.game_started:
         print("Conditions met. Starting dealer selection...")
         results = game.start_dealer_selection()
         emit('dealer_selection_start', results, room=room)
         
         game.start_game()
         broadcast_game_state(room, game)
         
         # Check if Dealer (first turn) is a Bot
         dealer_p = game.players[game.dealer_index]
         if "bot_sid" in dealer_p.session_id:
             # Start background task WITHOUT blocking here
             socketio.start_background_task(delayed_bot_start, room, game, dealer_p.session_id)
    else:
        print("Conditions NOT met for start_dictionary.")

def delayed_bot_start(room, game, bot_sid):
    # Add delay before bot starts so users see who is dealer
    socketio.sleep(4.0) 
    bot_turn(room, game, bot_sid)

    # 3. Check for Dealer Selection Start (When 4 players are ready)
    if len(game.players) == 4:
        if not game.game_started:
             # START DEALER SELECTION PHASE
             results = game.start_dealer_selection()
             print(f"Dealer Selection: {results}")
             
             # Broadcast Dice Results to ALL
             emit('dealer_selection_start', results, room=room)
             
             # Small delay handled by frontend animation, then frontend asks for game start?
             # Or we just start game state and broadcast it, allowing frontend to animate first.
             # Let's start game state immediately but frontend will show dice overlay first.
             game.start_game()
             broadcast_game_state(room, game)
    else:
        # > 4 players or something else
        pass

@socketio.on('discard_tile')
def on_discard(data):
    room = 'default_room'
    if room not in games: return
    game = games[room]
    
    # Process Human Discard
    process_turn(room, game, request.sid, data.get('tile_index'))

def process_turn(room, game, session_id, tile_index):
    result = game.player_discard(session_id, tile_index)
    if result:
        broadcast_game_state(room, game)
        
        next_sid = result['next_player_sid']
        next_p = next(p for p in game.players if p.session_id == next_sid)

        # Notify next player
        if result['drawn_tile']:
             socketio.emit('hand_update', {
                 'hand': [t.to_dict() for t in next_p.hand],
                 'drawn_tile': result['drawn_tile'],
                 'my_turn': True
             }, room=next_sid)
        
        # CHECK IF NEXT IS BOT
        if "bot_sid" in next_sid:
             socketio.start_background_task(bot_turn, room, game, next_sid)

def bot_turn(room, game, bot_sid):
    # Simulate thinking time
    socketio.sleep(1.0)
    
    # Simple Tsumogiri: Discard the last drawn tile (index = len-1)
    # We need to find the bot player object again to be safe
    bot = next((p for p in game.players if p.session_id == bot_sid), None)
    if not bot: return

    # Discard the last tile added (drawn tile)
    discard_index = len(bot.hand) - 1
    
    process_turn(room, game, bot_sid, discard_index)

def broadcast_game_state(room, game):
    # Public info for everyone
    state = game.get_public_state()
    state['turn_player_index'] = game.turn_index
    state['turn_player_name'] = game.players[game.turn_index].name
    
    emit('game_state_update', state, room=room)
    
    # Private hand info for each player
    for i, p in enumerate(game.players):
        socketio.emit('hand_update', {
            'hand': [t.to_dict() for t in p.hand],
            'my_turn': (i == game.turn_index)
        }, room=p.session_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
