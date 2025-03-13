import pandas as pd
import numpy as np
from datetime import timedelta

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import get_start_locations, get_carry_end_locations, get_pass_end_locations, \
    calculate_action_distance


def ball_receipts_under_pressure_next_action_outcome(row, all_events_df):
    """
    returns the outcome of the player next action after receiving the ball under pressure
    :param all_events_df:
    :param row:
    :return: Successful / Unsuccessful
    """
    player_id = row["player_id"]
    player = row["player"]
    action_type = row["type"]
    timestamp = row["timestamp"]
    possession = row["possession"]
    period = row["period"]
    match_id = row["match_id"]

    # the timestamp needs to be the same or higher as if the player passes on their first touch
    # the timestamp will be the same as the receipt
    player_first_next_action = all_events_df[
        (all_events_df["match_id"] == match_id)
        & (all_events_df["possession"] == possession)
        & (all_events_df["period"] == period)
        & (all_events_df["timestamp"] >= timestamp)
        & (all_events_df["player_id"] == player_id)
        & (all_events_df["type"] != "Ball Receipt*")].sort_values("index", ascending=True).iloc[0]

    first_action_type = player_first_next_action["type"]

    if first_action_type == "Pass":
        pass_outcome = player_first_next_action["pass_outcome"]
        if pass_outcome not in ["Incomplete", "Out", "Unknown", "Pass Offside", "Injury Clearance"]:
            first_action_outcome = "Successful"
        elif pass_outcome in ["Pass Offside", "Injury Clearance"]:
            first_action_outcome = "Exclude"
        else:
            first_action_outcome = "Unsuccessful"

    elif first_action_type in ["Miscontrol", "Dispossessed"]:
        first_action_outcome = "Unsuccessful"
    elif first_action_type == "Carry":
        try:
            player_action_after_carry = all_events_df[
                (all_events_df["match_id"] == match_id)
                & (all_events_df["possession"] == possession)
                & (all_events_df["period"] == period)
                & (all_events_df["timestamp"] >= timestamp)
                & (all_events_df["player_id"] == player_id)
                & (all_events_df["type"] != "Ball Receipt*")].sort_values("index", ascending=True).iloc[1]

            player_action_after_carry_type = player_action_after_carry["type"]
            if player_action_after_carry_type == "Pass":
                pass_outcome_after_carry = player_action_after_carry["pass_outcome"]
                if pass_outcome_after_carry not in ["Incomplete", "Out", "Unknown", "Pass Offside", "Injury Clearance"]:
                    first_action_outcome = "Successful"
                elif pass_outcome_after_carry in ["Pass Offside", "Injury Clearance"]:
                    first_action_outcome = "Exclude"
                else:
                    first_action_outcome = "Unsuccessful"

            elif player_action_after_carry_type in ["Miscontrol", "Dispossessed"]:
                first_action_outcome = "Unsuccessful"
            elif player_action_after_carry_type in ["Foul Won", "Shot"]:
                first_action_outcome = "Successful"
            elif player_action_after_carry_type in ["Dribble"]:
                dribble_outcome_after_carry = player_action_after_carry["dribble_outcome"]
                if dribble_outcome_after_carry == "Complete":
                    first_action_outcome = "Successful"
                else:
                    first_action_outcome = "Unsuccessful"
            else:
                first_action_outcome = "Exclude"

        except IndexError:
            first_action_outcome = "Exclude"

    elif first_action_type in ["Shot", "Foul Won"]:  # other options are shot a
        first_action_outcome = "Successful"
    else:
        first_action_outcome = "Exclude"

    return first_action_outcome


