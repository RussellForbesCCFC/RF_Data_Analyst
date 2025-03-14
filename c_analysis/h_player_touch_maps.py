import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from highlight_text import ax_text
from matplotlib import gridspec
from matplotlib.colors import Normalize
from mplsoccer import VerticalPitch

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import get_start_locations


def player_touch_maps(focus_player_id, filtered_general_position):
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

    fig = plt.figure(figsize=(22, 5.5), dpi=100)

    ax_pitches = gridspec.GridSpec(2, number_of_matches, height_ratios=[.95, .05])
    ax_cbar = gridspec.GridSpec(2, 3, height_ratios=[.95, .05], width_ratios=[0.4, 0.3, 0.4], hspace=-0.3)
    title_text_color = "black"

    for n, match_id_reference in enumerate(player_matches_played_in):
        ax = fig.add_subplot(ax_pitches[n])

        pitch = VerticalPitch(pitch_type="statsbomb",
                              pitch_color='none',
                              half=False, line_zorder=2, corner_arcs=True,
                              linewidth=1, line_alpha=1, line_color='black',
                              pad_left=4, pad_right=4, pad_bottom=4, pad_top=4)

        pitch.draw(ax=ax)

        ax.fill_between([0, 80],
                        0, 120,
                        linewidth=0,
                        color="#fefaf1",
                        alpha=1, zorder=1)

        x_plot_points = [18, 30, 50, 62]
        y_plot_points = [18, 40, 60, 80, 102]
        for y in y_plot_points:
            ax.plot([0, 80], [y, y], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

        for x in x_plot_points:
            ax.plot([x, x], [0.1, 120], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

        if n == 0:
            ax.annotate(xy=(-2, 90), xytext=(-2, 30), text='', color=title_text_color, size=16,
                        xycoords='data',
                        arrowprops=dict(arrowstyle='-|>', color=title_text_color))

            ax.annotate(xy=(-2.5, 60), xytext=(-2.5, 60), text='Direction of Attack'.upper(),
                        va='center', ha="right", color=title_text_color, size=8,
                        xycoords='data', family='avenir', rotation=90)

        # get match data
        # player minutes in position in match
        player_match_minute_data = all_matches_player_positions_df[
            (all_matches_player_positions_df["match_id"] == match_id_reference)]

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
                textalign="center", vsep=2, color=title_text_color,
                ha="center", va="center", family="avenir next condensed", fontsize=10)

        # player touches
        # get all the team events in the time when the focus player is playing the filtered position
        match_team_data = []
        for index, row in player_match_minute_data.iterrows():
            start_index = row["start_index"]
            end_index = row["end_index"]

            player_events_in_range = player_events_df[
                (player_events_df["match_id"] == match_id_reference)
                & (player_events_df["team"] == focus_player_team)
                & (player_events_df["player_id"] == focus_player_id)
                & (player_events_df["index"] >= start_index)
                & (player_events_df["index"] <= end_index)]

            match_team_data.append(player_events_in_range)

        player_match_events_df = pd.concat(match_team_data)

        player_match_touches = player_match_events_df[
            (((player_match_events_df["type"] == "Pass") &
              (player_match_events_df["pass_outcome"] != "Pass Offside"))
             | (player_match_events_df["type"] == "Clearance")
             | ((player_match_events_df["type"] == "Dribble") & (
                            player_match_events_df["dribble_outcome"] == "Complete"))
             | ((player_match_events_df["duel_type"] == "Tackle")
                & (player_match_events_df["duel_outcome"].isin(["Success In Play", "Won", "Success Out"])))
             | ((player_match_events_df["type"] == "Ball Receipt*") & (
                        player_match_events_df["ball_receipt_outcome"].isnull()))
             | (player_match_events_df["type"] == "Shot")
             | (player_match_events_df["type"].isin(["Interception", "Block"])))].copy()

        player_match_touches[['location_x', 'location_y']] = player_match_touches.apply(
            lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

        focus_player_average_x_position = player_match_touches["location_x"].mean()
        focus_player_average_y_position = player_match_touches["location_y"].mean()

        touch_count = player_match_touches.shape[0]

        pitch.scatter(focus_player_average_x_position, focus_player_average_y_position,
                      s=550, color="powderblue", edgecolors="black", linewidth=1,
                      zorder=8, alpha=1, ax=ax)

        pitch.text(focus_player_average_x_position, focus_player_average_y_position,
                   touch_count, ha="center", va="center", fontsize=8, color="black",
                   family="avenir next condensed", zorder=8, alpha=1, ax=ax)

        pitch.kdeplot(player_match_touches["location_x"],
                      player_match_touches["location_y"], ax=ax,
                      fill=True, levels=30, thresh=0.1,
                      cut=4, cmap="cool", zorder=1, bw_adjust=.85)

        pitch.kdeplot(player_match_touches["location_x"],
                      player_match_touches["location_y"], ax=ax,
                      fill=False, levels=1, thresh=0.1,
                      cut=4, color="black", zorder=2, bw_adjust=.85)

    # COLOR BAR -------------------------------------------------------------------------------------------------------
    cbar_ax = fig.add_subplot(ax_cbar[4])

    cbar_ax.set_ylim(0, 1)
    cbar_ax.set_xlim(0, 1)

    cmap = matplotlib.colormaps["cool"]
    norm = Normalize(vmin=0, vmax=1)
    fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax,
                 orientation="horizontal", location="bottom", shrink=0.8)

    cbar_ax.set_yticks([])
    cbar_ax.set_xticks([])
    cbar_ax.set_yticklabels([])
    cbar_ax.set_xticklabels([])

    cbar_ax.annotate(xy=(0, 0.5), xytext=(-0.01, 0.5), text=f"Lower Volume of Touches".upper(),
                     color='black', size=10, family="avenir",
                     xycoords='data', ha="right", va="center")

    cbar_ax.annotate(xy=(1, 0.5), xytext=(1.01, 0.5), text=f"Higher Volume of Touches".upper(),
                     color='black', size=10, family="avenir",
                     xycoords='data', ha="left", va="center")

    # FIGURE TEXT AND SAVE

    fig.text(x=.5125, y=1.02, s=f"{focus_player_name} Touch Maps".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=26, ha="center", va="center")

    fig.text(x=.5125, y=.96,
             s=f"Circles show {focus_player_name}s average position | Number represents the amount of touches | underlying heatmaps are of all his touches\n"
               f"When playing {filtered_general_position} for {focus_player_team} in {focus_player_competition}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=10, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(

        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_touch_maps_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


player_touch_maps(6655, "Central / Defensive Midfielder")
