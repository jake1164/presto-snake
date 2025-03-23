import utime
from random import randint

from machine import I2C
from presto import Presto

from qwstpad import ADDRESSES, QwSTPad

"""
Snake Game ported for the Presto.

Controls:
* U = Move Forward
* D = Move Backward
* R = Move Right
* L = Move left
* + = Continue (once the current level is complete)
"""

# Setup the Presto display
presto = Presto(ambient_light=True)
display = presto.display

# Get width and height of the display
WIDTH, HEIGHT = display.get_bounds()

I2C_PINS = {"id": 0, "sda": 40, "scl": 41}
I2C_ADDRESSES = ADDRESSES[0]
BRIGHTNESS = 1.0

# Colors
SNAKE_COLOR = display.create_pen(0, 200, 0) # Green
FOOD_COLOR  = display.create_pen(200, 0, 0) # Red
WALL_COLOR  = display.create_pen(200, 0, 200) # Purple
TITLE_COLOR = display.create_pen(255, 255, 0) # Yellow
SCORE_COLOR = display.create_pen(255, 255, 255) # White
BACKGROUND_COLOR = display.create_pen(0, 0, 0) # Black

tile_size = 12
grid_w = WIDTH // tile_size
grid_h = HEIGHT // tile_size

i2c = I2C(**I2C_PINS)
complete = False


class State:
    TITLE = 0
    LEVEL = 1
    LIVES = 2
    PLAYING = 3
    SCORE = 4
    GAME_OVER = 5


class Node:
    def __init__(self, position=None, direction=None, next=None) -> None:
        self.position = position
        self.direction = direction
        self.next = next


class Snake:
    def __init__(self) -> None:
        center = grid_w//2, grid_h//2
        self.direction = (0, 0)
        self.head = Node(center, self.direction)

    def push(self, new_head) -> None:
        new_head.next = self.head
        self.head = new_head

    def __len__(self) -> int:
        length = 0
        current = self.head
        while current:
            length += 1
            current = current.next
        return length


    def pop(self) -> None:
        current = self.head
        previous = None

        while current.next:
            previous = current
            current = current.next

        if previous:
            previous.next = None


    def contains(self, position) -> bool:
        current = self.head

        while current:
            if current.position == position:
                return True
            current = current.next

        return False


    def move(self) -> Node:
        x, y = self.direction
        head_x, head_y = self.head.position

        head_x += x
        head_y += y

        head_x %= grid_w
        head_y %= grid_h

        new_node = Node((head_x, head_y), self.direction)

        return new_node


    def show(self):
        display.set_pen(SNAKE_COLOR)

        current = self.head
        previous = None

        while current:
            if current != self.head and previous is not None:
                x1, y1 = current.position
                x2, y2 = previous.position

                invisible = abs(x1 - x2) > 1 or abs(y1 - y2) > 1

                if not invisible:
                    x1 *= tile_size
                    y1 *= tile_size
                    x2 *= tile_size
                    y2 *= tile_size

                    x1 += tile_size // 2
                    y1 += tile_size // 2
                    x2 += tile_size // 2
                    y2 += tile_size // 2
                    self.line(x1, y1, x2, y2)
            else:
                x, y = current.position
                x *= tile_size
                y *= tile_size

                center_x = x + tile_size // 2
                center_y = y + tile_size // 2
                radius = tile_size - 4 // 2

                display.circle(center_x, center_y, radius)

            previous = current
            current = current.next


    def moving(self) -> bool:
        return self.direction != (0, 0)


    def update_direction(self, pressed) -> None:
        if pressed['U']:
            self.direction = (0, -1)
        elif pressed['D']:
            self.direction = (0, 1)
        elif pressed['L']:
            self.direction = (-1, 0)
        elif pressed['R']:
            self.direction = (1, 0)


    def line(self, x1, y1, x2, y2):
        start_x = min(x1, x2)
        stary_y = min(y1, y2)

        line_thinkness = 4
        offset = line_thinkness // 2

        start_x -= offset
        stary_y -= offset

        if x1 == x2:
            line_width = offset * 2
            line_height = offset + abs(y1 - y2) + offset

        elif y1 == y2:
            line_width = offset + abs(x1 - x2) + offset
            line_height = offset * 2
        display.rectangle(start_x, stary_y, line_width, line_height)


class Level:
    def __init__(self, level_number) -> None:
        self.load_level(level_number)


    def load_level(self, level_number) -> None:
        self.walls = []
        filename = f"level-{level_number}.txt"

        try:
            with open(filename, "r") as f:
                lines = f.readlines()
                for y, line in enumerate(lines):
                    for x, char in enumerate(line):
                        if char == '0' and 0 <= y < grid_h and 0 <= x < grid_w:
                            self.walls.append((x, y))
        except OSError:
            print(f"File not found: {filename}, using an empty level.")
        except Exception as e:
            print(f"Error loading level: {e}")


    def check_walls(self, position) -> bool:
        return position in self.walls


    def show(self) -> None:
        for wall in self.walls:
            x, y = wall
            display.set_pen(WALL_COLOR)
            display.rectangle(x * tile_size, y * tile_size, tile_size, tile_size)


