from pygame.math import Vector2 as vec

'''
settings文件
存放大部分常量

'''

# UI
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 64

# overlay position
OVERLAY_POSITIONS = {
    'tool': (40, SCREEN_HEIGHT - 15),
    'seed': (70, SCREEN_HEIGHT - 5),
}

PLAY_TOOL_OFFSET = {
    'left': vec(-50, 40),
    'right': vec(50, 40),
    'up': vec(0, -10),
    'down': vec(0, 50),
}

LAYERS = {
    'water': 0,
    'ground': 1,
    'soil': 2,
    'soil water': 3,
    'rain floor': 4,
    'house bottom': 5,
    'ground plant': 6,
    'main': 7,
    'house top': 8,
    'fruit': 9,
    'rain drops': 10,
}

APPLE_POS = {
    'Small': [(18, 17), (30, 37), (12, 50), (30, 45), (20, 30), (30, 10)],
    'Large': [(30, 24), (60, 65), (50, 50), (16, 40), (45, 50), (42, 70)]
}

GROW_SPEED = {
    'cron': 1,
    'tomato': 0.7
}
