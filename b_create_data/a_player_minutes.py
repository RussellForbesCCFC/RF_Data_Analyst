import pandas as pd
import numpy as np

from helpers.helper_dictionaries import position_groups


def create_player_minutes_by_position():
    """
    Creates the player aggregated minutes by position and exports to a csv file in b_aggregated_data
    :return: a dataframe containing player minutes by wider position group
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

    # df that will be used to get team names in each game
    match_teams_df = player_events_df[player_events_df["type"] == "Starting XI"]

    # WORKINGS FOR PLAYER MINUTES BY POSITION -------------------------------------------------------------------------
    # empty list that will temporarily hold dataframes of each match
    competition_player_positions_list = []

    # list match ids in the df
    competition_match_ids = player_events_df["match_id"].unique().tolist()
    for match_id_ref in competition_match_ids:
        # get the teams in each match
        teams_in_match = match_teams_df[
            (match_teams_df["match_id"] == match_id_ref)]["team"].unique().tolist()

        match_events_df = player_events_df[(player_events_df["match_id"] == match_id_ref)]
        match_competition = match_events_df["competition_name"].iloc[0]

        # loop each team in the match to get the players in each team
        for team_ref in teams_in_match:
            # empty list to hold dataframes of both teams players
            team_match_positions_list = []

            # team lineup and tactical shifts
            team_lineups_df = match_events_df[
                (match_events_df["team"] == team_ref)
                & (match_events_df['type'].isin(['Starting XI', "Tactical Shift"]))]

            game_substitutions_cards = match_events_df[
                (match_events_df["team"] == team_ref)
                & ((match_events_df["foul_committed_card"] == "Red Card")
                   | (match_events_df["bad_behaviour_card"] == "Red Card")
                   | (match_events_df['type'] == "Substitution"))]

            game_half_start_ends = match_events_df[
                (match_events_df["team"] == team_ref)
                & (((match_events_df["type"] == "Half Start") & (match_events_df["period"].isin([2, 3, 4])))
                   | (match_events_df["type"] == "Half End"))]

            # Return a list of dictionaries of all players in the starting lineup and tactical shifts
            team_player_list = []
            for index_, row_ in team_lineups_df.iterrows():
                tactics_dict = eval(row_["tactics"])
                formation = tactics_dict['formation']
                lineups = tactics_dict['lineup']
                time_s = row_["timestamp"]
                event_type = row_["type"]
                period = row_["period"]
                index = row_["index"]

                for n, p_ in enumerate(lineups):
                    player_id = p_['player']['id']
                    player_name = p_['player']['name']
                    position_name = p_['position']['name']
                    player_pos = {"index": index, "type": event_type,
                                  "player": player_name, "player_id": player_id,
                                  "position": position_name, "timestamp": time_s,
                                  "period": period, "team_formation": formation}

                    team_player_list.append(player_pos)

            # add in half ends
            for index_, row_ in game_half_start_ends.iterrows():
                index = row_["index"]
                event_type = row_["type"]
                time_s = row_["timestamp"]
                period = row_["period"]

                player_pos = {"index": index, "type": event_type,
                              "timestamp": time_s,
                              "period": period}

                team_player_list.append(player_pos)

            # add in subs and red cards (end time events)
            for index_, row_ in game_substitutions_cards.iterrows():
                player_id = row_["player_id"]
                index = row_["index"]
                event_type = row_["type"]
                player_name = row_["player"]
                position_name = row_["position"]
                time_s = row_["timestamp"]
                period = row_["period"]
                player_sub_on = row_["substitution_replacement"]
                foul_red_card = row_["foul_committed_card"]
                bb_red_card = row_["bad_behaviour_card"]

                player_pos = {"index": index, "type": event_type,
                              "player": player_name, "player_id": player_id,
                              "position": position_name, "timestamp": time_s,
                              "period": period, "player_substituted_on": player_sub_on,
                              "foul_red_card": foul_red_card, "behaviour_red_card": bb_red_card}

                team_player_list.append(player_pos)

                if event_type == "Substitution":
                    player_sub_on_game_events = match_events_df[
                        (match_events_df["team"] == team_ref)
                        & (match_events_df["player"] == player_sub_on)]

                    # small chance the player was subbed on and had no events
                    # get df of all player events to get their player id
                    player_sub_on_season_events = player_events_df[
                        (player_events_df["team"] == team_ref)
                        & (player_events_df["player"] == player_sub_on)]

                    if player_sub_on_game_events.shape[0] > 0:
                        player_sub_on_id = match_events_df[
                            (match_events_df["team"] == team_ref)
                            & (match_events_df["player"] == player_sub_on)]["player_id"].iloc[0]

                    # if the subbed on player has no events in the match - get from competition events
                    elif player_sub_on_season_events.shape[0] > 0:
                        player_sub_on_id = player_sub_on_season_events["player_id"].iloc[0]

                    # if still can't find player ID - manually enter it
                    else:
                        # in this example if a player has no events in the whole dataset they won't meet the minute threshold
                        # so can be excluded at this stage
                        # in other cases I have an input here and manually input the player ID
                        player_sub_on_id = None

                    # get the first position of the subbed on player
                    player_match_events = match_events_df[(match_events_df["player_id"] == player_sub_on_id)]

                    if player_match_events.shape[0]:
                        sub_on_position = player_match_events["position"].iloc[0]
                    else:
                        sub_on_position = position_name

                    sub_player_pos = {"index": index, "type": "Substitution On",
                                      "player": player_sub_on, "player_id": player_sub_on_id,
                                      "position": sub_on_position, "timestamp": time_s,
                                      "period": period}

                    team_player_list.append(sub_player_pos)

            # IF THERE ARE NO YELLOW CARDS OR SUBS IN THE GAME, NEED TO STILL CREATE THE COLUMNS
            if game_substitutions_cards.shape[0] == 0:
                column_fill = {
                    "index": np.nan, "type": np.nan,
                    "player": np.nan, "player_id": np.nan,
                    "position": np.nan, "timestamp": np.nan,
                    "period": np.nan, "player_substituted_on": np.nan,
                    "foul_red_card": np.nan, "behaviour_red_card": np.nan}

                team_player_list.append(column_fill)

            player_df = pd.DataFrame(team_player_list)

            player_match_ids = player_df[~(player_df["player_id"].isnull())]["player_id"].unique().tolist()
            player_df.sort_values("index", inplace=True)

            # get individual player minutes by position for each player in the lineup
            for pl in player_match_ids:
                player_id_events = player_df[
                    (player_df["player_id"] == pl)
                    | (player_df["type"].isin(["Half End", "Half Start"]))]

                player_sub_on_row = player_id_events[player_id_events["type"] == "Substitution On"]
                player_sub_off_row = player_id_events[player_id_events["type"] == "Substitution"]

                player_red_card_row = player_id_events[(player_id_events["foul_red_card"] == "Red Card")
                                                       | (player_id_events["behaviour_red_card"] == "Red Card")]

                # if the player is subbed on and not subbed off
                if player_sub_on_row.shape[0] > 0 and player_sub_off_row.shape[0] == 0:
                    sub_on_index = player_id_events[player_id_events["type"] == "Substitution On"]["index"].iloc[0]
                    player_id_events = player_id_events[player_id_events["index"] >= sub_on_index]

                # if the player is subbed off
                elif player_sub_off_row.shape[0] > 0 and player_sub_on_row.shape[0] == 0:
                    sub_off_index = player_id_events[player_id_events["type"] == "Substitution"]["index"].iloc[0]
                    player_id_events = player_id_events[player_id_events["index"] <= sub_off_index]

                # if player is subbed on then subbed off
                elif player_sub_on_row.shape[0] > 0 and player_sub_off_row.shape[0] > 0:
                    sub_on_index = player_id_events[player_id_events["type"] == "Substitution On"]["index"].iloc[0]
                    sub_off_index = player_id_events[player_id_events["type"] == "Substitution"]["index"].iloc[0]
                    player_id_events = player_id_events[(player_id_events["index"] >= sub_on_index)
                                                        & (player_id_events["index"] <= sub_off_index)]

                # if the player was sent off
                elif player_red_card_row.shape[0] > 0:
                    red_card_index = player_id_events[
                        (player_id_events["foul_red_card"] == "Red Card")
                        | (player_id_events["behaviour_red_card"] == "Red Card")]["index"].iloc[0]
                    player_id_events = player_id_events[player_id_events["index"] <= red_card_index]

                else:
                    player_id_events = player_id_events

                player_id_events = player_id_events.copy()
                player_id_events["position"] = player_id_events["position"].ffill()
                player_id_events['start_time'] = player_id_events['timestamp']
                player_id_events['end_time'] = player_id_events['timestamp'].shift(-1)
                player_id_events['start_time'] = pd.to_timedelta(player_id_events['start_time'])
                player_id_events['end_time'] = pd.to_timedelta(player_id_events['end_time'])
                player_id_events['start_index'] = player_id_events['index']
                player_id_events['end_index'] = player_id_events['index'].shift(-1)
                team_match_positions_list.append(player_id_events)

            team_match_positions_df = pd.concat(team_match_positions_list, ignore_index=True)
            team_match_positions_df = team_match_positions_df[
                ~(team_match_positions_df["type"].isin(
                    ["Half End", "Substitution", "Foul Committed", "Bad Behaviour"]))]

            team_match_positions_df = team_match_positions_df.copy()
            team_match_positions_df['time_in_position'] = team_match_positions_df['end_time'] - team_match_positions_df[
                'start_time']
            team_match_positions_df['total_time_seconds'] = team_match_positions_df['time_in_position'].apply(
                lambda x: pd.to_timedelta(x).total_seconds())
            team_match_positions_df['total_time_minutes'] = team_match_positions_df['total_time_seconds'] / 60

            team_match_positions_df.drop(
                columns=["player_substituted_on", "time_in_position", "start_time", "end_time"])

            team_match_positions_df["player"] = team_match_positions_df["player"].ffill()
            team_match_positions_df["player_id"] = team_match_positions_df["player_id"].ffill()

            team_match_positions_df["index"] = range(0, team_match_positions_df.shape[0])
            team_match_positions_df["row_reference"] = range(0, team_match_positions_df.shape[0])
            team_match_positions_df["match_id"] = match_id_ref
            team_match_positions_df["team"] = team_ref
            team_match_positions_df["team_formation"] = team_match_positions_df["team_formation"].ffill()
            team_match_positions_df["competition_name"] = match_competition
            competition_player_positions_list.append(team_match_positions_df)

    competition_player_positions_df = pd.concat(competition_player_positions_list)
    competition_player_positions_df["position_group"] = competition_player_positions_df["position"].apply(
        lambda x: position_groups[x])

    # group player data to get player minutes by general position
    player_position_minutes = competition_player_positions_df.groupby(
        ["player_id", "player", "position_group", "competition_name", "team"])[
        "total_time_minutes"].sum().reset_index()

    player_position_minutes.to_csv(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_minutes.csv")


create_player_minutes_by_position()
