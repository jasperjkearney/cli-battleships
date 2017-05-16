import random
import numpy as np


class Ship:
    def __init__(self, length, start, direction):
        """
        Args:
            - length: The length of the ship.
            - start: Coordinate of the rearmost ship section as a 2-element tuple.
            - direction: Orientation of the ship, given as 'N', 'E', 'S', or 'W'.
        """
        ship_varieties = {2: 'Destroyer', 3: 'Submarine', 4: 'Battleship', 5: 'Aircraft Carrier'}

        self._length = length
        self.variety = ship_varieties[length]
        self.condition = length

        direction_vectors = {'N': (-1, 0),
                             'S': (1, 0),
                             'E': (0, 1),
                             'W': (0, -1)}
        direction_vector = direction_vectors[direction]

        self._points = [(start[0] + i*direction_vector[0], start[1] + i*direction_vector[1])
                        for i in range(length)]

        self.endpoint = self._points[-1]

    def __iter__(self):
        return iter(self._points)

    def __len__(self):
        return self._length

    def damage(self):
        self.condition -= 1

    def sunk(self):
        return not bool(self.condition)


class Board:
    def __init__(self, n):
        # The board attribute contains an n x n numpy array representing the game board
        # Each square of the board has a different value:
        # 0 = sea,  1 = un-hit ship section, 2 = hit ship section, 3 = previous miss
        self._n = n
        self._board = np.zeros((self._n, self._n), dtype=np.int)

        # The ships attribute contains a list of Ship objects.
        self.ships = list()

        # The previous_hits variable stores all coordinates where the AI hit a player's ship, this is so that further
        # shots can target a similar area.
        # When a ship is sunk, it's coordinates are removed from the list, this is so that the AI does not continue to
        # fire near ships that are already sunk.
        self._previous_hits = list()

    def to_string(self, symbols=None):
        """ Returns a string representation of the board.
        Args:
            - symbols: A dictionary mapping board square values to symbols. """

        if not symbols:
            symbols = {0: '_',  # Sea
                       1: '#',  # Un-hit ship section
                       2: 'X',  # Hit ship section
                       3: 'O'}  # Previous miss

        result = []
        result.append('  ' + '_ '*self._n)
        for row_name, row in zip(ROWS, self._board):
            result.append(row_name + '|' + '|'.join([symbols[x] for x in row]) + '|')
        result.append('  ' + ' '.join(COLS))
        return '\n'.join(result) + '\n'

    def __str__(self):
        """ Returns a string representation of the board. """
        return self.to_string()

    def with_hidden_ships(self):
        """ Returns a string representation of the board with the location of the ships obscured."""
        symbols = {0: '~',  # Sea
                   1: '~',  # Un-hit ship section
                   2: 'X',  # Hit ship section
                   3: 'O'}  # Previous miss

        return self.to_string(symbols=symbols)

    def is_valid_placement(self, ship):
        """ Checks the attributes of a Ship object to see if it can fit on the board.
        Args:
           - ship: A Ship object.

        Returns:
            bool: Returns True if the Ship object can fit on the board.
        """
        return (all(i in range(self._n) for i in ship.endpoint)  # Check to see that the ship does not end out of bounds
                and all(self._board[point] != 1 for point in ship))  # Check for intersection with other ships

    def place_ship(self, ship):
        """ Places a ship on the board by adding a Ship object to the Board object.
        Args:
           - ship: A Ship object.
        """
        self.ships.append(ship)

        for point in ship:
            self._board[point] = 1

    def initialise_ships_with_inputs(self, ship_lengths):
        """ Places a player's ships on the board by using user inputs.
        Args:
            - ship_lengths: A list of ship lengths, representing player's allocation of ships.
        """
        print(self)

        for ship_length in ship_lengths:
            ship_variety = Ship(ship_length, (-1, -1), 'N').variety
            print('Now placing {} of length {}.'.format(ship_variety, ship_length))
            print('Specify start point and direction for ship.\n')

            while True:  # Until the ship is placed in a valid location.
                start_coordinate = get_coordinate_input()
                direction = get_direction_input()
                ship = Ship(ship_length, start_coordinate, direction)

                if self.is_valid_placement(ship):
                    break

                print('''\nInvalid placement. Ship would intersect other ships or be out of bounds; try again. \n''')

            self.place_ship(ship)
            print(self)
            input('{} placed, press enter to continue.\n'.format(ship_variety))

    def initialise_ships_randomly(self, ship_lengths):
        """ Randomly places the ship allocation on the board.
        Args:
            - ship_lengths: A list of ship lengths, representing player's allocation of ships.
        """
        for ship_length in ship_lengths:
            while True:
                start_coordinate = tuple(random.randint(0, self._n - 1) for _ in range(2))
                direction = random.choice(['N', 'E', 'S', 'W'])

                ship = Ship(ship_length, start_coordinate, direction)

                if self.is_valid_placement(ship):
                    break
            self.place_ship(ship)

    def is_hit(self, coordinate):
        """ Checks if a shot will hit.
         Args:
             - coordinate: The target coordinate as a 2-element tuple
         Returns:
            - bool: True if shot will hit
        """
        return self._board[coordinate] == 1

    def vertical_neighbours(self, coordinate):
        """ Returns the directly vertical neighbours of a coordinate, if they are on the board.
         Args:
             - coordinate: Coordinate as a 2-element tuple
         Returns:
            - list: List of 2-element tuples
        """
        row, col = coordinate
        return [(row + dy, col) for dy in [1, -1] if row + dy in range(self._n)]

    def horizontal_neighbours(self, coordinate):
        """ Returns the directly horizontal neighbours of a coordinate, if they are on the board.
         Args:
             - coordinate: Coordinate as a 2-element tuple
         Returns:
            - list: List of 2-element tuples
        """
        row, col = coordinate
        return [(row, col + dx) for dx in [1, -1] if col + dx in range(self._n)]

    def all_neighbours(self, coordinate):
        """ Returns the direct neighbours of a coordinate, if they are on the board.
         Args:
             - coordinate: Coordinate as a 2-element tuple
         Returns:
            - list: List of 2-element tuples
        """
        return self.vertical_neighbours(coordinate) + self.horizontal_neighbours(coordinate)

    def can_contain_ship(self, coordinate):
        """ Checks if it is possible for a ship be present at a specified coordinate.
         Args:
             - coordinate: Coordinate as a 2-element tuple
         Returns:
             - bool: True if the coordinate could contain a ship.
         """
        # Find the maximum possible length of ship that could be at the coordinate:
        row, col = coordinate
        dx, dy = (1, 1)
        max_x_len, max_y_len = (1, 1)

        while col+dx in range(self._n) and self._board[(row, col+dx)] < 3:
            dx += 1
            max_x_len += 1
        dx = 1
        while col-dx in range(self._n) and self._board[(row, col-dx)] < 3:
            dx += 1
            max_x_len += 1

        while row+dy in range(self._n) and self._board[(row+dy, col)] < 3:
            dy += 1
            max_y_len += 1
        dy = 1
        while row-dy in range(self._n) and self._board[(row-dy, col)] < 3:
            dy += 1
            max_y_len += 1

        max_possible_len = max(max_x_len, max_y_len)

        # Find the smallest remaining ship:
        smallest_ship = min(self.ships, key=lambda s: len(s))

        return (self._board[coordinate] < 2  # Check that the coordinate has not already been fired on
                and len(smallest_ship) <= max_possible_len)  # Check that one of the remaining ships could fit here

    def apply_shot(self, coordinate):
        """ Handles a shot being made at the board, prints feedback.
        Args:
             - coordinate: Coordinate as a 2-element tuple
        """
        # If there is a ship at the location, mark a hit, update Ship object.
        if self._board[coordinate] == 1:
            print('Hit!')
            self._board[coordinate] = 2
            self._previous_hits.append(coordinate)

            for ship in self.ships:
                if target_coordinate in ship:
                    ship.damage()
                    if ship.sunk():
                        print('{} sunk!'.format(ship.variety))
                        self.ships.remove(ship)
                        for point in ship:
                            self._previous_hits.remove(point)

        else:  # self.board[coordinate] != 1:
            print('Miss.')
            if self._board[coordinate] == 0:
                self._board[coordinate] = 3

    def generate_targets(self):
        """ This is the key to the AI of the computer player, the function returns a list of the coordinates on the
        board most likely to contain ships, using only information derived from the result of previous shots.
        Returns:
            - list: List of 2-element tuples representing viable targets.
        """
        possible_targets = list()

        # Of primary interest are adjacent previous hits, normally indicating a ship.
        # Consider target coordinates that lie on the line formed by the adjacent hits.
        if adjacent_coordinates_in(self._previous_hits):
            for coord_pair in adjacent_coordinates_in(self._previous_hits):
                coord1, coord2 = coord_pair
                if coord1[0] - coord2[0]:  # The coordinates are vertically adjacent.
                    possible_targets += (self.vertical_neighbours(coord1) +
                                         self.vertical_neighbours(coord2))
                else:  # The coordinates are horizontally adjacent.
                    possible_targets += (self.horizontal_neighbours(coord1) +
                                         self.horizontal_neighbours(coord2))
                # Coordinates that cannot contain ships are removed:
                possible_targets = [coord for coord in possible_targets if self.can_contain_ship(coord)]

        if possible_targets:
            return possible_targets

        # If no target coordinates have been identified yet, target all neighbours of the previous hits:
        for previous_hit in self._previous_hits:
            possible_targets += self.all_neighbours(previous_hit)
            # Coordinates that cannot contain ships are removed.
            possible_targets = [coord for coord in possible_targets if self.can_contain_ship(coord)]

        if possible_targets:
            return possible_targets

        # If there are still no identified target coordinates, return all coordinates that could contain a ship.
        return [(row, col) for row in range(self._n) for col in range(self._n) if self.can_contain_ship((row, col))]


