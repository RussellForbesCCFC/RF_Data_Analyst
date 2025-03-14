import numpy as np


def get_start_locations(row):
    elements = eval(row['location'])
    start_x = float(elements[0])
    start_y = float(elements[1])

    return start_x, start_y


def get_pass_end_locations(row):
    elements = eval(row['pass_end_location'])
    end_x = float(elements[0])
    end_y = float(elements[1])

    return end_x, end_y


def get_carry_end_locations(row):
    elements = eval(row['carry_end_location'])
    end_x = float(elements[0])
    end_y = float(elements[1])

    return end_x, end_y


def calculate_action_distance(row):
    """
    returns the distance of a pass or carry
    as well as the distance in % to goal
    :param row:
    :return: Distance of action in sb coordinates and %
    """

    action_start_location_x = row["location_x"]
    action_start_location_y = row["location_y"]

    action_end_location_x = row["end_location_x"]
    action_end_location_y = row["end_location_y"]

    goal_x = 120
    goal_y = 40

    x_distance_to_goal_at_start = abs(goal_x - action_start_location_x)
    y_distance_to_goal_at_start = abs(goal_y - action_start_location_y)

    x_distance_to_goal_at_end = abs(goal_x - action_end_location_x)
    y_distance_to_goal_at_end = abs(goal_y - action_end_location_y)

    distance_to_goal_at_start = np.sqrt(
        (x_distance_to_goal_at_start * x_distance_to_goal_at_start)
        + (y_distance_to_goal_at_start * y_distance_to_goal_at_start))

    distance_to_goal_at_end = np.sqrt(
        (x_distance_to_goal_at_end * x_distance_to_goal_at_end)
        + (y_distance_to_goal_at_end * y_distance_to_goal_at_end))

    action_distance = distance_to_goal_at_start - distance_to_goal_at_end
    action_distance_as_per_of_distance_at_start = round((action_distance / distance_to_goal_at_start) * 100, 1)

    return action_distance, action_distance_as_per_of_distance_at_start


def assign_zone_to_start_thirds(row):
    event_start_x = row["location_x"]
    event_start_y = row["location_y"]

    positional_x_range = [0, 18, 40, 60, 80, 102]
    positional_x_step = [18, 22, 20, 20, 22, 18.5]

    positional_y_range = [0, 18, 30, 50, 62]
    positional_y_step = [18, 12, 20, 12, 18.5]

    count = 0
    zone_list = []
    for n, x in enumerate(positional_x_range):
        for n_2, y in enumerate(positional_y_range):
            x_start = x
            x_step = positional_x_step[n]
            x_end = x + x_step

            y_start = y
            y_step = positional_y_step[n_2]
            y_end = y_start + y_step

            count += 1

            zone_dict = {"x_start": x_start, "x_end": x_end, "y_start": y_start, "y_end": y_end, "zone_name": count}
            zone_list.append(zone_dict)

    start_zone = []
    for z in zone_list:
        zone_start_x = z["x_start"]
        zone_end_x = z["x_end"]

        zone_start_y = z["y_start"]
        zone_end_y = z["y_end"]

        name = z["zone_name"]

        if (zone_start_x <= event_start_x < zone_end_x
                and zone_start_y <= event_start_y < zone_end_y):
            start_zone.append(name)

    return start_zone[0]


def assign_zone_to_pass_carry_shot_thirds(row):
    event_start_x = row["location_x"]
    event_start_y = row["location_y"]
    event_end_x = row["end_location_x"]
    event_end_y = row["end_location_y"]

    positional_x_range = [0, 18, 40, 60, 80, 102]
    positional_x_step = [18, 22, 20, 20, 22, 18.5]

    positional_y_range = [0, 18, 30, 50, 62]
    positional_y_step = [18, 12, 20, 12, 18.5]

    count = 0
    zone_list = []
    for n, x in enumerate(positional_x_range):
        for n_2, y in enumerate(positional_y_range):
            x_start = x
            x_step = positional_x_step[n]
            x_end = x + x_step

            y_start = y
            y_step = positional_y_step[n_2]
            y_end = y_start + y_step

            count += 1

            zone_dict = {"x_start": x_start, "x_end": x_end, "y_start": y_start, "y_end": y_end, "zone_name": count}
            zone_list.append(zone_dict)

    start_zone = []
    end_zone = []
    for z in zone_list:
        zone_start_x = z["x_start"]
        zone_end_x = z["x_end"]

        zone_start_y = z["y_start"]
        zone_end_y = z["y_end"]

        name = z["zone_name"]

        if (zone_start_x <= event_start_x < zone_end_x
                and zone_start_y <= event_start_y < zone_end_y):
            start_zone.append(name)

        if (zone_start_x <= event_end_x < zone_end_x
                and zone_start_y <= event_end_y < zone_end_y):
            end_zone.append(name)

    return start_zone[0], end_zone[0]


def add_position_to_pass_receiver(row, df):
    pass_receiver_id = row["pass_recipient_id"]
    pass_receiver_name = row["pass_recipient"]
    pass_index = row["index"]
    pass_match_id = row["match_id"]

    receiver_events_after_index = df[
        (df["index"] >= pass_index)
        & (df["player_id"] == pass_receiver_id)
        & (df["match_id"] == pass_match_id)]

    receiver_events_before_index = df[
        (df["index"] < pass_index)
        & (df["player_id"] == pass_receiver_id)
        & (df["match_id"] == pass_match_id)]

    count_of_receiver_events_post = receiver_events_after_index.shape[0]
    count_of_receiver_events_pre = receiver_events_before_index.shape[0]
    if count_of_receiver_events_post > 0:
        player_first_position = receiver_events_after_index["position"].iloc[0]
    elif count_of_receiver_events_pre > 0:
        player_first_position = receiver_events_before_index["position"].tail(1).iloc[0]
    else:
        player_first_position = None

    return player_first_position
