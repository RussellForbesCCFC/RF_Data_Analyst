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


def player_minutes_by_match_and_position(focus_player_id):
    positive_cmap_list = ["#FEFAF1", "#9cb7d8", "#1974b1"]
    positive_cmap = LinearSegmentedColormap.from_list("", positive_cmap_list)

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

    # get a list of the match_ids the team the player plays for
    player_team = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]["team"].iloc[0]

    focus_player_name = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]["player"].iloc[0]

    focus_player_team_events_df = player_events_df[player_events_df["team"] == player_team]

    player_team_matches = sorted(focus_player_team_events_df["match_id"].unique().tolist())
    player_matches = player_events_df[player_events_df["player_id"] == focus_player_id]["match_id"].unique().tolist()

    all_matches_player_positions_list = []
    # loop each match - get the player positions played and time in each
    for match_id_ref in player_matches:
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

    player_specific_position_minutes = all_matches_player_positions_df.groupby(
        "position")["total_time_minutes"].sum().sort_values(ascending=False).reset_index()
    max_minutes_in_position = player_specific_position_minutes["total_time_minutes"].max()

    player_specific_match_position_minutes = all_matches_player_positions_df.groupby(
        ["match_id", "position"])["total_time_minutes"].sum().sort_values(ascending=False).reset_index()
    max_minutes_in_position_match = player_specific_match_position_minutes["total_time_minutes"].max()

    player_specific_match_minutes = all_matches_player_positions_df.groupby(
        ["match_id"])["total_time_minutes"].sum().sort_values(ascending=False).reset_index()
    max_minutes_in_match = player_specific_match_minutes["total_time_minutes"].max()

    player_positions_played_list = player_specific_position_minutes["position"].tolist()

    # FIGURE -----------------------------------------------------------------------------------------------------------

    number_of_team_matches = len(player_team_matches)
    number_of_positions_played = len(player_positions_played_list)

    fig = plt.figure(figsize=(20, 4), dpi=100)
    ax = fig.add_subplot()
    title_text_color = "black"
    # ax.set_facecolor("#FEFAF1")

    ax.set_xlim(-0.1, number_of_team_matches + 2.1)
    ax.set_ylim(-1.1, number_of_positions_played + 1.1)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # color fill just inside lines of table
    ax.fill_between([ax.get_xlim()[0] + .1, ax.get_xlim()[1] - .1],
                    ax.get_ylim()[1] - 0.1,
                    ax.get_ylim()[0] + 0.1,
                    linewidth=0,
                    color="#FEFAF1",
                    alpha=1, zorder=1)

    # plot lines
    # inside left vertical
    ax.plot([1, 1], [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 0.1], color='black')
    # outside left vertical
    ax.plot([0, 0], [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 0.1], color='black')

    # outside right vertical
    ax.plot([ax.get_xlim()[1] - 0.1, ax.get_xlim()[1] - 0.1], [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 0.1],
            color='black')

    # top horizontal line
    ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
            [ax.get_ylim()[1] - 0.1, ax.get_ylim()[1] - 0.1], color='black')

    # inside top horizontal line
    ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
            [ax.get_ylim()[1] - 1.1, ax.get_ylim()[1] - 1.1], color='black')

    # bottom horizontal line
    ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
            [ax.get_ylim()[0] + 0.1, ax.get_ylim()[0] + 0.1], color='black')

    ax.yaxis.set_ticks([])
    ax.xaxis.set_ticks([])

    # static titles
    ax.text(x=ax.get_xlim()[0] + 0.6, y=ax.get_ylim()[1] - 0.6, s="Positions".upper(), ha="center",
            va="center",
            family="avenir next condensed", fontsize=16)

    # player total minutes
    total_minutes = all_matches_player_positions_df["total_time_minutes"].sum()
    ax.text(x=ax.get_xlim()[1] - 0.6,
            y=ax.get_ylim()[0] + 0.6,
            s=f"{int(round(total_minutes))}",
            ha="center", va="center",
            family="avenir next condensed", fontsize=16)

    y_title_text_start = ax.get_ylim()[1] - 1.6
    # adding position titles
    for pos_text in player_positions_played_list:
        text_split = pos_text.split(" ")
        if len(text_split) == 3:
            text_joined = f"{text_split[0]} {text_split[1]}\n{text_split[2]}"
        else:
            text_joined = "\n".join(text_split)

        ax.text(x=0.5, y=y_title_text_start,
                s=text_joined.upper(), ha="center",
                va="center",
                family="avenir next condensed", fontsize=12)

        # dotted line under each position
        ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
                [y_title_text_start - 0.5, y_title_text_start - 0.5], lw=.5, color="black")

        # adding position total minutes
        total_minutes_in_position = player_specific_position_minutes[
            (player_specific_position_minutes["position"] == pos_text)]["total_time_minutes"].sum()

        ax.text(x=ax.get_xlim()[1] - 0.6,
                y=y_title_text_start, s=f"{int(round(total_minutes_in_position))}",
                ha="center", va="center",
                family="avenir next condensed", fontsize=16)

        match_minutes_per_max = total_minutes_in_position / max_minutes_in_position

        color = positive_cmap(match_minutes_per_max)
        ax.fill_between([ax.get_xlim()[1] - 0.1, ax.get_xlim()[1] - 1.1],
                        y_title_text_start + 0.5,
                        y_title_text_start - 0.5,
                        linewidth=0, color=color,
                        alpha=.4, zorder=1)

        y_title_text_start -= 1

    # total text and thicker line above
    ax.text(x=0.5, y=y_title_text_start,
            s="total".upper(), ha="center",
            va="center",
            family="avenir next condensed", fontsize=14)

    ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
            [y_title_text_start + 0.5, y_title_text_start + 0.5], lw=1.5, color="black")

    # adding match titles and data for each match
    x_start = 1.5
    for n, match_id_reference in enumerate(player_team_matches):
        match_events = player_events_df[
            (player_events_df["match_id"] == match_id_reference)]

        match_teams = match_events["team"].unique().tolist()

        fixture_goals = {}
        for team in match_teams:
            team_goals_in_match = match_events[
                (match_events["period"] != 5)
                & (match_events["team"] == team)
                & ((match_events["type"] == "Own Goal For")
                   | (match_events["shot_outcome"] == "Goal"))].shape[0]

            fixture_goals[team] = team_goals_in_match

        match_title = (f"{match_teams[0]} {fixture_goals[match_teams[0]]}\n"
                       f"{match_teams[1]} {fixture_goals[match_teams[1]]}")

        # match title
        ax.text(x=x_start, y=ax.get_ylim()[1] - 0.6, s=match_title.upper(), ha="center",
                va="center",
                family="avenir next condensed", fontsize=16)

        # divider line after each game
        ax.plot([x_start + 0.5, x_start + 0.5],
                [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 0.1], lw=.5, color="black")

        # adding match total minutes
        total_minutes_in_match = player_specific_match_minutes[
            (player_specific_match_minutes["match_id"] == match_id_reference)]["total_time_minutes"].sum()

        ax.text(x=x_start, y=ax.get_ylim()[0] + 0.6, s=f"{int(round(total_minutes_in_match))}",
                ha="center", va="center",
                family="avenir next condensed", fontsize=16)

        match_minutes_per_max = total_minutes_in_match / max_minutes_in_match

        color = positive_cmap(match_minutes_per_max)
        ax.fill_between([x_start - .5, x_start + .5],
                        ax.get_ylim()[0] + 0.1,
                        ax.get_ylim()[0] + 1.1,
                        linewidth=0, color=color,
                        alpha=.4, zorder=1)

        # add minutes in position for match
        y_data_start = ax.get_ylim()[1] - 1.6
        for pos_data in player_positions_played_list:
            minutes_in_position = player_specific_match_position_minutes[
                (player_specific_match_position_minutes["match_id"] == match_id_reference)
                & (player_specific_match_position_minutes["position"] == pos_data)]["total_time_minutes"].sum()

            if minutes_in_position > 0:
                ax.text(x=x_start, y=y_data_start,
                        s=f"{int(round(minutes_in_position))}", ha="center",
                        va="center",
                        family="avenir next condensed", fontsize=18)

                per_max = minutes_in_position / max_minutes_in_position_match

                color = positive_cmap(per_max)

                ax.fill_between([x_start - .5, x_start + .5],
                                y_data_start - 0.5,
                                y_data_start + 0.5,
                                linewidth=0,
                                color=color,
                                alpha=.4, zorder=1)

            y_data_start -= 1

        x_start += 1

    # total text and thicker line to left
    ax.text(x=x_start, y=ax.get_ylim()[1] - 0.6,
            s="total".upper(), ha="center",
            va="center",
            family="avenir next condensed", fontsize=14)

    ax.plot([x_start - 0.5, x_start - 0.5],
            [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 0.1], lw=1.5, color="black")

    # fig.text(x=.5125, y=.98, s=f"{focus_player_name}".upper(),
    #          color=title_text_color,
    #          family="avenir next condensed",
    #          fontsize=26, ha="center", va="center")

    fig.text(x=.5125, y=.95,
             s=f"Minutes Played by Position and Matches".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=24, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_match_minutes_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=True)

    plt.close()


player_minutes_by_match_and_position(6655)
