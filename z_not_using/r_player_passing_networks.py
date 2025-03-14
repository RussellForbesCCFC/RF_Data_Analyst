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


def add_position_to_pass_receiver(row, df):
    pass_receiver_id = row["pass_recipient_id"]
    pass_index = row["index"]

    receiver_events_after_index = df[
        (df["index"] >= pass_index)
        & (df["player_id"] == pass_receiver_id)]

    player_first_position = receiver_events_after_index["position"].iloc[0]

    return player_first_position


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

    fig = plt.figure(figsize=(20, 12), dpi=100)
    title_text_color = "black"

    ax = fig.add_subplot()

    pitch = VerticalPitch(pitch_type="statsbomb",
                          pitch_color='none',
                          half=False, line_zorder=2, corner_arcs=True,
                          linewidth=1, line_alpha=1, line_color='black',
                          pad_left=0, pad_right=0, pad_bottom=0, pad_top=0)

    pitch.draw(ax=ax)

    ax.set_facecolor("#FEFAF1")

    x_plot_points = [18, 30, 50, 62]
    y_plot_points = [18, 40, 60, 80, 102]
    for y in y_plot_points:
        ax.plot([0, 80], [y, y], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

    for x in x_plot_points:
        ax.plot([x, x], [0.1, 120], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

    # DATA
    open_play_team_pass_events_df = player_events_df[
        (player_events_df["team"] == focus_player_team)
        & (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

    open_play_team_pass_events_df[['location_x', 'location_y']] = open_play_team_pass_events_df.apply(
        lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

    open_play_team_pass_events_df[
        ['end_location_x', 'end_location_y']] = open_play_team_pass_events_df.apply(
        lambda _row_: pd.Series(get_pass_end_locations(_row_)), axis=1)

    print(open_play_team_pass_events_df.head().to_string())

    # passes from the focus player
    focus_player_open_play_pass_events_df = open_play_team_pass_events_df[
        (open_play_team_pass_events_df["player_id"] == focus_player_id)].copy()

    focus_player_open_play_pass_events_df["pass_recipient_group"] = focus_player_open_play_pass_events_df.apply(
        add_position_to_pass_receiver, axis=1)

    # passes to the focus player
    open_play_passes_to_focus_player_df = open_play_team_pass_events_df[
        (open_play_team_pass_events_df["pass_recipient_id"] == focus_player_id)].copy()

    focus_player_passes_from_counts = open_play_passes_to_focus_player_df["player"].value_counts().rename(
        "passes_from_players")

    pass_counts_from_focus_player = focus_player_open_play_pass_events_df["pass_recipient"].value_counts().rename(
        "passes_to_players")

    combined_pass_df = pd.concat([focus_player_passes_to_counts, focus_player_passes_from_counts], axis=1).reset_index()
    combined_pass_df["total_pass_events_between_players"] = combined_pass_df[
        ["passes_to_players", "passes_from_players"]].sum(axis=1).fillna(0)
    combined_pass_df.rename(columns={"index": "player"}, inplace=True)
    combined_pass_df.sort_values("total_pass_events_between_players", ascending=False, inplace=True)
    combined_pass_df = combined_pass_df.head(6)

    print(combined_pass_df.to_string())
    for index, row in combined_pass_df.iterrows():
        player_name = row["player"]
        total_passes = row["total_pass_events_between_players"]
        passe_to = row["passes_to_players"]
        passe_from = row["passes_from_players"]

        passes_from_players_to_focus_player = open_play_team_pass_events_df[
            (open_play_team_pass_events_df["player"] == player_name)
            & (open_play_team_pass_events_df["pass_recipient"] == focus_player_name)
            & (open_play_team_pass_events_df["pass_outcome"].isnull())]

        player_average_x = passes_from_players_to_focus_player["location_x"].mean()
        player_average_y = passes_from_players_to_focus_player["location_y"].mean()

        pitch.scatter(player_average_x, player_average_y,
                      s=550, color="powderblue", edgecolors="black", linewidth=1,
                      zorder=8, alpha=1, ax=ax)

    # FIGURE
    fig.text(x=.5125, y=.955, s=f"Passing Networks".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=32, ha="center", va="center")

    fig.text(x=.5125, y=.915,
             s=f"Pitch Shows {focus_player_name} average position he players and receives passes\n"
               f"and the 6 players he has the most passes to/from\n"
               f"and their average positions in these pass events".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=13, ha="center", va="center")

    fig.set_facecolor("#FEFAF1")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_passing_networks_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()

# player_team_passing_networks(6655, "Central / Defensive Midfielder")
