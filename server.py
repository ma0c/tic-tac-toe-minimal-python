#!/usr/bin/env python

import os
import sys
import json

from django import setup
from django.conf import settings
from django.conf.urls import url
from django.core.management import execute_from_command_line
from django.http import JsonResponse
from django.db import models
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[0] = os.path.dirname(BASE_DIR)
APP_LABEL = os.path.basename(BASE_DIR)


settings.configure(
    DEBUG=True,
    SECRET_KEY='A-random-secret-key!',
    ROOT_URLCONF=sys.modules[__name__],
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        APP_LABEL,
    ],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }
)

setup()

class Game(models.Model):
    game = models.CharField(max_length=9)
    author = models.TextField()

    class Meta:
        app_label = APP_LABEL


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


class CreateOrJoin(View):
    def get(self, request, *args, **kwargs):
        if not GAMES or GAMES[-1]['turn'] > 1:
            # There are no games
            json_response = self.create_new_game()
            json_response['id'] = len(GAMES)
            GAMES.append(json_response)
            json_response['last_player'] = "O"
        else:
            # Return last game
            current_game = GAMES[-1]
            json_response = current_game.copy()
            json_response['last_player'] = "X"
        print(GAMES)
        return JsonResponse(json_response)

    def create_new_game(self):
        new_game = dict()
        new_game['board'] = [' ' for _ in range(9)]
        new_game['turn'] = 0
        new_game['finished'] = False
        new_game['winner'] = ''
        return new_game


class MakeMove(View):

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(MakeMove, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def check_winner(board, current_player, play):
        for possible_win in CHECK_FOR_WIN[play]:
            is_a_win = True
            for slot in WINNER_MATRIX[possible_win]:
                if board[slot] != current_player:
                    is_a_win = False
                    break
            if is_a_win:
                return True
        return False

    @staticmethod
    def check_game_end(turn):
        return turn >= 9

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
                if current_game['board'][move_index - 1] == " ":
                    if current_game['last_player'] == player:
                        response['status'] = 400
                        response['message'] = TURN_INVALID
                    else:
                        current_game['board'][move_index - 1] = player
                        current_game['last_player'] = player
                        current_game['turn'] += 1
                        if self.check_winner(
                                current_game['board'],
                                player,
                                move_index -1
                        ):
                            current_game['finished'] = True
                            current_game['winner'] = player
                            response['finished'] = True
                            response['message'] = GAME_ENDED_WITH_WINNER.format(player)
                        elif self.check_game_end(current_game['turn']):
                            current_game['finished'] = True
                            response['finished'] = True
                            response['message'] = GAME_ENDED_WITH_DRAW

                        response['status'] = 200
                        response['message'] = response.get('message', '')
                        response['board'] = current_game['board']
                        response['last_player'] = current_game['last_player']
                        response['turn'] = current_game['turn']
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
                response['turn'] = game['turn']
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
                response['turn'] = game['turn']
                response['board'] = game['board']
                response['finished'] = game['finished']
                if game['finished']:
                    if game['winner']:
                        response['message'] = GAME_ENDED_WITH_WINNER.format(game['winner'])
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
