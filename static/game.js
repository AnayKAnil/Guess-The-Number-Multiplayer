const socket = io();
const messages = document.getElementById('Messages');
const joinForm = document.getElementById('JoinForm');
const guessForm = document.getElementById('GuessForm');
const playerInput = document.getElementById('Player');
const guessInput = document.getElementById('Guess');
const playersDiv = document.getElementById('Players');
const gameStatusDiv = document.getElementById('GameStatus');

function addMessage(msg) {
  const div = document.createElement('div');
  div.className = 'message';
  div.innerText = msg;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function updatePlayerList(data) {
  if (data.players && data.players.length > 0) {
    playersDiv.innerHTML = `<strong>🎮 Players Online (${data.count}):</strong> ${data.players.join(', ')}`;
  } else {
    playersDiv.innerHTML = '<strong>🎮 No players online</strong>';
  }
}

function updateGameStatus(data) {
  if (gameStatusDiv) {
    gameStatusDiv.innerHTML = `<strong>📊 Round ${data.current_round} | Total Guesses: ${data.total_guesses} | Players: ${data.total_players}</strong>`;
  }
}

socket.on('game_message', (data) => {
  addMessage(data.msg);
});

socket.on('player_list', (data) => {
  updatePlayerList(data);
});

socket.on('game_state', (data) => {
  updateGameStatus(data);
});

joinForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const player = playerInput.value.trim() || 'Anonymous';
  socket.emit('join_player', { username: player });
  joinForm.style.display = 'none';
  guessForm.style.display = 'flex';
});

guessForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const guess = guessInput.value.trim();
  if (!guess) return;
  socket.emit('make_guess', { guess });
  guessInput.value = '';
  guessInput.focus();
});
