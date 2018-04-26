import sys
import json
import copy


from random import choice

from django.conf import settings
from django.conf.urls import url
from django.core.management import execute_from_command_line
from django.http import JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

settings.configure(
    DEBUG=True,
    SECRET_KEY='A-random-secret-key!',
    ROOT_URLCONF=sys.modules[__name__],
)

INVALID_PAYLOAD = "Invalid Payload"
INVALID_MOVE_MESSAGE = "Invalid Move"
GAME_NOT_FOUND_MESSAGE = "Game not found"
TURN_INVALID = "Turn invalid please wait for opponent"
GAME_ENDED_WITH_WINNER = "The game is ended and the winner is {}"
GAME_ENDED_WITH_DRAW = "The game is ended there is a draw"
GAMES = list()

# This matrix could be calculated automatically
WINNER_MATRIX = [
    [0, 1, 2],  # 0
    [3, 4, 5],  # 1
    [6, 7, 8],  # 2
    [0, 3, 6],  # 3
    [1, 4, 7],  # 4
    [2, 5, 8],  # 5
    [0, 4, 8],  # 6
    [2, 4, 6]   # 7
]

# Also this dict but for AI this should be a better option
CHECK_FOR_WIN = {
    0: [0, 3, 6],
    1: [0, 4],
    2: [0, 5, 7],
    3: [1, 3],
    4: [1, 4, 6, 7],
    5: [1, 5],
    6: [2, 3, 7],
    7: [2, 4],
    8: [2, 5, 6],
}


class Game(object):
    PLAY_WIN = "win"
    PLAY_DRAW = "draw"
    PLAY_OK = "play_ok"

    P2P_GAME = "p2p"
    LVL1_GAME = "lvl1"
    LVL2_GAME = "lvl2"

    id = 0
    board = [' ' for _ in range(9)]
    turn = 0
    finished = False
    winner = ""
    game_type = "p2p"
    last_player = ""

    def make_move(self, player, position):
        self.board[position] = player
        self.last_player = player
        self.turn += 1
        if self.check_winner(position):
            self.finished = True
            self.winner = player
            return self.PLAY_WIN
        if self.check_game_end():
            self.finished = True
            return self.PLAY_DRAW
        return self.PLAY_OK

    def check_winner(self, play):
        for possible_win in CHECK_FOR_WIN[play]:
            is_a_win = True
            for slot in WINNER_MATRIX[possible_win]:
                if self.board[slot] != self.last_player:
                    is_a_win = False
                    break
            if is_a_win:
                return True
        return False

    def check_game_end(self):
        return self.turn >= 9

    def to_json(self):
        return {
            'id': self.id,
            'board': self.board,
            'turn': self.turn,
            'finished': self.finished,
            'winner': self.winner,
            'game_type': self.game_type,
            'last_player': self.last_player,
        }

    def copy(self):
        return copy.copy(self)

    def __str__(self):
        return str(self.to_json())


class GameAgent(object):

    @staticmethod
    def make_move(board):
        pass


class RandomAgent(GameAgent):

    @staticmethod
    def make_move(board):
        possibles_movements = [i for i, x in enumerate(board) if x == " "]
        if len(possibles_movements) > 0:
            return choice(possibles_movements)
        return None


class CreateOrJoin(View):
    def get(self, request, *args, **kwargs):
        if not GAMES or GAMES[-1].turn > 1:
            # There are no games
            json_response = self.create_new_game()
            json_response.id = len(GAMES)
            GAMES.append(json_response)
            json_response.last_player = "O"
        else:
            # Return last game
            current_game = GAMES[-1]
            json_response = current_game.copy()
            # json_response = current_game  # .copy()
            json_response.last_player = "X"
        print(json_response)
        return JsonResponse(json_response.to_json())

    def create_new_game(self):
        new_game = Game()
        new_game.board = [' ' for _ in range(9)]
        new_game.turn = 0
        new_game.finished = False
        new_game.winner = ''
        new_game.type = self.request.GET.get('type', 'p2p')

        return new_game


