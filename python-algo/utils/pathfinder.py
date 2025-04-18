import gamelib
from gamelib.game_map import WALL


def most_convenient_spawn_location(self, game_state, location_options, turret):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        path_lengths = []
        enemy_walls = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            path_length = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += (
                    len(game_state.get_attackers(path_location, 0))
                    * gamelib.GameUnit(turret, game_state.config).damage_i
                )

                # get number of walls alongside the path
                enemy_wall_amount += count_adjacent_enemy_walls(game_state, location)

                # add 1 to the path length
                path_length += 1

            damages.append(damage)
            path_lengths.append(path_length)
            enemy_walls.append(enemy_wall_amount)

        best_path_index = get_best_scoring_path_index(damages, path_lengths, enemy_walls)

        # Now just return the location that takes the least damage
        return location_options[best_path_index]

def count_adjacent_enemy_walls(game_state, path_location):
    """
    Count the amount of enemy walls next to a location (the more the worse)
    """
    adjacent_wall_count = 0

    # Get surrounding coordinates
    x, y = path_location
    neighbors = [
        (x + 1, y), (x - 1, y),
        (x, y + 1), (x, y - 1)
    ]
    # for each neighbouring square, check if there is an enemy wall
    # if so, increment!
    for neighbor in neighbors:
        if game_state.contains_stationary_unit(neighbor):
            unit = game_state.contains_stationary_unit(neighbor)[0]
            if unit.unit_type == WALL and unit.player_index == 1:  # 1 = enemy side
                adjacent_wall_count += 1

    return adjacent_wall_count


def get_best_scoring_path_index(damages, path_lengths, enemy_walls):
    # lowest score is best score so i gave the initial best score a rlly high number so it will get replaced immediately
    best_score = 10000000
    current_score = 0
    best_path_index = 0

    # run through the stats for all of the locations
    for i in range(damages.length):
        current_score = (0.5 * damages[i]) + (0.35 * path_lengths[i]) + (0.2 * enemy_walls[i])
        if current_score < best_score:
            best_score = current_score
            best_path_index = i

    return best_path_index





# LATER I wanna build something that keeps track of where we got scored on. I then want us to avoid that area