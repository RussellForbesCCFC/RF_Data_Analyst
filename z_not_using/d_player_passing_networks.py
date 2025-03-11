import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import VerticalPitch
import seaborn as sns
from highlight_text import ax_text
import matplotlib.patheffects as path_effects
from PIL import Image
from io import BytesIO
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)
from matplotlib.colors import LinearSegmentedColormap

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import get_start_locations, get_pass_end_locations


def player_team_passing_networks(focus_player_id, filtered_general_position):
    # read and combine raw data
    euro_events_df = pd.read_csv(
        "/a_data/a_raw_data/euro_2024_task_data.csv",
        low_memory=False)
    euro_events_df["competition_name"] = "Euro 2024"

    copa_events_df = pd.read_csv(
        "/a_data/a_raw_data/copa_2024_task_data.csv",
        low_memory=False)
    copa_events_df["competition_name"] = "Copa 2024"

    player_events_df = pd.concat([euro_events_df, copa_events_df], ignore_index=True)

    # get a list of the match_ids the player played in
    focus_player_events_df = player_events_df[player_events_df["player_id"] == focus_player_id]
    focus_player_name = focus_player_events_df["player"].iloc[0]
    focus_player_team = focus_player_events_df["team"].iloc[0]
    focus_player_competition = focus_player_events_df["competition_name"].iloc[0]

    player_matches_played_in = sorted(focus_player_events_df["match_id"].unique().tolist())

    all_matches_player_positions_list = []
    # loop each match - get the player positions played and time in each
    for match_id_ref in player_matches_played_in:
        match_events_df = player_events_df[(player_events_df["match_id"] == match_id_ref)]
        focus_player_team = player_events_df[player_events_df["player_id"] == focus_player_id]["team"].iloc[0]

        match_competition = match_events_df["competition_name"].iloc[0]

        # empty list to hold dataframes of all the matches the player has played in
        player_match_positions_list = []

        # team lineup and tactical shifts
        team_lineups_df = match_events_df[
            (match_events_df["team"] == focus_player_team)
            & (match_events_df['type'].isin(['Starting XI', "Tactical Shift"]))]

        game_substitutions_cards = match_events_df[
            (match_events_df["team"] == focus_player_team)
            & ((match_events_df["foul_committed_card"] == "Red Card")
               | (match_events_df["bad_behaviour_card"] == "Red Card")
               | (match_events_df['type'] == "Substitution"))]

        game_half_start_ends = match_events_df[
            (match_events_df["team"] == focus_player_team)
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
                    (match_events_df["team"] == focus_player_team)
                    & (match_events_df["player"] == player_sub_on)]

                # small chance the player was subbed on and had no events
                # get df of all player events to get their player id
                player_sub_on_season_events = player_events_df[
                    (player_events_df["team"] == focus_player_team)
                    & (player_events_df["player"] == player_sub_on)]

                if player_sub_on_game_events.shape[0] > 0:
                    player_sub_on_id = match_events_df[
                        (match_events_df["team"] == focus_player_team)
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

        # get individual player minutes for the focus player

        player_id_events = player_df[
            (player_df["player_id"] == focus_player_id)
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

        player_match_positions_list.append(player_id_events)

        player_match_positions_df = pd.concat(player_match_positions_list, ignore_index=True)
        player_match_positions_df = player_match_positions_df[
            ~(player_match_positions_df["type"].isin(
                ["Half End", "Substitution", "Foul Committed", "Bad Behaviour"]))].copy()

        player_match_positions_df['time_in_position'] = player_match_positions_df['end_time'] - \
                                                        player_match_positions_df[
                                                            'start_time']
        player_match_positions_df['total_time_seconds'] = player_match_positions_df['time_in_position'].apply(
            lambda x: pd.to_timedelta(x).total_seconds())
        player_match_positions_df['total_time_minutes'] = player_match_positions_df['total_time_seconds'] / 60

        player_match_positions_df.drop(
            columns=["player_substituted_on", "time_in_position", "start_time", "end_time"])

        player_match_positions_df["player"] = player_match_positions_df["player"].ffill()
        player_match_positions_df["player_id"] = player_match_positions_df["player_id"].ffill()

        player_match_positions_df["index"] = range(0, player_match_positions_df.shape[0])
        player_match_positions_df["row_reference"] = range(0, player_match_positions_df.shape[0])
        player_match_positions_df["match_id"] = match_id_ref
        player_match_positions_df["team"] = focus_player_team
        player_match_positions_df["team_formation"] = player_match_positions_df["team_formation"].ffill()
        player_match_positions_df["competition_name"] = match_competition

        all_matches_player_positions_list.append(player_match_positions_df)

    all_matches_player_positions_df = pd.concat(all_matches_player_positions_list)
    all_matches_player_positions_df["position_group"] = all_matches_player_positions_df["position"].apply(
        lambda x: position_groups[x])

    all_matches_player_positions_df = all_matches_player_positions_df[
        (all_matches_player_positions_df["position_group"] == filtered_general_position)]

    # CREATE FIGURE
    number_of_matches = len(player_matches_played_in)

    fig = plt.figure(figsize=(22, 18), dpi=100)

    if number_of_matches == 7:
        subplot_arrange = [2, 4]
    else:
        subplot_arrange = [1, 6]

    for n, match_id_reference in enumerate(player_matches_played_in):
        ax = fig.add_subplot(subplot_arrange[0], subplot_arrange[1], n + 1)

        pitch = VerticalPitch(pitch_type="statsbomb",
                              pitch_color='none',
                              half=False, line_zorder=2, corner_arcs=True,
                              linewidth=1, line_alpha=1, line_color='black',
                              pad_left=4, pad_right=4, pad_bottom=4, pad_top=4)

        pitch.draw(ax=ax)

        ax.set_facecolor("#FEFAF1")

        x_plot_points = [18, 30, 50, 62]
        y_plot_points = [18, 39, 60, 80, 102]
        for y in y_plot_points:
            ax.plot([0, 80], [y, y], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

        for x in x_plot_points:
            ax.plot([x, x], [0.1, 120], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

        if n == 0:
            ax.annotate(xy=(-2, 90), xytext=(-2, 30), text='', color='black', size=16,
                        xycoords='data',
                        arrowprops=dict(arrowstyle='-|>', color='black'))

            ax.annotate(xy=(-2.5, 60), xytext=(-2.5, 60), text='Direction of Attack'.upper(),
                        va='center', ha="right", color='black', size=8,
                        xycoords='data', family='avenir', style='italic', rotation=90)

        # get match data
        # player minutes in position in match
        player_match_minute_data = all_matches_player_positions_df[
            (all_matches_player_positions_df["match_id"] == match_id_reference)]

        print(player_match_minute_data.to_string())

        player_total_minutes_in_position = player_match_minute_data["total_time_minutes"].sum()

        # data for title
        match_events = player_events_df[(player_events_df["match_id"] == match_id_reference)]

        match_teams = match_events["team"].unique().tolist()

        fixture_goals = {}
        for team in match_teams:
            team_goals_in_match = match_events[
                (match_events["period"] != 5)
                & (match_events["team"] == team)
                & ((match_events["type"] == "Own Goal For")
                   | (match_events["shot_outcome"] == "Goal"))].shape[0]

            fixture_goals[team] = team_goals_in_match

        match_title = (
            f"{match_teams[0]} {fixture_goals[match_teams[0]]} - {fixture_goals[match_teams[1]]} {match_teams[1]}\n"
            f"<Minutes: {int(round(player_total_minutes_in_position))}>")

        ax_text(x=40, y=128, s=match_title.upper(), highlight_textprops=[{"family": "avenir", "fontsize": 8}],
                textalign="center", vsep=2,
                ha="center", va="center", family="avenir next condensed", fontsize=10)

        # passing network
        # get all the team events in the time when the focus player is playing the filtered position
        match_team_data = []
        for index, row in player_match_minute_data.iterrows():
            start_index = row["start_index"]
            end_index = row["end_index"]

            events_in_range = player_events_df[
                (player_events_df["match_id"] == match_id_reference)
                & (player_events_df["team"] == focus_player_team)
                & (player_events_df["index"] >= start_index)
                & (player_events_df["index"] <= end_index)]

            match_team_data.append(events_in_range)

        match_team_events_df = pd.concat(match_team_data)

        # start workings for passing network

        subs_list = match_team_events_df[
            (match_team_events_df['type'] == "Substitution")][
            'substitution_replacement'].to_list()

        match_pass_events_df = match_team_events_df[
            (match_team_events_df["type"] == "Pass")
            & (match_team_events_df["pass_outcome"] != "Pass Offside")
            & ~ (match_team_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

        match_ball_receipt_events_df = match_team_events_df[
            (match_team_events_df["type"] == "Ball Receipt*")
            & (match_team_events_df["ball_receipt_outcome"].isnull())].copy()

        match_pass_events_df[['location_x', 'location_y']] = match_pass_events_df.apply(
            lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

        match_pass_events_df[['end_location_x', 'end_location_y']] = match_pass_events_df.apply(
            lambda _row_: pd.Series(get_pass_end_locations(_row_)), axis=1)

        match_ball_receipt_events_df[['location_x', 'location_y']] = match_ball_receipt_events_df.apply(
            lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

        match_pass_and_receipts_df = pd.concat([match_pass_events_df, match_ball_receipt_events_df], ignore_index=True)

        max_pass_and_receipt_count = match_pass_and_receipts_df[["player_id", "player"]].value_counts().max()
        min_pass_and_receipt_count = match_pass_and_receipts_df[["player_id", "player"]].value_counts().min()

        player_positions = match_pass_and_receipts_df.groupby(['player', 'player_id'])[
            ['location_x', 'location_y']].mean().reset_index()

        player_list = player_positions['player'].unique().tolist()

        for ply in player_list:
            player_x_average = player_positions[player_positions['player'] == ply]['location_x'].iloc[0]
            player_y_average = player_positions[player_positions['player'] == ply]['location_y'].iloc[0]

            player_event_count = match_pass_and_receipts_df[
                (match_pass_and_receipts_df['player'] == ply)].shape[0]

            player_event_count_in_range = (
                    (player_event_count -
                     min_pass_and_receipt_count) /
                    (max_pass_and_receipt_count - min_pass_and_receipt_count))

            marker_size_scale = [100, 450]
            marker_range = marker_size_scale[1] - marker_size_scale[0]

            marker_size = (player_event_count_in_range * marker_range) + marker_size_scale[0]

            text_size_scale = [10, 18]
            text_size_range = text_size_scale[1] - text_size_scale[0]
            text_size = (player_event_count_in_range * text_size_range) + text_size_scale[0]

            if ply in subs_list:
                fill_color = 'black'
                text_color = "#FEFAF1"
                text_path_color = "black"
                edge_width = 2
                z_ref = 8
                text_z = 8
                col_alpha = 1
                marker = 'h'

                # ax.scatter(player_y_average, player_x_average, s=marker_size + 100,
                #            color="black", edgecolor="black", marker="h", linewidth=2,
                #            zorder=z_ref - 1, alpha=col_alpha)

            else:
                edge_col = "black"
                text_color = "black"
                text_path_color = "#FEFAF1"
                edge_width = 1
                z_ref = 5
                text_z = 5
                col_alpha = 1
                marker = 'o'

                ax.scatter(player_y_average, player_x_average, s=marker_size,
                           color="blue", edgecolor='black', marker=marker,
                           linewidth=edge_width, zorder=z_ref, alpha=col_alpha)

                ax.annotate(xy=(player_y_average, player_x_average), text="", ha='center', va='center',
                            color=text_color, zorder=text_z, fontsize=text_size,
                            family='avenir next condensed',
                            path_effects=[path_effects.withStroke(linewidth=1, foreground=text_path_color, alpha=1)])

            # player_teammate_passes = player_passes_and_receipts[
            #     (player_passes_and_receipts['type'] == "Pass")
            #     & ~(player_passes_and_receipts["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))
            #     & (player_passes_and_receipts['player'] == ply)].groupby(
            #     'pass_recipient_id')['type'].count().rename('pass_count').reset_index()
            #
            # player_teammate_pass_obv = player_passes_and_receipts[
            #     (player_passes_and_receipts['type'] == "Pass")
            #     & ~(player_passes_and_receipts["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))
            #     & (player_passes_and_receipts['player'] == ply)].groupby(
            #     'pass_recipient_id')['obv_total_net'].sum().rename('pass_pair_obv').reset_index()
            #
            # for x_, p_r in enumerate(player_teammate_passes['pass_recipient_id']):
            #     player_name = find_player_final_name(lineups_df, p_r)
            #     recipient_df_check = player_positions[player_positions['player_id'] == p_r]
            #     if recipient_df_check.shape[0] == 0:
            #         pass
            #     else:
            #         pass_recipient_x = player_positions[player_positions['player_id'] == p_r]['location_x'].iloc[0]
            #         pass_recipient_y = player_positions[player_positions['player_id'] == p_r]['location_y'].iloc[0]
            #
            #         pass_count = player_teammate_passes['pass_count'].iloc[x_]
            #         pass_obv = \
            #             player_teammate_pass_obv[player_teammate_pass_obv["pass_recipient_id"] == p_r][
            #                 "pass_pair_obv"].iloc[0]
            #
            #         # get event count of the receiver for line adjustments
            #         receiver_position_event_count = \
            #             player_passes_and_receipts[(player_passes_and_receipts['player_id'] == p_r)].shape[0]
            #
            #         # STEP 1: GET THE SCALED MARKER SIZE OF THE RECEIVER
            #         # receiver_marker_size = (receiver_position_event_count / player_max_pass_and_receipt_count) * marker_size_scale[1]
            #
            #         receiver_position_event_count_in_range = (
            #                 (receiver_position_event_count - player_min_pass_and_receipt_count) /
            #                 player_pass_and_receipt_range)
            #
            #         receiver_marker_size = ((receiver_position_event_count_in_range * marker_range) +
            #                                 marker_size_scale[0])
            #
            #         # CALCULATE WIDTH OF THE LINE
            #         player_pass_pair_count_in_range = (
            #                 (pass_count - min_pass_pair_count) / range_pass_pair_count)
            #
            #         line_width_scale = [5, 40]
            #         line_width_range = line_width_scale[1] - line_width_scale[0]
            #
            #         line_width = (player_pass_pair_count_in_range * line_width_range) + line_width_scale[0]
            #
            #         # GET THE MARKER SIZE AS % MAX MAKER SIZE
            #         marker_per_scale = (receiver_marker_size - marker_size_scale[0]) / (
            #                 marker_size_scale[1] - marker_size_scale[0])
            #
            #         # REDUCE THE LINE BY THE MARKER % MAX BY LINE REDUCE MAX (15)
            #         line_reduction_range = 18 - 10
            #         line_reduction_value = 10 + (line_reduction_range * marker_per_scale)
            #         line_reduction_value = line_reduction_value * 1.08
            #
            #         direction_vector = np.array(
            #             [pass_recipient_x - player_x_average, pass_recipient_y - player_y_average])
            #
            #         # Calculate the perpendicular direction vector
            #         perpendicular_vector = np.array([-direction_vector[1], direction_vector[0]])
            #
            #         # Normalize the perpendicular vector
            #         perpendicular_vector /= np.linalg.norm(perpendicular_vector)
            #
            #         # Calculate the adjusted starting and ending coordinates
            #         adjusted_start_x = player_x_average - .9 * perpendicular_vector[0]
            #         adjusted_start_y = player_y_average - .9 * perpendicular_vector[1]
            #
            #         adjusted_end_x = pass_recipient_x - .9 * perpendicular_vector[0]
            #         adjusted_end_y = pass_recipient_y - .9 * perpendicular_vector[1]
            #
            #         # line_alpha = pass_count / max_game_passes
            #
            #         line_alpha_values = [0.25, 1]
            #         line_alpha_range = line_alpha_values[1] - line_alpha_values[0]
            #
            #         line_alpha = (player_pass_pair_count_in_range * line_alpha_range) + line_alpha_values[0]
            #
            #         if pass_obv >= 0:
            #             obv_per_range = pass_obv / abs_pair_obv_value
            #             cmap = positive_cmap
            #         elif pass_obv < 0:
            #             obv_per_range = abs(pass_obv) / abs_pair_obv_value
            #             cmap = negative_cmap
            #         else:
            #             obv_per_range = None
            #             cmap = None
            #
            #         pass_obv_color = cmap(obv_per_range)
            #
            #         if pass_count >= 4:
            #             ax.annotate(xy=(adjusted_end_y, adjusted_end_x),
            #                         xytext=(adjusted_start_y, adjusted_start_x),
            #                         text='', size=line_width,
            #                         xycoords='data', zorder=3,
            #                         arrowprops=dict(arrowstyle='simple', color=pass_obv_color,
            #                                         linewidth=0, edgecolor="black",
            #                                         shrinkB=line_reduction_value, alpha=line_alpha))
            #
            #             ax.annotate(xy=(adjusted_end_y, adjusted_end_x),
            #                         xytext=(adjusted_start_y, adjusted_start_x),
            #                         text='', size=line_width + 2,
            #                         xycoords='data', zorder=2,
            #                         arrowprops=dict(arrowstyle='simple', color="#82A0B2",
            #                                         linewidth=1, edgecolor="black",
            #                                         shrinkB=line_reduction_value, alpha=line_alpha))

    fig.text(x=.5125, y=.65, s=f"{focus_player_name}".upper(),
             color="black",
             family="avenir next condensed",
             fontsize=26, ha="center", va="center")

    fig.text(x=.5125, y=.63,
             s=f"Each Pitch shows {focus_player_name} position in "
               f"{focus_player_team}s Passing networks in each match he played in "
               f"{focus_player_competition}\n"
               f"Only when {focus_player_name} is playing {filtered_general_position}".upper(),
             color="black",
             family="avenir",
             fontsize=10, ha="center", va="center")

    fig.set_facecolor("#FEFAF1")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_passing_networks_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


player_team_passing_networks(6655, "Central / Defensive Midfielder")