class Food:
    def __init__(self, snake, level) -> None:
        self.reset_position(snake, level)


    def reset_position(self, snake, level) -> None:
        new_position = (randint(0, grid_w - 1), randint(0, grid_h - 1))

        while snake.contains(new_position) or level.check_walls(new_position):
            new_position = (randint(0, grid_w - 1), randint(0, grid_h - 1))

        self.position = new_position


    def show(self):
        x, y = self.position
        display.set_pen(FOOD_COLOR)
        display.rectangle(x * tile_size, y * tile_size, tile_size, tile_size)

        tile_x = (tile_size * x) + tile_size // 2
        tile_y = (tile_size * y) + tile_size // 2

        radius = (tile_size - 2) // 2
        display.set_pen(FOOD_COLOR)
        display.circle(tile_x, tile_y, radius)



class Game:
    def __init__(self, pad) -> None:
        self.pad = pad
        self.pressed = {}
        self.frameCount = 0
        self.score = 0
        self.target_score = 5
        self.base_refresh = 0.01

        self.countdown = 20
        self.cooldown = self.countdown
        self.slow, self.fast = 12, 2

        self.level_number = 0
        self.total_levels = 4
        self.state = State.TITLE


    def init_level(self) -> None:
        self.level = Level(self.level_number)
        self.snake = Snake()
        self.food = Food(self.snake, self.level)
        self.score = 0


    def tick(self) -> None:
        self.frame_skip = self.map_to_range(self.score, 0, 50, self.slow, self.fast)

        if self.frameCount % self.frame_skip == 0:
            self.update_inputs()
            self.draw_background()

            if self.state == State.PLAYING:
                self.draw_game_objects()

                self.snake.update_direction(self.pressed)
                new_head = self.snake.move()

                if new_head.position == self.food.position:
                    self.score += 1
                    self.snake.push(new_head)
                    self.food.reset_position(self.snake, self.level)

                elif self.snake.moving() and (self.level.check_walls(new_head.position) or self.snake.contains(new_head.position)):
                    self.cooldown = self.countdown
                    self.state = State.SCORE

                else:
                    self.snake.push(new_head)
                    self.snake.pop()
            else:
                self.cooldown -= 1
                self.show_game_text()
                if self.cooldown < 0:
                    self.cooldown = self.countdown

                    if self.state == State.TITLE:
                        self.lives_left = 3
                        self.state = State.LEVEL

                    elif self.state == State.LEVEL:
                        self.init_level()
                        self.state = State.LIVES

                    elif self.state == State.LIVES:
                        self.state = State.PLAYING

                    elif self.state == State.SCORE:
                        if self.score > self.target_score:
                            self.level_number += 1
                            self.level_number %= self.total_levels
                        else:
                            self.lives_left -= 1

                        if self.lives_left == 0:
                            self.state = State.GAME_OVER
                        else:
                            self.state = State.LEVEL

                    elif self.state == State.GAME_OVER:
                        self.state = State.TITLE

            presto.update()

        self.frameCount += 1
        utime.sleep(self.base_refresh)


    def map_to_range(self, value, min1, max1, min2, max2) -> int:
        if value < min1:
            return min2
        elif value > max1:
            return max2
        else:
            return min2 + int(((value - min1)//(max1 - min1)) * (max2 - min2))


    def update_inputs(self) -> None:
        button = self.pad.read_buttons()
        self.pressed['U'] = button['U']
        self.pressed['D'] = button['D']
        self.pressed['L'] = button['L']
        self.pressed['R'] = button['R']
        self.pressed['+'] = button['+']
        self.pressed['-'] = button['-']


    def draw_background(self) -> None:
        display.set_pen(BACKGROUND_COLOR)
        display.clear()


    def draw_game_objects(self) -> None:
        self.food.show()
        self.level.show()
        self.snake.show()


    def show_game_text(self) -> None:
        if self.state == State.TITLE:
            self.display_text("Presto", 20, 35, SCORE_COLOR)
            self.display_text_center("Snake", 20, TITLE_COLOR)

        elif self.state == State.LEVEL:
            self.display_text("Level", 20, 35, SCORE_COLOR)
            self.display_text(str(self.level_number), 20, 80, SCORE_COLOR)

        elif self.state == State.LIVES:
            self.display_text("Lives", 20, 35, SCORE_COLOR)
            self.display_text(str(self.lives_left), 20, 80, SCORE_COLOR)

        elif self.state == State.SCORE:
            self.display_text("Score", 20, 35, SCORE_COLOR)
            self.display_text(str(self.score), 20, 80, SCORE_COLOR)

        elif self.state == State.GAME_OVER:
            self.draw_game_objects()
            display.text("Game", 20, 35, SCORE_COLOR)
            display.text("Over", 20, 80, SCORE_COLOR)


    def display_text(self, text, x, y, pen) -> None:
        # text(text, x, y, angle=None, max_width=0, max_height=0)
        #display.clear()
        display.set_pen(pen)
        display.text(text, x, y)

    def display_text_center(self, text, y, pen) -> None:
        x = display.measure_text(text, 3)
        self.display_text(text, x, y, pen)


# Create the snake pit
game = Game(QwSTPad(i2c, I2C_ADDRESSES))

# Release the Snake!!!
while True:
    game.tick()
