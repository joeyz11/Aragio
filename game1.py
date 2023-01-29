from util import W, H, NAME_MAX_LEN, START_RADIUS, ROUND_TIME, START_VEL, BALL_RADIUS
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
from client import Network
from sys import exit
import os

# set up pygame
pygame.font.init()

# constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

NAME_FONT = pygame.font.SysFont("verdana", 20)
TIME_FONT = pygame.font.SysFont("verdana", 30)
SCORE_FONT = pygame.font.SysFont("verdana", 26)


# make window start in top left hand corner
# os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 30)


# helper functions
def get_user_name():
    """
    Gets user input for name.

    Parameters
        NAME_MAX_LEN
    Returns
        name (str): string of len between 1 and NAME_MAX_LEN [inclusive]
    """
    while True:
        name = input("Please enter your name: ")
        if 1 <= len(name) <= NAME_MAX_LEN:
            return name
            break
        else:
            print(
                f"Error, your name must be between 1 and {NAME_MAX_LEN} characters long [inclusive]")


def convert_time(t_sec):
    """
    Convert a time given in seconds to a time in minutes as a string.

    Parameters
        t_sec (int): time in seconds
        ROUND_TIME
    Returns
        t_min (str): time formatted MM:SS as a string if t_sec is less than ROUND_TIME, else return the string `Starting Soon`
    """
    if t_sec == ROUND_TIME:
        return "Starting Soon"

    min = str(t_sec // 60)
    sec = str(t_sec % 60)
    if len(sec) == 1:
        t_min = min + ":0" + sec
    else:
        t_min = min + ":" + sec
    return t_min


def format_data(x, y):
    """
    Formats updated x and y coordinate.

    Parameters
        x (int): The updated x coordinate
        y (int): The updated y coordinate
    Returns
        A string in the format `move x y` where x and y are replaced by values
    """
    return "move " + str(x) + " " + str(y)


def redraw_balls(balls):
    """
    Draw balls to screen.

    Parameters
        balls (list): A list of balls where each ball is in the tuple (int x, int y, tuple color)
    Returns
        None
    """
    for ball in balls:
        pygame.draw.circle(SCREEN, ball[2], (ball[0], ball[1]), BALL_RADIUS)
    return None


def redraw_players(players):
    """
    Draw players to the screen.

    Parameters
        players (dict): a dict of players mapping id to player 
        where each player is the dict {"x": int, "y": int, "color": str, "score": int, "name": str}
    Returns
        None
    """
    for player in sorted(players, key=lambda x: players[x]["score"]):
        p = players[player]
        pygame.draw.circle(
            SCREEN, p["color"], (p["x"], p["y"]), START_RADIUS + round(p["score"]))
        text = NAME_FONT.render(p["name"], 1, BLACK)
        SCREEN.blit(text, (p["x"] - text.get_width() /
                    2, p["y"] - text.get_height()/2))
    return None


def redraw_scoreboard(players):
    """
    Sorts the players by score and draws the scoreboard.

    Parameters
        players (dict): a dict of players mapping id to player 
        where each player is the dict {"x": int, "y": int, "color": str, "score": int, "name": str}
    Returns
        None
    """
    sort_players = list(
        reversed(sorted(players, key=lambda x: players[x]["score"])))
    title = TIME_FONT.render("Scoreboard", True, BLACK)
    start_y = 50
    x = W - title.get_width() - 50
    SCREEN.blit(title, (x, 5))

    ran = min(len(players), 3)
    for count, i in enumerate(sort_players[:ran]):
        text = SCORE_FONT.render(
            str(count+1) + ". " + str(players[i]["name"]), True, BLACK)
        SCREEN.blit(text, (x, start_y + count * 20))
    return None


def redraw_timer(game_time):
    """
    Draws the time to the screen.

    Parameters
        game_time (int): time left of the round
    Returns
        None
    """
    text = TIME_FONT.render(
        "Time: " + convert_time(game_time), True, BLACK)
    SCREEN.blit(text, (10, 10))
    return None


def redraw_score(score):
    """
    Draws the score to the screen.

    Parameters
        score (int): score of the current player
    Returns
        None
    """
    text = TIME_FONT.render("Score: " + str(round(score)), True, BLACK)
    SCREEN.blit(text, (10, 15 + text.get_height()))
    return None


def redraw_screen(balls, players, game_time, score):
    """
    Redraws the screen.

    Parameters
        balls (list): list of ball data
        players (dict): dictionary of id to player data
        game_time (int): time left of the round
        score (int): score of the current player
    Returns
        None
    """
    SCREEN.fill(WHITE)
    redraw_balls(balls)
    redraw_players(players)
    redraw_scoreboard(players)
    redraw_timer(game_time)
    redraw_score(score)
    return None


def main(name):
    """
    Runs the client side and main game loop.

    Parameters
        name (str): name of the current player
    Returns
        None
    """
    # set up socket and clock
    server = Network()
    curr_id = server.connect(name)
    balls, players, game_time = server.send("get")

    # print('players', players)
    clock = pygame.time.Clock()

    # game loop
    while True:
        clock.tick(30)  # 30 fps max
        curr_p = players[curr_id]
        curr_vel = max(1, START_VEL - round(curr_p["score"]/14))
        keys = pygame.key.get_pressed()
        # go left
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if curr_p["x"] - curr_vel - START_RADIUS - curr_p["score"] >= 0:
                curr_p["x"] = curr_p["x"] - curr_vel
        # go right
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if curr_p["x"] + curr_vel + START_RADIUS + curr_p["score"] <= W:
                curr_p["x"] = curr_p["x"] + curr_vel
        # go up
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if curr_p["y"] - curr_vel - START_RADIUS - curr_p["score"] >= 0:
                curr_p["y"] = curr_p["y"] - curr_vel
        # go down
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if curr_p["y"] + curr_vel + START_RADIUS + curr_p["score"] <= H:
                curr_p["y"] = curr_p["y"] + curr_vel
        data = format_data(curr_p["x"], curr_p["y"])
        # send data to server and recieve back all players information
        # server.send(data)
        # print('x', x, '\n')
        # balls, players, game_time = server.send(data)

        for event in pygame.event.get():
            # quit the game
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                server.disconnect()
                pygame.quit()
                exit()
        redraw_screen(balls, players, game_time, curr_p["score"])
        pygame.display.update()


# start client
name = get_user_name()
SCREEN = pygame.display.set_mode((W, H))
pygame.display.set_caption("Aragio")
main(name)
