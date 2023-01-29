from util import W, H, FORMAT, NAME_MAX_LEN, HOST_IP_ADDR, PORT, START_RADIUS, MIN_NUM_BALL, DEL_SCORE, ROUND_TIME, MASS_LOSS_TIME, MIN_SCORE, SCORE_DEP_RATE, COLORS
import socket
from _thread import *
import _pickle as pickle
import time
import random
import math

# setup sockets
S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
S.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Set constants

# HOST_NAME = socket.gethostname()
SERVER_IP = socket.gethostbyname(HOST_IP_ADDR)

# try to connect to server
try:
    S.bind((SERVER_IP, PORT))
except socket.error as e:
    print(str(e))
    print("[SERVER] Server could not start")
    quit()

S.listen()  # listen for connections

print(f"[SERVER] Server Started with local ip {SERVER_IP}")

# dynamic variables
players = {}
balls = []
connections = 0
_id = 0
start = False
game_time = ROUND_TIME
nxt = 1


# helper functions

def release_mass(players):
    """
    Decreases score of players whose score is greater than MIN_SCORE to SCORE_DEP_RATE the original score. 

    Parameters
        players (dict): a dict of players mapping id to player 
            where each player is the dict {"x": int, "y": int, "color": tuple, "score": int, "name": str}
    Returns
        None
    """
    for player in players:
        p = players[player]
        if p["score"] > MIN_SCORE:
            p["score"] = math.floor(p["score"]*SCORE_DEP_RATE)


def check_collision(players, balls):
    """
    Checks if any of the player have collided with any of the balls.

    Parameters
        players (dict): dict of players mapping player id to player data
        balls (list): a list of balls
    Returns
        None
    """
    for player in players:
        p = players[player]
        x = p["x"]
        y = p["y"]
        for ball in balls:
            bx = ball[0]
            by = ball[1]

            dis = math.sqrt((x - bx)**2 + (y-by)**2)
            if dis <= START_RADIUS + p["score"]:
                p["score"] = p["score"] + DEL_SCORE
                balls.remove(ball)


def player_collision(players):
    """
    Checks for player collision and handles that collision.

    Parameters
        players (dict): dict of players mapping player id to player data
    Returns
        None
    """
    sort_players = sorted(players, key=lambda x: players[x]["score"])
    for x, player1 in enumerate(sort_players):
        for player2 in sort_players[x+1:]:
            p1x = players[player1]["x"]
            p1y = players[player1]["y"]

            p2x = players[player2]["x"]
            p2y = players[player2]["y"]

            dis = math.sqrt((p1x - p2x)**2 + (p1y-p2y)**2)
            if dis < players[player2]["score"] - players[player1]["score"]*0.85:
                players[player2]["score"] = math.sqrt(
                    players[player2]["score"]**2 + players[player1]["score"]**2)  # adding areas instead of radii
                players[player1]["score"] = 0
                players[player1]["x"], players[player1]["y"] = get_start_location(
                    players)
                print(f"[GAME] " + players[player2]["name"] +
                      " ATE " + players[player1]["name"])


def create_balls(balls, n):
    """
    Creates balls

    Parameters
        balls: a list to add balls to
        n: the amount of balls to add
    Returns
        None
    """
    for _ in range(n):
        while True:
            stop = True
            x = random.randrange(0, W)
            y = random.randrange(0, H)
            for player in players:
                p = players[player]
                dis = math.sqrt((x - p["x"])**2 + (y-p["y"])**2)
                if dis <= START_RADIUS + p["score"]:
                    stop = False
            if stop:
                break
        balls.append((x, y, random.choice(COLORS)))


def get_start_location(players):
    """
    Picks a start location for a player based on other player locations. 
    It will ensure it does not spawn inside another player.

    Parameters
        players (dict): dict of players mapping player id to player data
    Returns
        (x, y) (tuple): tuple of x, y coordinate
    """
    while True:
        stop = True
        x = random.randrange(0, W)
        y = random.randrange(0, H)
        for player in players:
            p = players[player]
            dis = math.sqrt((x - p["x"])**2 + (y-p["y"])**2)
            if dis <= START_RADIUS + p["score"]:
                stop = False
                break
        if stop:
            break
    return (x, y)


def threaded_client(conn, _id):
    """
    runs in a new thread for each player connected to the server

    :param con: ip address of connection
    :param _id: int
    :return: None
    """
    global connections, players, balls, game_time, nxt, start

    current_id = _id

    # recieve a name from the client
    name_data = conn.recv(4*NAME_MAX_LEN)
    name = name_data.decode(FORMAT)
    print("[LOG]", name, "connected to the server.")
    # pickle data and send initial info to clients
    conn.send(str(current_id).encode(FORMAT))

    # Setup properties for each new player
    color = COLORS[current_id % len(COLORS)]
    x, y = get_start_location(players)
    # initialize player data
    players[current_id] = {"x": x, "y": y,
                           "color": color, "score": 0, "name": name}

    init_req_data = conn.recv(8)
    init_req = init_req_data.decode(FORMAT)
    if init_req == "get":
        conn.send(pickle.dumps((balls, players, game_time)))
    else:
        print("[DISCONNECT] error with initial request")

    # server will recieve basic commands from client
    # it will send back all of the other clients info
    '''
	commands start with:
	move
	'''
    while True:
        if start:
            game_time = ROUND_TIME - round(time.time()-start_time)
            if game_time <= 0:
                start = False
            else:
                if (ROUND_TIME - game_time) // MASS_LOSS_TIME == nxt:
                    nxt += 1
                    release_mass(players)
                    print(f"[GAME] {name}'s Mass depleting")
        try:
            # Recieve data from client
            data = conn.recv(64)

            if not data:
                break

            data = data.decode(FORMAT)
            print('data recv', data)

            if data.split(" ")[0] == "move":
                split_data = data.split(" ")
                x = int(split_data[1])
                y = int(split_data[2])
                players[current_id]["x"] = x
                players[current_id]["y"] = y

                # only check for collison if the game has started
                if start:
                    check_collision(players, balls)
                    player_collision(players)

                # if the amount of balls is less than 150 create more
                if len(balls) < MIN_NUM_BALL:
                    create_balls(balls, random.randrange(100, MIN_NUM_BALL))
                    print("[GAME] Generating more orbs")

                # print((balls, players, game_time))
                # send data back to clients
                conn.send(pickle.dumps((balls, players, game_time)))

            else:
                start = False
                print("[DISCONNECT] error with request")
                break

        except Exception as e:
            print(e)
            break  # if an exception has been reached disconnect client

        # time.sleep(0.001)

    # user disconnects
    print("[DISCONNECT] Name:", name,
          ", Client Id:", current_id, "disconnected")
    connections -= 1
    del players[current_id]  # remove client information from players list
    conn.close()  # close connection


# MAINLOOP

# setup level with balls
create_balls(balls, random.randrange(200, 2*MIN_NUM_BALL))

print("[GAME] Setting up level")
print("[SERVER] Waiting for connections")

# Keep looping to accept new connections
while True:

    host, addr = S.accept()
    print("[CONNECTION] Connected to:", addr)

    # start game when a client on the server computer connects
    if addr[0] == SERVER_IP and not (start):
        start = True
        start_time = time.time()
        print("[STARTED] Game Started")

    # increment connections start new thread then increment ids
    connections += 1
    start_new_thread(threaded_client, (host, _id))
    _id += 1
