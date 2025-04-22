import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from utils.pathfinder import most_convenient_spawn_location


class AlgoStrategy(gamelib.AlgoCore):
    attack_state = 0
    hole_area = [[[10, 8]]] # CHANGED TO ONE SQUARE ONLY
    chosen_hole = []
    stack_size = 8

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
            self.chosen_hole = random.choice(self.hole_area)
            game_state.attempt_remove(
                self.chosen_hole
            )  # The walls will remove NEXT TURN

        if self.attack_state == 1 and not any(
            list(map(game_state.contains_stationary_unit, self.chosen_hole))
        ):  # any[False, False, False] = False
            self.attack_state = 2

        # if game_state.turn_number <= 3:
        #     self.stall_with_interceptors(game_state)

        if game_state.turn_number > 2:
            self.build_structure(game_state)
            self.attack(game_state)
            self.upgrade_structure(game_state)
        else:
            self.starter_strategy(game_state)

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
        walls = []
        walls.extend([[2, 11], [3, 10], [4, 9]])  # Left top side, 3 SP
        walls.extend([[x, 8] for x in range(5, 18)])  # Flat part, 13 SP
        walls.extend([[18, 9], [19, 10], [20, 11], [20, 12], [22, 9]]) # Right side, 5 SP

        # idk how this code is gonna be now. I wanna keep it tho!
        # COMMENTED OUT HOLE OPEN/CLOSE BC IT WAS CAUSING ERRORS


        if (
            self.attack_state == 1 or self.attack_state == 2
        ):  # If attempt_remove has been called, then don't build the chosen hole area
            for loc in self.chosen_hole:
                walls.remove(loc)

        turrets = []
        turrets.extend([[0, 13], [1, 13], [1, 12]])  # Left diagonal bits, 6 SP
        turrets.extend([
            [27, 13],
            [26, 13],
            [25, 13],
            [24, 12],
            [23, 11],
            [22, 11],
            [20, 10]
        ])  # RHS, 14 SP

        support = []
        support.extend([[22, 8], [23, 9]]) # 8 SP

        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_spawn(TURRET, turrets)
        game_state.attempt_spawn(SUPPORT, support)

    def upgrade_structure(self, game_state):
        walls = []
        walls.extend([[21, 13], [22, 13]]) # 2 SP

        turrets = []
        turrets.extend([[9, 8], [11, 8]])  # Left and right bits, 6 SP
        turrets.extend([[24, 13], [2, 13], [2, 12]])  # Left and right bits, 6 SP

        support = []
        support.extend([[19, 8], [19, 7], [18, 8], [9, 7], [11, 7]]) # 20 SP

        for x in range(18, 14, -1):  # 18 to 15 inclusive
            for y in range(7, 4, -1):  # 7 to 5 inclusive
                support.append([x, y])

        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_spawn(TURRET, turrets)
        game_state.attempt_spawn(SUPPORT, support)

    def attack(self, game_state):

        if self.attack_state == 2:
            all_edge_coordinates = []
            massive_attack_spawn_locations = [[24, 10], [14, 0]]

            # bottom_left_edge = game_state.game_map.get_edge_locations(
            #     game_state.game_map.BOTTOM_LEFT
            # )
            # bottom_right_edge = game_state.game_map.get_edge_locations(
            #     game_state.game_map.BOTTOM_RIGHT
            # )

            # all_edge_coordinates.extend(bottom_left_edge)
            # all_edge_coordinates.extend(bottom_right_edge)

            # for location in all_edge_coordinates:
            #     if game_state.can_spawn(SCOUT, location) == False:
            #         all_edge_coordinates.remove(location)
            #     else:
            #         massive_attack_spawn_locations.append(location)

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

            if (
                self.detect_enemy_unit(
                    game_state, unit_type=None, valid_x=None, valid_y=[14, 15]
                )
                > 10
            ):
                game_state.attempt_spawn(
                    DEMOLISHER, [picked_demolisher_location_spawn], 4
                )
                game_state.attempt_spawn(
                    INTERCEPTOR, [picked_interceptor_location_spawn], 2
                )
            else:
                game_state.attempt_spawn(
                    SCOUT, picked_scout_location_spawn, 6
                )  # Initial one that might self destruct
                game_state.attempt_spawn(
                    INTERCEPTOR, [picked_demolisher_location_spawn], 3
                )
                friendly_edges = game_state.game_map.get_edge_locations(
                    game_state.game_map.BOTTOM_LEFT
                ) + game_state.game_map.get_edge_locations(
                    game_state.game_map.BOTTOM_RIGHT
                )

                deploy_locations = self.filter_blocked_locations(
                    friendly_edges, game_state
                )
                chosen = random.choice(deploy_locations)

                game_state.attempt_spawn(SCOUT, chosen, 5)  # Second smaller stack

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

        # Stacking
        stack_size = 3
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
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        friendly_edges = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT
        ) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        random.shuffle(deploy_locations)

        # If we have remaining MP to spend on THREE interceptors, do it

        for i in range(0, min(len(deploy_locations), 1000)):
            game_state.attempt_spawn(INTERCEPTOR, deploy_locations[i])

            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

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
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write(
                    "All locations: {}".format(self.scored_on_locations)
                )


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