def is_valid_coordinate_string(coord_string):
    """ Checks if a coordinate string is valid, valid strings include: A1, b10 etc.
    Args:
        - coord_string: A coordinate as a string.
    Returns:
        - bool: True if coordinate string is valid.
    """
    if len(coord_string) < 2:
        print('Invalid input')
        return False

    validity = True  # Let's be optimistic

    row = coord_string[0]
    col = coord_string[1:]

    if row.upper() not in ROWS:
        print('Invalid row: "{}"'.format(row))
        validity = False
    if col not in COLS:
        print('Invalid column "{}"'.format(col))
        validity = False

    return validity


def get_coordinate_input():
    """ Gets a coordinate from user input.
    Returns:
        - tuple: Coordinate as a 2-element tuple.
    """
    while True:
        raw_coord = input('Enter coordinate in the form "A1": ')

        if is_valid_coordinate_string(raw_coord):
            return ord(raw_coord[0].upper()) - ord('A'), int(raw_coord[1:]) - 1


def get_direction_input():
    """ Gets a compass direction from user input.
    Returns:
        - string: 'N', 'E', 'S' or 'W'.
    """
    while True:
        direction = input('Enter direction (NESW): ')
        if direction.upper() in ['N', 'E', 'S', 'W']:
            return direction.upper()
        print('Invalid direction "{}"'.format(direction))


