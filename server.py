from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state
games = {}  # {room_code: {players: {player_name: chits}, current_player, game_state, scores: {player_name: total_score}, chit_pool: [...] ...}}

def initialize_game(room_code, starting_player):
    # Initialize the chit pool for the room: exactly 4 of each fruit
    chit_pool = ['🍎', '🍌', '🍊', '🥝'] * 4  # 4 chits of each fruit, total 16 chits
    random.shuffle(chit_pool)

    # Assign 4 chits to the starting player from the chit pool
    player_chits = chit_pool[:4]
    chit_pool = chit_pool[4:]  # Remove assigned chits from the pool

    players = {starting_player: player_chits}
    games[room_code] = {
        'players': players,
        'current_player': None,  # Will be set when game starts with 4 players
        'game_state': 'waiting',  # Start in waiting state
        'victory_player': None,
        'reaction_times': {},
        'reaction_start_time': None,
        'player_ids': {request.sid: starting_player},
        'scores': games[room_code]['scores'] if room_code in games else {starting_player: 0},
        'round_number': games[room_code]['round_number'] if room_code in games else 1,
        'chit_pool': chit_pool  # Store remaining chits in the pool
    }
    print(f"Initialized game for room {room_code} with player {starting_player}, chits: {player_chits}, remaining pool: {chit_pool}")

def assign_initial_chits(room_code):
    # Assign 4 chits to a new player from the room's chit pool
    if len(games[room_code]['chit_pool']) < 4:
        return []  # Shouldn't happen with proper player limit, but safety check
    player_chits = games[room_code]['chit_pool'][:4]
    games[room_code]['chit_pool'] = games[room_code]['chit_pool'][4:]  # Remove assigned chits
    return player_chits

def start_game_if_full(room_code):
    if len(games[room_code]['players']) == 4:
        games[room_code]['game_state'] = 'playing'
        # Set the first current_player (e.g., first player who joined)
        games[room_code]['current_player'] = list(games[room_code]['players'].keys())[0]
        print(f"Game started in room {room_code} with 4 players: {list(games[room_code]['players'].keys())}")
        emit('update_game', games[room_code], room=room_code)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def create_room(data):
    player_name = data.get('player_name')
    room_code = data.get('room_code')
    if not player_name or not room_code or not (room_code.isdigit() and len(room_code) == 4):
        emit('room_error', {'message': 'Player name and a 4-digit room number are required!'})
        return
    if room_code in games:
        emit('room_error', {'message': 'Room already exists!'})
        return
    initialize_game(room_code, player_name)
    join_room(room_code)
    print(f"Created room: {room_code} with player {player_name}")
    emit('room_joined', {
        'room_code': room_code,
        'player_name': player_name,
        'current_player': None,
        'players': games[room_code]['players'],
        'game_state': games[room_code]['game_state']
    }, room=request.sid)
    start_game_if_full(room_code)

@socketio.on('join_room')
def join_room_handler(data):
    player_name = data.get('player_name')
    room_code = data.get('room_code')
    if not player_name or not room_code or not (room_code.isdigit() and len(room_code) == 4):
        emit('room_error', {'message': 'Player name and a 4-digit room number are required!'})
        return
    print(f"Attempting to join room: {room_code}")
    print(f"Current rooms: {list(games.keys())}")
    if room_code not in games:
        emit('room_error', {'message': 'Room not found!'})
        return
    if len(games[room_code]['players']) >= 4:
        emit('room_error', {'message': 'Room is full!'})
        return
    if player_name in games[room_code]['players']:
        emit('room_error', {'message': 'Player name already in use!'})
        return
    join_room(room_code)
    games[room_code]['players'][player_name] = assign_initial_chits(room_code)
    games[room_code]['player_ids'][request.sid] = player_name
    if player_name not in games[room_code]['scores']:
        games[room_code]['scores'][player_name] = 0
    print(f"Player {player_name} joined room {room_code} with chits: {games[room_code]['players'][player_name]}, remaining pool: {games[room_code]['chit_pool']}")
    emit('room_joined', {
        'room_code': room_code,
        'player_name': player_name,
        'current_player': games[room_code]['current_player'],
        'players': games[room_code]['players'],
        'game_state': games[room_code]['game_state']
    }, room=request.sid)
    emit('update_game', games[room_code], room=room_code)
    start_game_if_full(room_code)

