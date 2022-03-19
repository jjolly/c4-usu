from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from rest_framework.decorators import api_view
import numpy as np
import math
import random
from .models import Win

def index(request):
  return render(request, 'game/index.html')

def twoPlayer(request):
  return render(request, 'game/two-players.html')

def onePlayer(request):
    
    context = {'player1': Win.objects.filter(winner=1).count(), 'player2': Win.objects.filter(winner=2).count()}
    return render(request, 'game/one-player.html', context)

ROW_COUNT = 6
COLUMN_COUNT = 7

EMPTY = 0
PLAYER_PIECE = 1
AI_PIECE = 2

WINDOW_LENGTH = 4

TERMINAL_NO_WIN = 0
TERMINAL_PLAYER_WIN = PLAYER_PIECE
TERMINAL_AI_WIN = AI_PIECE
NON_TERMINAL = 3

def is_valid_location(board, col):
  return board[ROW_COUNT-1][col] == 0

def get_valid_locations(board):
  valid_locations = []
  for col in range(COLUMN_COUNT):
    if is_valid_location(board, col):
      valid_locations.append(col)
  return valid_locations

def winning_move(board, piece):
  # Check horizontal locations for win
  for c in range(COLUMN_COUNT-3):
    for r in range(ROW_COUNT):
      if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
        return True

  # Check vertical locations for win
  for c in range(COLUMN_COUNT):
    for r in range(ROW_COUNT-3):
      if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
        return True

  # Check positively sloped diaganols
  for c in range(COLUMN_COUNT-3):
    for r in range(ROW_COUNT-3):
      if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
        return True

  # Check negatively sloped diaganols
  for c in range(COLUMN_COUNT-3):
    for r in range(3, ROW_COUNT):
      if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
        return True

def get_terminal_state(board):
  if winning_move(board, PLAYER_PIECE):
    return TERMINAL_PLAYER_WIN
  elif winning_move(board, AI_PIECE):
    return TERMINAL_AI_WIN
  elif len(get_valid_locations(board)) == 0:
    return TERMINAL_NO_WIN
  return NON_TERMINAL

def evaluate_window(window, piece):
  score = 0
  opp_piece = PLAYER_PIECE
  if piece == PLAYER_PIECE:
    opp_piece = AI_PIECE

  if window.count(piece) == 4:
    score += 100
  elif window.count(piece) == 3 and window.count(EMPTY) == 1:
    score += 5
  elif window.count(piece) == 2 and window.count(EMPTY) == 2:
    score += 2

  if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
    score -= 4

  return score

def score_position(board, piece):
  score = 0

  ## Score center column
  center_array = [int(i) for i in list(board[:, COLUMN_COUNT//2])]
  center_count = center_array.count(piece)
  score += center_count * 3

  ## Score Horizontal
  for r in range(ROW_COUNT):
    row_array = [int(i) for i in list(board[r,:])]
    for c in range(COLUMN_COUNT-3):
      window = row_array[c:c+WINDOW_LENGTH]
      score += evaluate_window(window, piece)

  ## Score Vertical
  for c in range(COLUMN_COUNT):
    col_array = [int(i) for i in list(board[:,c])]
    for r in range(ROW_COUNT-3):
      window = col_array[r:r+WINDOW_LENGTH]
      score += evaluate_window(window, piece)

  ## Score posiive sloped diagonal
  for r in range(ROW_COUNT-3):
    for c in range(COLUMN_COUNT-3):
      window = [board[r+i][c+i] for i in range(WINDOW_LENGTH)]
      score += evaluate_window(window, piece)

  for r in range(ROW_COUNT-3):
    for c in range(COLUMN_COUNT-3):
      window = [board[r+3-i][c+i] for i in range(WINDOW_LENGTH)]
      score += evaluate_window(window, piece)

  return score

def get_next_open_row(board, col):
  for r in range(ROW_COUNT):
    if board[r][col] == 0:
      return r

def drop_piece(board, row, col, piece):
  board[row][col] = piece

def minimax(board, depth, alpha, beta, maximizingPlayer):
  if depth == 0:
    return (None, score_position(board, AI_PIECE))
  terminal_state = get_terminal_state(board)
  if terminal_state == TERMINAL_AI_WIN:
    return (None, 100000000000000)
  if terminal_state == TERMINAL_PLAYER_WIN:
    return (None, -10000000000000)
  if terminal_state == TERMINAL_NO_WIN:
    return (None, 0)
  valid_locations = get_valid_locations(board)
  if maximizingPlayer:
    value = -math.inf
    column = random.choice(valid_locations)
    for col in valid_locations:
      row = get_next_open_row(board, col)
      b_copy = board.copy()
      drop_piece(b_copy, row, col, AI_PIECE)
      new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
      if new_score > value:
        value = new_score
        column = col
      alpha = max(alpha, value)
      if alpha >= beta:
        break
    return column, value

  else: # Minimizing player
    value = math.inf
    column = random.choice(valid_locations)
    for col in valid_locations:
      row = get_next_open_row(board, col)
      b_copy = board.copy()
      drop_piece(b_copy, row, col, PLAYER_PIECE)
      new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
      if new_score < value:
        value = new_score
        column = col
      beta = min(beta, value)
      if alpha >= beta:
        break
    return column, value

def search_for_move(b):
  col, minimax_score = minimax(b, 5, -math.inf, math.inf, True)
  return col

@api_view(['GET'])
def move_from_board(request, pk):
  if request.method == 'GET':
    if len(pk) != 42:
      return HttpResponseBadRequest('Invalid Board Configuration')
    board = np.flipud(np.asarray([int(x) for x in pk]).reshape((ROW_COUNT,COLUMN_COUNT))).copy()
    terminal_state = get_terminal_state(board)
    result = (False, 0, True, terminal_state)
    if terminal_state == NON_TERMINAL:
      col = search_for_move(board.copy())
      drop_piece(board, get_next_open_row(board, col), col, AI_PIECE)
      terminal_state = get_terminal_state(board)
      result = (True, col, True, terminal_state)
      if terminal_state == NON_TERMINAL:
        result = (True, col, False, 0)
    resp = dict(zip(('move_valid', 'move_col', 'is_finished', 'winner'), result))
    if resp["is_finished"]:
      winner = Win(winner=resp['winner'])
      winner.save()
      print(Win.objects.filter(winner=2).count(), resp['winner'])

    return JsonResponse(resp)
