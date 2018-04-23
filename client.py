#!/usr/bin/env python

import requests
import time

BOARD_WIDTH = 3
BOARD_HEIGHT = 3


WELCOME_MESSAGE = "Welcome to tictactoe press: \n1. To play\n2. For Instructions\n3. Exit:\n"
UNAVAILABLE_OPTION = "Unavailable option"
GETTING_GAME_MESSAGE = "We're checking for game availability"
INSTRUCTION_MESSAGE = "To play put a number between 1 and 9  that represent the grid"
MAKE_MOVE_MESSAGE = "Make your move [1-9]:\n"
INVALID_MOVE_MESSAGE = "Invalid move, try again"
SLOT_OCCUPIED = "Slot Occupied"
WAITING_FOR_PLAYER = "Waiting for player"
EXIT_MESSAGE = "Have a nice day"
INSTRUCTION_GRID = [str(x) for x in range(1, 10)]
UNAVAILABLE_SERVER = "Unavailable server, please try later"

BACKEND_URL = "http://localhost:8000"
CREATE_OR_JOIN_ENDPOINT = "/create-or-join/"
MAKE_MOVE_ENDPOINT = "/make-move/"
GAME_STATUS_ENDPOINT = "/game-status/"
GET_BOARD_ENDPOINT = "/get-board/"


def print_board(board_str):
    """
from client import print_board
print_board("XO XO X  ")
    :param board_str: 
    :return: 
    """
    # separated_board = "|".join(board_str)
    print("|".join(board_str[0:3]))
    print("|".join(board_str[3:6]))
    print("|".join(board_str[6:9]))


def read_valid_move(board):
    user_input = input(MAKE_MOVE_MESSAGE)
    try:
        int_move = int(user_input.strip())
        if 1 <= int_move <= 9:
            if board[int_move-1] == " ":
                return int_move
            else:
                print(SLOT_OCCUPIED)
    except ValueError:
        pass
    print(INVALID_MOVE_MESSAGE)
    return read_valid_move(board)


def main_menu():
    user_input = input(WELCOME_MESSAGE)
    try:
        int_value = int(user_input.strip())
        if int_value == 1:
            loop()
        elif int_value == 2:
            instructions()
        elif int_value == 3:
            exit_game()
        else:
            print("Main main Not main main option", int_value)
            print(UNAVAILABLE_OPTION)
    except ValueError:
        print("Main main Not menu option")
        print(UNAVAILABLE_OPTION)


def make_move(game_id, move_index, player):
    payload = {
        'id': game_id,
        'move_index': move_index,
        'player': player
    }
    make_move_response = requests.post(
        "{}{}".format(BACKEND_URL, MAKE_MOVE_ENDPOINT),
        json=payload
    )
    if make_move_response.status_code == 200:
        return make_move_response.json()
    else:
        print(UNAVAILABLE_SERVER)
        exit(0)


def check_status(game_id):
    check_status_response = requests.get(
        "{}{}?id={}".format(BACKEND_URL, GAME_STATUS_ENDPOINT, game_id)
    )
    if check_status_response.status_code == 200:
        response_json = check_status_response.json()
        return response_json.get('turn', game_id)
    else:
        return game_id


def get_board(game_id):
    check_status_response = requests.get(
        "{}{}?id={}".format(BACKEND_URL, GET_BOARD_ENDPOINT, game_id)
    )
    if check_status_response.status_code == 200:
        response_json = check_status_response.json()
        return response_json
    else:
        return dict()


def wait_for_play(current_game, turn):
    while check_status(current_game) <= turn:
        print(WAITING_FOR_PLAYER)
        time.sleep(1)


def loop():
    print(WELCOME_MESSAGE)
    create_or_join_request = requests.get("{}{}".format(BACKEND_URL, CREATE_OR_JOIN_ENDPOINT))
    if create_or_join_request.status_code == 200:
        response_json = create_or_join_request.json()
        current_game = response_json.get('id', 0)
        last_player = response_json.get('last_player', 'O')
        player = "X" if last_player == "O" else "O"
        print("Game number {}".format(current_game))
        board = [' ' for _ in range(9)]
        turn = response_json.get('turn', 0)
        print("You are {}".format(player))
        if player == "O":
            wait_for_play(current_game, turn)
            response_json = get_board(current_game)
        while not response_json.get("finished", True):
            board = response_json.get('board', board)
            print_board(board)
            response_json = make_move(
                current_game,
                read_valid_move(board),
                player
            )
            turn = response_json.get('turn', turn)
            board = response_json.get('board', board)
            print_board(board)
            print(response_json.get('message', ''))

            if not response_json.get("finished", True):
                # The game is not ended
                wait_for_play(current_game, turn)
                response_json = get_board(current_game)
                if response_json.get("finished", False):
                    # The opponent won the game
                    print_board(response_json.get('board', board))
                    print(response_json.get('message', ''))
            else:
                # The game ended because I win
                pass
        main_menu()
    else:
        print(UNAVAILABLE_SERVER)


def instructions():
    print(INSTRUCTION_MESSAGE)
    print(print_board(INSTRUCTION_GRID))
    main_menu()


def exit_game():
    print(EXIT_MESSAGE)
    exit(0)

if __name__ == '__main__':
    main_menu()