def create_player_data_by_position():
    """
    Creates the player aggregated performance data by position and exports to a csv file in b_aggregated_data
    :return: a dataframe containing player performance data by wider position group
    """

    # read and combine raw data
    euro_events_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/a_raw_data/euro_2024_task_data.csv",
        low_memory=False)
    euro_events_df["competition_name"] = "Euro 2024"

    copa_events_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/a_raw_data/copa_2024_task_data.csv",
        low_memory=False)
    copa_events_df["competition_name"] = "Copa 2024"

    player_events_df = pd.concat([euro_events_df, copa_events_df], ignore_index=True)

    # print(player_events_df["type"].value_counts().to_string())
    # remove events where the position is substitute - all players on the bench getting cards
    # filter to only player events
    player_events_df = player_events_df[
        (player_events_df["position"] != "Substitute")
        & ~(player_events_df["player"].isnull())
        & (player_events_df["period"] != 5)]

    player_events_df["position_group"] = player_events_df["position"].apply(
        lambda x: position_groups[x])

    # create player metric totals
    metric_group_by_list = ["player_id", "player", "team", "position_group", "competition_name"]
    # BALL RECEIPTS UNDER PRESSURE -------------------------------------------------------------------------------------
    ball_receipts_under_pressure = player_events_df[
        (player_events_df["type"] == "Ball Receipt*")
        & (player_events_df["under_pressure"] == True)
        & (player_events_df["ball_receipt_outcome"].isnull())].copy()

    ball_receipts_under_pressure["next_action_outcome"] = ball_receipts_under_pressure.apply(
        lambda row: ball_receipts_under_pressure_next_action_outcome(row, player_events_df), axis=1)

    ball_lost_under_pressure = ball_receipts_under_pressure[
        (ball_receipts_under_pressure["next_action_outcome"] == "Unsuccessful")].groupby(
        metric_group_by_list)[
        "id"].count().rename("ball_lost_under_pressure")

    ball_retained_under_pressure = ball_receipts_under_pressure[
        (ball_receipts_under_pressure["next_action_outcome"] == "Successful")].groupby(
        metric_group_by_list)[
        "id"].count().rename("ball_retained_under_pressure")

    # SHOOTING AND xG --------------------------------------------------------------------------------------------
    total_obv = player_events_df.groupby(
        metric_group_by_list)["obv_total_net"].sum().rename("total_obv_net")

    total_np_shots = player_events_df[
        (player_events_df["type"] == "Shot")
        & (player_events_df["shot_type"] != "Penalty")].groupby(
        metric_group_by_list)[
        "id"].count().rename("total_np_shots")

    total_np_goals = player_events_df[
        (player_events_df["type"] == "Shot")
        & (player_events_df["shot_outcome"] == "Goal")
        & (player_events_df["shot_type"] != "Penalty")].groupby(
        metric_group_by_list)["id"].count().rename(
        "total_np_goals")

    total_np_xg = player_events_df[
        (player_events_df["type"] == "Shot")
        & (player_events_df["shot_type"] != "Penalty")].groupby(
        metric_group_by_list)[
        "shot_statsbomb_xg"].sum().rename("total_np_xg")

    np_shots_on_target = player_events_df[
        (player_events_df["type"] == "Shot") & (player_events_df["shot_type"] != "Penalty")
        & (player_events_df["shot_outcome"].isin(["Saved", "Goal", "Saved to Post"]))].groupby(
        metric_group_by_list)["id"].count().rename(
        "np_on_target_shots")

    # CARRIES AND DRIBBLES =--------------------------------------------------------------------------------------------
    total_dribbles = player_events_df[
        (player_events_df["type"] == "Dribble")].groupby(
        metric_group_by_list)["id"].count().rename(
        "total_dribbles")

    complete_dribbles = player_events_df[
        (player_events_df["type"] == "Dribble")
        & (player_events_df["dribble_outcome"] == "Complete")].groupby(
        metric_group_by_list)[
        "id"].count().rename("completed_dribbles")

    dribble_carry_obv = player_events_df[
        (player_events_df["type"].isin(["Dribble", "Carry"]))].groupby(
        metric_group_by_list)[
        "obv_total_net"].sum().rename(
        "total_dribble_carry_obv")

    player_carry_events = player_events_df[(player_events_df["type"] == "Carry")].copy()

    player_carry_events[['location_x', 'location_y']] = player_carry_events.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    player_carry_events[['end_location_x', 'end_location_y']] = player_carry_events.apply(
        lambda row_: pd.Series(get_carry_end_locations(row_)), axis=1)

    player_carry_events[
        ['action_distance_towards_goal', 'action_distance_towards_goal_as_per']] = player_carry_events.apply(
        lambda row: pd.Series(calculate_action_distance(row)), axis=1)

    carries_into_final_third = player_carry_events[
        (player_carry_events["location_x"] < 80)
        & (player_carry_events["end_location_x"] >= 80)].groupby(
        metric_group_by_list)[
        "id"].count().rename("carries_into_final_third")

    carry_distance = player_carry_events.groupby(
        metric_group_by_list)["action_distance_towards_goal"].sum().rename(
        "carry_distance")

    carry_distance_from_own_half = player_carry_events[
        (player_carry_events["location_x"] <= 60)].groupby(
        metric_group_by_list)["action_distance_towards_goal"].sum().rename(
        "carry_distance_from_own_half")

    progressive_carries = player_carry_events[
        (player_carry_events["action_distance_towards_goal_as_per"] >= 10)
        & (player_carry_events["action_distance_towards_goal"] >= 5)].groupby(
        metric_group_by_list)[
        "id"].count().rename("progressive_carries")

    progressive_carries_from_own_half = player_carry_events[
        (player_carry_events["action_distance_towards_goal_as_per"] >= 10)
        & (player_carry_events["action_distance_towards_goal"] >= 5)
        & (player_carry_events["location_x"] <= 60)].groupby(
        metric_group_by_list)[
        "id"].count().rename("progressive_carries_from_own_half")

    carry_obv_from_own_half = player_carry_events[
        (player_carry_events["location_x"] <= 60)].groupby(
        metric_group_by_list)["obv_total_net"].sum().rename(
        "carry_obv_from_own_half")

    # PASSES ---------------------------------------------------------------------------------------------------------
    total_passes = player_events_df[
        (player_events_df["type"] == "Pass") & (player_events_df["pass_outcome"] != "Pass Offside")].groupby(
        metric_group_by_list)[
        "id"].count().rename("total_passes")

    total_op_passes = player_events_df[
        (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Pass Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Kick Off", "Goal Kick", "Throw-in"]))].groupby(
        metric_group_by_list)[
        "id"].count().rename(
        "open_play_total_passes")

    total_passes_completed = player_events_df[
        (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"].isnull())].groupby(
        metric_group_by_list)["id"].count().rename(
        "completed_passes")

    expected_passes_completed = player_events_df[
        (player_events_df["type"] == "Pass")].groupby(
        metric_group_by_list)["pass_pass_success_probability"].sum().rename(
        "expected_completed_passes")

    total_key_passes = player_events_df[
        (player_events_df["type"] == "Pass")
        & ((player_events_df["pass_shot_assist"] == True) | (player_events_df["pass_goal_assist"] == True))].groupby(
        metric_group_by_list)[
        "id"].count().rename(
        "key_passes")

    open_play_key_passes = player_events_df[
        (player_events_df["type"] == "Pass") & ~(
            player_events_df["pass_type"].isin(["Corner", "Free Kick", "Kick Off", "Goal Kick", "Throw-in"]))
        & ((player_events_df["pass_shot_assist"] == True)
           | (player_events_df["pass_goal_assist"] == True))].groupby(
        metric_group_by_list)[
        "id"].count().rename(
        "open_play_key_passes")

    player_pass_events = player_events_df[(player_events_df["type"] == "Pass")].copy()

    player_pass_events[['location_x', 'location_y']] = player_pass_events.apply(
        lambda row: pd.Series(get_start_locations(row)), axis=1)

    player_pass_events[['end_location_x', 'end_location_y']] = player_pass_events.apply(
        lambda row: pd.Series(get_pass_end_locations(row)), axis=1)

    player_pass_events[
        ['action_distance_towards_goal', 'action_distance_towards_goal_as_per']] = player_pass_events.apply(
        lambda row: pd.Series(calculate_action_distance(row)), axis=1)

    progressive_passes = player_pass_events[
        (player_pass_events["action_distance_towards_goal_as_per"] >= 10)
        & (player_pass_events["action_distance_towards_goal"] >= 5)
        & (player_pass_events["pass_outcome"].isnull())
        & ~(player_pass_events["pass_type"].isin(["Corner", "Free Kick", "Kick Off", "Throw-in"]))].groupby(
        metric_group_by_list)[
        "id"].count().rename("progressive_passes")

    progressive_passes_from_own_half = player_pass_events[
        (player_pass_events["action_distance_towards_goal_as_per"] >= 10)
        & (player_pass_events["action_distance_towards_goal"] >= 5)
        & (player_pass_events["pass_outcome"].isnull())
        & ~(player_pass_events["pass_type"].isin(["Corner", "Free Kick", "Kick Off", "Throw-in"]))
        & (player_pass_events["location_x"] <= 60)].groupby(
        metric_group_by_list)[
        "id"].count().rename("progressive_passes_from_own_half")

    completed_passes_into_final_third = player_pass_events[
        (player_pass_events["location_x"] < 80)
        & (player_pass_events["end_location_x"] >= 80)
        & (player_pass_events["pass_outcome"].isnull())].groupby(
        metric_group_by_list)[
        "id"].count().rename("passes_into_final_third")

    pass_made_in_the_final_third = player_pass_events[
        (player_pass_events["location_x"] >= 80)].groupby(
        metric_group_by_list)["id"].count().rename(
        "passes_made_in_final_third")

    final_third_pass_obv = player_pass_events[
        (player_pass_events["location_x"] >= 80)].groupby(
        metric_group_by_list)["obv_total_net"].sum().rename("final_third_pass_obv")

    opp_half_pass_obv = player_pass_events[
        (player_pass_events["location_x"] >= 60)].groupby(
        metric_group_by_list)["obv_total_net"].sum().rename("opp_half_pass_obv")

    pass_attempted_crosses = player_pass_events[
        (player_pass_events["pass_cross"] == True)].groupby(
        metric_group_by_list)[
        "id"].count().rename("attempted_crosses")

    pass_completed_crosses = player_pass_events[
        (player_pass_events["pass_cross"] == True)
        & ((player_pass_events["pass_outcome"].isnull())
           | (player_pass_events["pass_outcome"] == "Pass Offside"))].groupby(
        metric_group_by_list)["id"].count().rename("successful_crosses")

    total_passes_under_pressure = player_pass_events[
        (player_pass_events["under_pressure"] == True)
        & (player_pass_events["pass_outcome"] != "Pass Offside")].groupby(
        metric_group_by_list)[
        "id"].count().rename("total_passes_under_pressure")

    completed_passes_under_pressure = player_pass_events[
        (player_pass_events["under_pressure"] == True)
        & (player_pass_events["pass_outcome"].isnull())].groupby(
        metric_group_by_list)[
        "id"].count().rename(
        "completed_passes_under_pressure")

    player_touches = player_events_df[
        (((player_events_df["type"] == "Pass") & (
                (player_events_df["pass_outcome"].isnull())
                | (player_events_df["pass_outcome"] == "Pass Offside")))
         | (player_events_df["type"] == "Clearance")
         | ((player_events_df["type"] == "Dribble") & (player_events_df["dribble_outcome"] == "Complete"))
         | ((player_events_df["duel_type"] == "Tackle")
            & (player_events_df["duel_outcome"].isin(["Success In Play", "Won", "Success Out"])))
         | ((player_events_df["type"] == "Ball Receipt*") & (player_events_df["ball_receipt_outcome"].isnull()))
         | (player_events_df["type"] == "Shot")
         | (player_events_df["type"].isin(["Interception", "Block"])))]

    player_touches = player_touches.copy()
    player_touches[["location_x", "location_y"]] = player_touches.apply(
        lambda row: pd.Series(get_start_locations(row)), axis=1)

    player_touches_inside_box = player_touches[
        (player_touches["location_x"] >= 102)
        & (player_touches["location_y"] >= 18)
        & (player_touches["location_y"] <= 62)].groupby(
        metric_group_by_list)[
        "id"].count().rename("touches_inside_box")

    player_touches_in_final_third = player_touches[
        (player_touches["location_x"] >= 80)].groupby(
        metric_group_by_list)[
        "id"].count().rename("touches_in_final_third")

    # XG CREATED BY POSITION PLAYED -----------------------------------------------------------------------------------
    # to get xg of key passes - create separate df of shots and their ID
    event_shots_df = player_events_df[
        (player_events_df["type"] == "Shot")][["id", "shot_statsbomb_xg"]].copy()

    event_shots_df.rename(columns={"id": "assisted_shot_id", "shot_statsbomb_xg": "assisted_shot_statsbomb_xg"},
                          inplace=True)

    player_key_pass_events_df = player_events_df[
        (player_events_df["pass_shot_assist"] == True)
        | (player_events_df["pass_goal_assist"] == True)]

    player_key_pass_events_df = player_key_pass_events_df.merge(
        event_shots_df, left_on="pass_assisted_shot_id", right_on="assisted_shot_id", how="left")

    all_xg_assisted = player_key_pass_events_df.groupby(
        metric_group_by_list)["assisted_shot_statsbomb_xg"].sum().rename("xga")

    op_xg_assisted = player_key_pass_events_df[
        ~(player_key_pass_events_df["pass_type"].isin(["Corner", "Free Kick", "Kick Off", "Throw-in"]))].groupby(
        metric_group_by_list)["assisted_shot_statsbomb_xg"].sum().rename("open_play_xga")

    sp_xg_assisted = player_key_pass_events_df[
        (player_key_pass_events_df["pass_type"].isin(
            ["Corner", "Free Kick", "Kick Off", "Throw-in"]))].groupby(
        metric_group_by_list)["assisted_shot_statsbomb_xg"].sum().rename("set_piece_xga")

    total_goal_assists = player_events_df[
        (player_events_df["pass_goal_assist"] == True)].groupby(metric_group_by_list)[
        "id"].count().rename(
        "pass_goal_assist")

    open_play_goal_assists = player_events_df[
        ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Kick Off", "Throw-in"]))
        & (player_events_df["pass_goal_assist"] == True)].groupby(metric_group_by_list)[
        "id"].count().rename(
        "open_play_pass_goal_assist")

    pass_obv = player_events_df[
        (player_events_df["type"] == "Pass")].groupby(
        metric_group_by_list)[
        "obv_total_net"].sum().rename(
        "pass_obv")

    tackle_events = player_events_df[
        (player_events_df['type'] == "Duel")
        & (player_events_df['duel_type'] == "Tackle")].copy()

    tackle_events[['location_x', 'location_y']] = tackle_events.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    tackles = tackle_events.groupby(
        metric_group_by_list)[
        'type'].count().rename('total_tackles')

    successful_tackles = tackle_events[
        (tackle_events["duel_outcome"].isin(["Success In Play", "Won", "Success Out"]))].groupby(
        metric_group_by_list)[
        'type'].count().rename('successful_tackles')

    tackles_defensive_third = tackle_events[
        (tackle_events["location_x"] <= 40)].groupby(
        metric_group_by_list)[
        'type'].count().rename('tackles_in_defensive_third')

    interception_events = player_events_df[
        ((player_events_df['type'] == "Interception") | (
                player_events_df["pass_type"] == "Interception"))].copy()

    interception_events[['location_x', 'location_y']] = interception_events.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    interceptions = interception_events.groupby(
        metric_group_by_list)[
        'type'].count().rename('total_interceptions')

    interceptions_defensive_third = interception_events[
        (interception_events["location_x"] <= 40)].groupby(
        metric_group_by_list)[
        'type'].count().rename('interceptions_in_defensive_third')

    dribbled_past = player_events_df[
        (player_events_df['type'] == "Dribbled Past")].groupby(
        metric_group_by_list)[
        'type'].count().rename('dribbled_past')

    aerial_wins = player_events_df[
        ((player_events_df['miscontrol_aerial_won'] == True)
         | (player_events_df['clearance_aerial_won'] == True)
         | (player_events_df['pass_aerial_won'] == True)
         | (player_events_df['shot_aerial_won'] == True))].groupby(
        metric_group_by_list)['id'].count().rename("aerial_wins")

    aerial_lost = player_events_df[
        (player_events_df['type'] == "Duel")
        & (player_events_df['duel_type'] == "Aerial Lost")].groupby(
        metric_group_by_list)['id'].count().rename("aerial_losses")

    fouls_won = player_events_df[
        (player_events_df['type'] == "Foul Won")].groupby(
        metric_group_by_list)['id'].count().rename("fouls_won")

    ball_recovery_events = player_events_df[
        (player_events_df["type"] == "Ball Recovery")
        | (player_events_df["pass_type"] == "Recovery")].copy()

    ball_recovery_events[['location_x', 'location_y']] = ball_recovery_events.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    ball_recoveries = ball_recovery_events.groupby(
        metric_group_by_list)['id'].count().rename("ball_recoveries")

    ball_recoveries_own_half = ball_recovery_events[
        (ball_recovery_events["location_x"] <= 60)].groupby(
        metric_group_by_list)['id'].count().rename("ball_recoveries_own_half")

    ball_recoveries_opp_half = ball_recovery_events[
        (ball_recovery_events["location_x"] > 60)].groupby(
        metric_group_by_list)['id'].count().rename("ball_recoveries_opp_half")

    # WORKINGS FOR PRESSURE REGAINS
    player_pressure_events = player_events_df[
        (player_events_df["type"] == "Pressure")].copy()

    player_pressure_events[['location_x', 'location_y']] = player_pressure_events.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    five_seconds = timedelta(seconds=5)

    def flag_pressure_regains(row_):
        match_id = row_["match_id"]
        team_name = row_["team"]
        possession_type = row_["play_pattern"]
        pressure_time = row_["timestamp"]
        pressure_time_as_time = pd.to_timedelta(pressure_time)
        pressure_time_plus_five = pressure_time_as_time + five_seconds

        possession_number = row_["possession"]

        end_time_of_possession = player_events_df[
            (player_events_df["match_id"] == match_id)
            & (player_events_df["possession"] == possession_number)]["timestamp"].max()

        possession_end_time_as_time = pd.to_timedelta(end_time_of_possession)

        next_possession_team_df = player_events_df[
            (player_events_df["match_id"] == match_id)
            & (player_events_df["possession"] == int(possession_number) + 1)]

        if next_possession_team_df.shape[0] > 0:
            next_poss_team = next_possession_team_df["team"].iloc[0]
            next_poss_type = next_possession_team_df["play_pattern"].iloc[0]
        else:
            next_poss_team = "No Next Possession"
            next_poss_type = "NA"

        if pressure_time_plus_five >= possession_end_time_as_time:
            within_five = "within 5"
        else:
            within_five = "not within 5"

        if (possession_type != "Other"
                and next_poss_team == team_name
                and within_five == "within 5"
                and next_poss_type != "Other"):
            pressure_regain = True
        else:
            pressure_regain = False

        return pressure_regain

    player_pressure_events = player_pressure_events.copy()
    player_pressure_events["pressure_regain"] = player_pressure_events.apply(flag_pressure_regains, axis=1)

    pressures = player_pressure_events.groupby(
        metric_group_by_list)['id'].count().rename("pressures")

    pressures_opp_half = player_pressure_events[
        (player_pressure_events["location_x"] >= 60)].groupby(
        metric_group_by_list)['id'].count().rename("pressures_in_opp_half")

    pressures_final_third = player_pressure_events[
        (player_pressure_events["location_x"] >= 80)].groupby(
        metric_group_by_list)['id'].count().rename("pressures_in_final_third")

    pressure_regains = player_pressure_events[
        (player_pressure_events["pressure_regain"] == True)].groupby(
        metric_group_by_list)[
        'id'].count().rename("pressure_regains")

    fouls = player_events_df[
        (player_events_df["type"] == "Foul Committed")
        & (player_events_df["foul_committed_type"] != "Foul Out")].groupby(
        metric_group_by_list)[
        'id'].count().rename("fouls")

    clearances = player_events_df[
        (player_events_df["type"] == "Clearance")].groupby(
        metric_group_by_list)[
        'id'].count().rename("clearances")

    turnovers = player_events_df[
        ((player_events_df["type"] == "Miscontrol")
         | ((player_events_df["type"] == "Dribble")
            & (player_events_df["dribble_outcome"] == "Incomplete")))].groupby(
        metric_group_by_list)[
        'id'].count().rename("turnovers")

    dispossessions = player_events_df[
        (player_events_df["type"] == "Dispossessed")].groupby(
        metric_group_by_list)[
        'id'].count().rename("dispossessions")

    defensive_action_obv = player_events_df[
        (((player_events_df["type"] == "Duel")
          & (player_events_df["duel_type"] == "Tackle"))
         | (player_events_df["type"] == "Interception")
         | (player_events_df["type"] == "Clearance")
         | (player_events_df["pass_type"] == "Interception")
         | (player_events_df["type"] == "Foul Committed")
         | (player_events_df["type"] == "Block")
         | (player_events_df["type"] == "Dribbled Past"))].groupby(
        metric_group_by_list)[
        "obv_total_net"].sum().rename("defensive_action_obv")

    competition_player_stats_df = pd.concat(
        [total_obv, total_np_shots, total_np_goals, total_np_xg, np_shots_on_target,
         total_dribbles, complete_dribbles, dribble_carry_obv, carry_obv_from_own_half,
         carries_into_final_third, carry_distance, carry_distance_from_own_half, progressive_carries,
         progressive_carries_from_own_half,
         total_passes, total_op_passes,
         total_passes_completed, expected_passes_completed,
         total_key_passes, open_play_key_passes, ball_lost_under_pressure, ball_retained_under_pressure,
         completed_passes_into_final_third, pass_made_in_the_final_third,
         final_third_pass_obv, opp_half_pass_obv, pass_attempted_crosses,
         pass_completed_crosses,
         progressive_passes, progressive_passes_from_own_half,
         total_passes_under_pressure, completed_passes_under_pressure,
         player_touches_inside_box, player_touches_in_final_third,
         all_xg_assisted, op_xg_assisted, sp_xg_assisted,
         total_goal_assists, open_play_goal_assists, pass_obv,
         tackles, successful_tackles, tackles_defensive_third, interceptions,
         interceptions_defensive_third,
         dribbled_past, aerial_lost, aerial_wins,
         fouls_won, ball_recoveries, ball_recoveries_own_half,
         ball_recoveries_opp_half, pressures, pressure_regains,
         pressures_opp_half, pressures_final_third,
         fouls, clearances, turnovers, dispossessions,
         defensive_action_obv], axis=1).fillna(0)

    competition_player_stats_df["total_aerial_duels"] = competition_player_stats_df[
        ["aerial_losses", "aerial_wins"]].sum(axis=1)

    competition_player_stats_df["tackles_and_interceptions"] = competition_player_stats_df[
        ["total_tackles", "total_interceptions"]].sum(axis=1)

    competition_player_stats_df["tackles_and_interceptions_in_defensive_third"] = competition_player_stats_df[
        ["tackles_in_defensive_third", "interceptions_in_defensive_third"]].sum(axis=1)

    print(competition_player_stats_df.head(20).to_string())

    competition_player_stats_df.to_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_metric_totals.csv")

    # print(competition_player_stats_df.head(10).to_string())


create_player_data_by_position()
