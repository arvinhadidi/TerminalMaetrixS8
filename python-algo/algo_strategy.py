import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from utils.pathfinder import most_convenient_spawn_location


class AlgoStrategy(gamelib.AlgoCore):
    attack_state = 0
    hole_area = [[[1, 13]], [[26, 13]]]
    stack_size = 8
    # booleans to track if we scored this or last round
    scored_last_round = False
    current_round_scored = False
    # lists to check holes that were last chosen
    last_chosen_hole = []
    chosen_hole = []

    left_side_triangle = [
        [3, 17],
        [2, 16],
        [3, 16],
        [1, 15],
        [2, 15],
        [3, 15],
        [0, 14],
        [1, 14],
        [2, 14],
        [3, 14],
    ]

    right_side_triangle = [
        [24, 17],
        [24, 16],
        [25, 16],
        [24, 15],
        [25, 15],
        [26, 15],
        [24, 14],
        [25, 14],
        [26, 14],
        [27, 14],
    ]

    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write("Random seed: {}".format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write("Configuring your custom algo strategy...")
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        Main place to control strategy
        """
        game_state = gamelib.GameState(self.config, turn_state)

        # shift variables forward
        self.scored_last_round = self.current_round_scored
        self.current_round_scored = False

        gamelib.debug_write(
            "Performing turn {} of your custom algo strategy".format(
                game_state.turn_number
            )
        )
        game_state.suppress_warnings(
            True
        )  # Comment or remove this line to enable warnings.

        if self.attack_state == 0 and self.check_if_attack_ready(
            game_state
        ):  # If enough mobile units are ready to attack in the NEXT turn
            self.attack_state = 1
            # self.chosen_hole = self.choose_weaker_side(
            #     game_state, self.left_side_triangle, self.right_side_triangle
            # )

            # choose a hole based on if we scored last round
            self.chosen_hole = self.choose_scored_on_side()
            game_state.attempt_remove(
                self.chosen_hole
            )  # The walls will remove NEXT TURN
        else:
            self.chosen_hole = []

        if self.attack_state == 1 and not any(
            list(map(game_state.contains_stationary_unit, self.chosen_hole))
        ):  # any[False, False, False] = False
            self.attack_state = 2

        if game_state.turn_number <= 2:
            self.stall_with_interceptors(game_state)

        self.build_structure(game_state)
        self.attack(game_state)
        self.upgrade_structure(game_state)

        # self.starter_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.

    """

    def clear_initial_defences(self, game_state):
        game_state.attempt_remove(
            [[4, 9], [3, 10], [2, 11], [1, 12], [26, 12], [25, 11], [24, 10], [23, 9]]
        )
        game_state.attempt_remove([[22, 11], [17, 11], [14, 11], [10, 11], [5, 11]])

    def check_if_attack_ready(self, game_state):
        return game_state.get_resource(MP) >= 14

    def build_structure(self, game_state):
        priority_turrets = []
        priority_turrets.extend([[0, 13], [27, 13], [1, 13], [26, 13], [2, 13], [25, 13]])

        if (
            self.attack_state == 1 or self.attack_state == 2
        ):  # If attempt_remove has been called, then don't build the chosen hole area
            for loc in self.chosen_hole:
                priority_turrets.remove(loc)

        game_state.attempt_spawn(TURRET, priority_turrets)

        walls = []

        walls.append([4, 12])
        walls.append([3, 13])
        walls.append([23, 12])
        walls.append([24, 13])
        walls.extend([[x, 11] for x in range(5, 23)])
        walls.extend([[7, 10], [11, 10], [16, 10], [20, 10]])

        turrets = []
        turrets.extend(
            [[3, 12], [4, 11], [24, 12], [23, 11]]
        )  # Left and right diagonal bits
        turrets.extend([[x, 13] for x in range(0, 4)])  # Left top side
        turrets.extend([[x, 13] for x in range(25, 28)])  # Right top side

        turrets.extend(
            [
                [5, 10],
                [6, 10],
                [8, 10],
                [9, 10],
                [10, 10],
                [12, 10],
                [13, 10],
                [14, 10],
                [15, 10],
                [17, 10],
                [18, 10],
                [19, 10],
                [21, 10],
                [22, 10],
            ]
        )  # Main line

        if (
            self.attack_state == 1 or self.attack_state == 2
        ):  # If attempt_remove has been called, then don't build the chosen hole area
            for loc in self.chosen_hole:
                turrets.remove(loc)

        support = []
        support.extend([[13, 8], [14, 8], [13, 9], [14, 9]])

        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_spawn(TURRET, turrets)
        game_state.attempt_spawn(SUPPORT, support)

    def upgrade_structure(self, game_state):
        walls = []

        walls.append([4, 12])
        walls.append([3, 13])
        walls.append([23, 12])
        walls.append([24, 13])
        walls.extend([[x, 11] for x in range(5, 23)])
        walls.extend([[7, 10], [11, 10], [16, 10], [20, 10]])

        turrets = []
        turrets.extend(
            [[3, 12], [4, 11], [24, 12], [23, 11]]
        )  # Left and right diagonal bits
        turrets.extend([[x, 13] for x in range(0, 4)])  # Left top side
        turrets.extend([[x, 13] for x in range(25, 28)])  # Right top side

        turrets.extend(
            [
                [5, 10],
                [6, 10],
                [8, 10],
                [9, 10],
                [10, 10],
                [12, 10],
                [13, 10],
                [14, 10],
                [15, 10],
                [17, 10],
                [18, 10],
                [19, 10],
                [21, 10],
                [22, 10],
            ]
        )  # Main line

        support = []
        support.extend([[13, 8], [14, 8], [13, 9], [14, 9]])

        game_state.attempt_upgrade(walls)
        game_state.attempt_upgrade(support)
        game_state.attempt_upgrade(turrets)

    def attack(self, game_state):

        if self.attack_state == 2:
            all_edge_coordinates = []
            massive_attack_spawn_locations = []

            bottom_left_edge = game_state.game_map.get_edge_locations(
                game_state.game_map.BOTTOM_LEFT
            )
            bottom_right_edge = game_state.game_map.get_edge_locations(
                game_state.game_map.BOTTOM_RIGHT
            )

            all_edge_coordinates.extend(bottom_left_edge)
            all_edge_coordinates.extend(bottom_right_edge)

            for location in all_edge_coordinates:
                if game_state.can_spawn(SCOUT, location) == False:
                    all_edge_coordinates.remove(location)
                else:
                    massive_attack_spawn_locations.append(location)

            picked_scout_location_spawn = self.least_damage_spawn_location(
                game_state, massive_attack_spawn_locations, "SCOUT"
            )

            # If some walls are detected, send as many demolishers
            # CAN CHANGE THE LIST OF POSSIBLE LOCATIONS FOR DEMOLISHER AND INTERCEPTOR
            picked_demolisher_location_spawn = self.least_damage_spawn_location(
                game_state, massive_attack_spawn_locations, "DEMOLISHER"
            )
            picked_interceptor_location_spawn = self.least_damage_spawn_location(
                game_state, massive_attack_spawn_locations, "INTERCEPTOR"
            )

            if self.chosen_hole == [[1, 13]]:
                demolisher_loc = [4, 9]
                interceptor_loc = [3, 10]
                scout_loc = [14, 0]

            else:
                demolisher_loc = [23, 9]
                interceptor_loc = [24, 10]
                scout_loc = [13, 0]

            # if (
            #     self.detect_enemy_unit(
            #         game_state, unit_type=None, valid_x=None, valid_y=[14, 15]
            #     )
            #     > 10
            # ):

            #     game_state.attempt_spawn(DEMOLISHER, demolisher_loc, 1000)

            # else:

            #     game_state.attempt_spawn(INTERCEPTOR, interceptor_loc, 5)
            # Initial one that might self destruct

            # New stuff
            if self.enemy_sides_full(
                game_state,
                self.chosen_hole,
                self.left_side_triangle,
                self.right_side_triangle,
            ):
                game_state.attempt_spawn(INTERCEPTOR, interceptor_loc, 5)
                game_state.attempt_spawn(SCOUT, scout_loc, 100)
            else:
                game_state.attempt_spawn(INTERCEPTOR, interceptor_loc, 5)
                game_state.attempt_spawn(SCOUT, scout_loc, 100)

            self.attack_state = 0  # Reset attack state

    def build_initial_defence(self, game_state):
        initial_turrets = [[22, 11], [17, 11], [14, 11], [10, 11], [5, 11]]
        initial_walls = [
            [0, 13],
            [1, 12],
            [2, 11],
            [3, 10],
            [4, 9],
            [27, 13],
            [26, 12],
            [25, 11],
            [24, 10],
            [23, 9],
        ]

        game_state.attempt_spawn(TURRET, initial_turrets)
        game_state.attempt_spawn(WALL, initial_walls)

    def clear_defences(self, game_state):
        for x in range(28):
            for y in range(14):
                loc = [x, y]
                # If there's a stationary unit, try to remove it
                if game_state.contains_stationary_unit(loc):
                    game_state.attempt_remove([loc])

    def starter_strategy(self, game_state):
        # First, place basic defenses

        # self.build_defences(game_state)

        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        if (
            self.detect_enemy_unit(
                game_state, unit_type=None, valid_x=None, valid_y=[14, 15]
            )
            > 10
        ):
            self.clear_defences(game_state)
            self.demolisher_line_strategy(game_state)
        else:
            # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

            self.clear_defences(game_state)
            self.build_defences(game_state)

            # Stacking
            stack_size = 10
            if game_state.get_resource(MP) >= stack_size:

                # Initialize an empty list to store all edge coordinates
                all_edge_coordinates = []
                massive_attack_spawn_locations = []

                bottom_left_edge = game_state.game_map.get_edge_locations(
                    game_state.game_map.BOTTOM_LEFT
                )
                bottom_right_edge = game_state.game_map.get_edge_locations(
                    game_state.game_map.BOTTOM_RIGHT
                )

                all_edge_coordinates.extend(bottom_left_edge)
                all_edge_coordinates.extend(bottom_right_edge)

                for location in all_edge_coordinates:
                    if game_state.can_spawn(SCOUT, location) == False:
                        all_edge_coordinates.remove(location)
                    else:
                        massive_attack_spawn_locations.append(location)

                # set to get location for a scout to spawn. change if needed.
                picked_location_spawn = self.least_damage_spawn_location(
                    game_state, massive_attack_spawn_locations, "SCOUT"
                )

                game_state.attempt_spawn(SCOUT, picked_location_spawn, stack_size)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            x, y = location
            # Turret cluster
            cluster_locs = [
                [x, y],
                [x, y + 1],
                [x + 1, y + 1],
                [x - 1, y + 1],
            ]
            for loc in cluster_locs:
                game_state.attempt_spawn(TURRET, loc)

            # Protecting walls in front
            wall_locs = [[x, y], [x + 1, y], [x - 1, y]]
            for loc in wall_locs:
                game_state.attempt_spawn(WALL, loc)

    def stall_with_interceptors(self, game_state):

        game_state.attempt_spawn(INTERCEPTOR, [21, 17])
        game_state.attempt_spawn(INTERCEPTOR, [10, 3])

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if (
                unit_class.cost[game_state.MP]
                < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]
            ):
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options, unit_type):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        # damages = []
        # # Get the damage estimate each path will take
        # for location in location_options:
        #     path = game_state.find_path_to_edge(location)
        #     damage = 0
        #     for path_location in path:
        #         # Get number of enemy turrets that can attack each location and multiply by turret damage
        #         damage += (
        #             len(game_state.get_attackers(path_location, 0))
        #             * gamelib.GameUnit(TURRET, game_state.config).damage_i
        #         )
        #     damages.append(damage)

        # # Now just return the location that takes the least damage
        return most_convenient_spawn_location(
            game_state, location_options, TURRET, WALL, unit_type
        )

    def enemy_sides_full(
        self, game_state, chosen_hole, left_side_triangle, right_side_triangle
    ):
        
        # PROBLEM IS HERE
        if not chosen_hole:
            return False
        
        x, _ = chosen_hole[0]
        if x == 1:
            coords = left_side_triangle
        elif x == 26:
            coords = right_side_triangle
        else:
            return False

        enemy_count = 0
        for loc in coords:
            t = tuple(loc)
            # only if that square actually has any stationary units
            if t in game_state.game_map:
                for unit in game_state.game_map[t]:
                    if unit.player_index == 1:
                        enemy_count += 1

        return enemy_count > 4

    def strength_score_at_locations(self, game_state, locations):
        weights = {SUPPORT: 1.2, WALL: 0.5, TURRET: 2.0}
        counts = {SUPPORT: 0, WALL: 0, TURRET: 0}

        for loc in locations:
            t = tuple(loc)
            if t in game_state.game_map:
                for unit in game_state.game_map[t]:
                    if unit.player_index == 1 and unit.unit_type in counts:
                        counts[unit.unit_type] += 1

        return (
            counts[SUPPORT] * weights[SUPPORT]
            + counts[WALL] * weights[WALL]
            + counts[TURRET] * weights[TURRET]
        )

    def choose_weaker_side(self, game_state, left_side_triangle, right_side_triangle):
        # Pick side which is weaker
        # Currently returns hard-coded values
        if self.strength_score_at_locations(
            game_state, left_side_triangle
        ) < self.strength_score_at_locations(game_state, right_side_triangle):

            return [[1, 13]]

        else:

            return [[26, 13]]
        
    def choose_scored_on_side(self):

        if self.scored_last_round and self.last_chosen_hole != []:
            self.chosen_hole = self.last_chosen_hole
        else:
            # Otherwise pick the opposite hole
            # (hole_area is [ [[1,13]], [[26,13]] ])
            if self.last_chosen_hole == self.hole_area[0]:
                self.chosen_hole = self.hole_area[1]
            else:
                self.chosen_hole = self.hole_area[0]

        # Remember for next time
        self.last_chosen_hole = self.chosen_hole

        return self.chosen_hole

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if (
                        unit.player_index == 1
                        and (unit_type is None or unit.unit_type == unit_type)
                        and (valid_x is None or location[0] in valid_x)
                        and (valid_y is None or location[1] in valid_y)
                    ):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]

        # Flag to track if we did any damage this round
        # damage_done_this_round = False
        # mobile_units_sent = False

        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if unit_owner_self:
                self.current_round_scored = True

            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write(
                    "All locations: {}".format(self.scored_on_locations)
                )


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