@socketio.on('select_chit')
def select_chit(data):
    room_code = data['room_code']
    player_name = data['player_name']
    chit = data['chit']
    print(f"Player {player_name} in room {room_code} selected chit: {chit}")
    if room_code in games and games[room_code]['game_state'] == 'playing' and games[room_code]['current_player'] == player_name:
        players = list(games[room_code]['players'].keys())
        current_idx = players.index(player_name)
        next_idx = (current_idx + 1) % len(players)
        next_player = players[next_idx]
        if chit in games[room_code]['players'][player_name]:
            games[room_code]['players'][player_name].remove(chit)
            games[room_code]['players'][next_player].append(chit)
            games[room_code]['current_player'] = next_player
            print(f"Chit {chit} passed from {player_name} to {next_player}")
            print(f"New game state: {games[room_code]}")
            emit('update_game', games[room_code], room=room_code)

@socketio.on('declare_victory')
def declare_victory(data):
    room_code = data['room_code']
    player_name = data['player_name']
    print(f"Player {player_name} in room {room_code} declared victory")
    if room_code in games and games[room_code]['game_state'] == 'playing' and games[room_code]['current_player'] == player_name:
        player_chits = games[room_code]['players'][player_name]
        counts = {}
        for chit in player_chits:
            counts[chit] = counts.get(chit, 0) + 1
        if any(count >= 4 for count in counts.values()):
            games[room_code]['game_state'] = 'reaction'
            games[room_code]['victory_player'] = player_name
            games[room_code]['reaction_times'] = {}
            games[room_code]['reaction_start_time'] = int(time.time() * 1000)
            emit('update_game', games[room_code], room=room_code)

@socketio.on('stack_hand')
def stack_hand(data):
    room_code = data['room_code']
    player_name = data['player_name']
    reaction_time = data['reaction_time']
    print(f"Player {player_name} in room {room_code} stacked hand")
    if room_code in games and games[room_code]['game_state'] == 'reaction' and player_name != games[room_code]['victory_player']:
        elapsed_time = reaction_time - games[room_code]['reaction_start_time']
        games[room_code]['reaction_times'][player_name] = elapsed_time

        # Check if all non-winner players have reacted
        players = list(games[room_code]['players'].keys())
        non_winner_players = [p for p in players if p != games[room_code]['victory_player']]
        if len(games[room_code]['reaction_times']) == len(non_winner_players):
            # Calculate scores based on reaction times
            reaction_rankings = sorted(
                games[room_code]['reaction_times'].items(),
                key=lambda x: x[1]
            )
            slowest_player = reaction_rankings[-1][0] if reaction_rankings else None

            # Assign points
            winner = games[room_code]['victory_player']
            games[room_code]['scores'][winner] += 3
            if len(reaction_rankings) >= 1:
                games[room_code]['scores'][reaction_rankings[0][0]] += 2
            if len(reaction_rankings) >= 2:
                games[room_code]['scores'][reaction_rankings[1][0]] += 1
            if len(reaction_rankings) >= 3:
                games[room_code]['scores'][reaction_rankings[2][0]] += 0

            emit('game_over', {
                'winner': winner,
                'slowest_player': slowest_player,
                'scores': games[room_code]['scores'],
                'round_number': games[room_code]['round_number']
            }, room=room_code)

@socketio.on('restart_game')
def restart_game(data):
    room_code = data['room_code']
    print(f"Restarting game in room {room_code}")
    if room_code in games:
        # Determine the player with the lowest score to start the new game
        scores = games[room_code]['scores']
        lowest_scorer = min(scores, key=scores.get)
        print(f"Lowest scorer: {lowest_scorer} with score {scores[lowest_scorer]}")

        # Preserve scores and player IDs
        current_scores = games[room_code]['scores']
        current_player_ids = games[room_code]['player_ids']
        
        # Reinitialize the game with the lowest scorer starting
        initialize_game(room_code, lowest_scorer)
        
        # Restore scores, player IDs, and increment round number
        games[room_code]['scores'] = current_scores
        games[room_code]['player_ids'] = current_player_ids
        games[room_code]['round_number'] += 1

        # Reassign chits to all existing players
        for player in current_player_ids.values():
            if player != lowest_scorer:  # Already assigned to lowest_scorer in initialize_game
                games[room_code]['players'][player] = assign_initial_chits(room_code)
                print(f"Assigned chits to {player}: {games[room_code]['players'][player]}")

        # Start the game if 4 players are present
        start_game_if_full(room_code)

        print(f"New game state after restart: {games[room_code]}")
        emit('update_game', games[room_code], room=room_code)

@socketio.on('end_game')
def end_game(data):
    room_code = data['room_code']
    print(f"Ending game in room {room_code}")
    if room_code in games:
        scores = games[room_code]['scores']
        final_winner = max(scores, key=scores.get)
        loser = min(scores, key=scores.get) if len(scores) > 1 else None
        emit('final_results', {
            'scores': scores,
            'final_winner': final_winner,
            'final_loser': loser
        }, room=room_code)
        del games[room_code]

if __name__ == "__main__":
    socketio.run(app, debug=True)