class MakeMove(View):

    def add_status_flags_to_response(self, response, game_status, player):
        if game_status == Game.PLAY_WIN:
            response['finished'] = True
            response['message'] = GAME_ENDED_WITH_WINNER.format(player)
        elif game_status == Game.PLAY_DRAW:
            response['finished'] = True
            response['message'] = GAME_ENDED_WITH_DRAW

    def post(self, request, *args, **kwargs):
        body = json.loads(request.body)
        print(body)
        response = dict()
        game_index = body.get('id', None)
        move_index = body.get('move_index', None)
        player = body.get('player', None)

        if game_index is None or move_index is None or player is None:
            response['status'] = 400
            response['message'] = INVALID_PAYLOAD

        else:
            try:
                game_index = int(game_index)
                current_game = GAMES[game_index]
                if current_game.board[move_index - 1] == " ":
                    if current_game.last_player == player:
                        response['status'] = 400
                        response['message'] = TURN_INVALID
                    else:
                        game_status = current_game.make_move(player, move_index -1)
                        game_type = current_game.type
                        print(current_game.board)
                        self.add_status_flags_to_response(response, game_status, player)

                        if game_type != Game.P2P_GAME and game_status == Game.PLAY_OK:
                            machine_player = "X" if player == "O" else "O"
                            if game_type == Game.LVL1_GAME:
                                random_movement = RandomAgent.make_move(current_game.board)

                                if random_movement is not None:
                                    game_status = current_game.make_move(machine_player, random_movement)
                                    self.add_status_flags_to_response(response, game_status, machine_player)
                            elif game_type == Game.LVL2_GAME:
                                pass

                        response['status'] = 200
                        response['message'] = response.get('message', '')
                        response['board'] = current_game.board
                        response['last_player'] = current_game.last_player
                        response['turn'] = current_game.turn
                else:
                    response['status'] = 400
                    response['message'] = INVALID_MOVE_MESSAGE

            except ValueError:
                response['status'] = 400
                response['message'] = INVALID_MOVE_MESSAGE
            except IndexError:
                response['status'] = 400
                response['message'] = GAME_NOT_FOUND_MESSAGE

        response['finished'] = response.get('finished', False)
        return JsonResponse(response)


class GameStatus(View):

    def get(self, request, *args, **kwargs):
        response = dict()
        game_index = request.GET.get('id', None)
        if game_index is None:
            response['status'] = 400
            response['message'] = INVALID_PAYLOAD
        else:
            try:
                game_index = int(game_index)
                game = GAMES[game_index]
                response['status'] = 200
                response['turn'] = game.turn
            except ValueError:
                response['status'] = 400
                response['message'] = INVALID_PAYLOAD
            except IndexError:
                response['status'] = 400
                response['message'] = GAME_NOT_FOUND_MESSAGE
        return JsonResponse(response)


class GetBoard(View):

    def get(self, request, *args, **kwargs):
        response = dict()
        game_index = request.GET.get('id', None)
        if game_index is None:
            response['status'] = 400
            response['message'] = INVALID_PAYLOAD
        else:
            try:
                game_index = int(game_index)
                game = GAMES[game_index]
                response['status'] = 200
                response['turn'] = game.turn
                response['board'] = game.board
                response['finished'] = game.finished
                if game.finished:
                    if game.winner:
                        response['message'] = GAME_ENDED_WITH_WINNER.format(game.winner)
                    else:
                        response['message'] = GAME_ENDED_WITH_DRAW
                response['message'] = response.get('message', '')
            except ValueError:
                response['status'] = 400
                response['message'] = INVALID_PAYLOAD
            except IndexError:
                response['status'] = 400
                response['message'] = GAME_NOT_FOUND_MESSAGE
        return JsonResponse(response)

urlpatterns = [
    url(r'^create-or-join/$', CreateOrJoin.as_view()),
    url(r'^make-move/$', MakeMove.as_view()),
    url(r'^game-status/$', GameStatus.as_view()),
    url(r'^get-board/$', GetBoard.as_view()),
]

if __name__ == '__main__':
    execute_from_command_line(sys.argv)
