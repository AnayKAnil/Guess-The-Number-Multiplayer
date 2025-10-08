const socket = io();
const messages = document.getElementById('Messages');
const joinForm = document.getElementById('JoinForm');
const guessForm = document.getElementById('GuessForm');
const playerInput = document.getElementById('Player');
const guessInput = document.getElementById('Guess');
const playersDiv = document.getElementById('Players');

function addMessage(msg) {
  const div = document.createElement('div');
  div.className = 'message';
  div.innerText = msg;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function updatePlayerList(players) {
  playersDiv.innerHTML = "<strong>Players:</strong> " + players.join(', ');
}

socket.on('game_message', (data) => {
  addMessage(data.msg);
});
socket.on('player_list', (players) => {
  updatePlayerList(players);
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