def adjacent_coordinates_in(coordinates):
    """ Given a list of coordinates, returns a list of tuples containing pairs of coordinates in the original list which
    are directly adjacent to one another.
    Args:
        - coordinates: A list of coordinates as 2-element tuples.
    Returns:
        - list: List of 2 element-tuples containing 2-element tuples of adjacent coordinates.
    Examples:
        >>> adjacent_coordinates_in([(0, 0), (0, 1), (1, 0)])
        [((0, 1), (0, 0)), ((1, 0), (0, 0))]
    """
    return [(coord1, coord2) for coord1 in coordinates for coord2 in coordinates
            if (coord1[0]-coord2[0] == 1 and coord1[1]-coord2[1] == 0)
            or (coord1[0]-coord2[0] == 0 and coord1[1]-coord2[1] == 1)]


if __name__ == '__main__':

    print("""
                                         |__
                                         |\/
                                         ---
                                         / | [
                                  !      | |||
                                _/|     _/|-++'
                            +  +--|    |--|--|_ |-
                         { /|__|  |/\__|  |--- |||__/
                        +---------------___[}-_===_.'____                 /\\
                    ____`-' ||___-{]_| _[}-  |     |_[___\==--            \/   _
     __..._____--==/___]_|__|_____________________________[___\==--____,------' .7
    |                                                                          /
     \_________________________________________________________________________|

     """)
    print('\n')
    input('Starting new game of battleships. Press enter to continue. \n')

    # ----- Define constants -----
    SHIP_CONTINGENT = (2, 3, 3, 4, 5)  # Lengths of the ships that are allocated to player and computer

    # Row and column names.
    N = 10  # Boards are n x n grids
    COLS = [str(x + 1) for x in range(N)]
    ROWS = [chr(x + ord('A')) for x in range(N)]

    # ----- Create player and computer boards -----
    player_board = Board(N)
    computer_board = Board(N)

    # ----- Place player and computer ships -----

    while True:
        choice = input('Would you like your ships to be randomly placed for you? (Y/N)\n').upper()
        if not len(choice) or choice[0] not in ['Y', 'N']:
            pass
        elif choice[0] == 'Y':
            player_board.initialise_ships_randomly(SHIP_CONTINGENT)
            break
        elif choice[0] == 'N':
            player_board.initialise_ships_with_inputs(SHIP_CONTINGENT)
            break

    computer_board.initialise_ships_randomly(SHIP_CONTINGENT)

    # ----- Decide turn order -----

    print('All ships placed. A coin will be flipped to determine turn order. \n')
    while True:
        c = (input('Enter heads or tails: ') + '_').strip()[0].upper()
        if c in ['H', 'T']:
            break
    print('Flipping coin...')
    is_player_turn = bool(random.randint(0, 1))
    if is_player_turn:
        print('Correct - You move first')
    else:
        print('Incorrect - Computer moves first.')

    # ----- Begin main loop. -----

    while player_board.ships and computer_board.ships:

        if is_player_turn:
            input('Your turn, press enter to continue.')
            print(computer_board.with_hidden_ships())
            target_coordinate = get_coordinate_input()

            input('Firing on {}{}! Press enter to continue.'.format(ROWS[target_coordinate[0]],
                                                                    COLS[target_coordinate[1]]))

            is_player_turn = computer_board.is_hit(target_coordinate)
            # Update the board.
            computer_board.apply_shot(target_coordinate)

        else:  # It is the computer's turn
            input("Computer's turn, press enter to continue.")
            print(player_board)
            print('Thinking...')

            # Make a list of coordinates likely to contain ships.
            target_coordinates = player_board.generate_targets()
            # Pick one at random.
            target_coordinate = random.choice(target_coordinates)

            input('Incoming at {}{}! Press enter to continue.'.format(ROWS[target_coordinate[0]],
                                                                      COLS[target_coordinate[1]]))

            is_player_turn = not player_board.is_hit(target_coordinate)
            # Update the board.
            player_board.apply_shot(target_coordinate)

    # Loop exits in the case of no player ships or no computer ships.
    if player_board.ships:
        input('You win!')
    else:
        input('You lose.')
