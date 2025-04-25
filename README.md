16 Chits Game

Welcome to the 16 Chits Game, a fun and interactive multiplayer card game implemented in Python using PySimpleGUI! This project recreates a classic chit-passing game where 4 players compete to collect 4 identical chits, with an exciting twist on victory declaration and reaction timing.

Features:
1. Multiplayer Fun: Designed for 4 players who pass a single device (or can be adapted for online play).
2. Chit Selection: Players see their 4 chits as clickable buttons during their turn, selecting one to pass to the next player.
3. Victory Detection: Declare victory when you have 4 matching chits, even if you hold extra chits.
4. Reaction Challenge: After a player wins, others must react by tapping a "Stack Hand" button in sequence, with reaction times recorded. The slowest player starts the next round.
5. Dynamic UI: Chits are hidden except during a player's turn, and a hand emoji (✋) appears after stacking, followed by a "Next Turn" option for smooth device passing.
6. No Distractions: Seamless gameplay with no popups during chit passing, ensuring an immersive experience.


How to Play:
1. Run the script and distribute the device among 4 players.
2. Each player takes turns selecting a chit to pass to the next player using the buttons.
3. When a player collects 4 identical chits, they declare victory.
4. Pass the device to each remaining player to stack their hand, recording reaction times.
5. The slowest reactor is revealed, and the game restarts with them starting.
Requirements:
-> Python 3.x
-> PySimpleGUI (pip install PySimpleGUI)


Getting Started:
1. Clone this repository: git clone https://github.com/yourusername/16-chits-game.git
2. Navigate to the directory: cd 16-chits-game
3. Install the required library: pip install PySimpleGUI
4. Run the game: python 16_chits_game.py
