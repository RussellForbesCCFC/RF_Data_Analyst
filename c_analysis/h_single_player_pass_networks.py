import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from matplotlib.colors import LinearSegmentedColormap
import matplotlib
import matplotlib.patheffects as path_effects
from matplotlib import gridspec
from matplotlib.colors import Normalize
import matplotlib.cm as cm
from highlight_text import ax_text

from helpers.helper_dictionaries import position_groups, position_rename
from helpers.helper_functions import get_start_locations, get_carry_end_locations, get_pass_end_locations, \
    calculate_action_distance


def get_receiver_position(row, df):
    try:
        pass_related_events = eval(row["related_events"])
        pass_receiver_id = row["pass_recipient_id"]

        for r in pass_related_events:
            related_event_row = df[df["id"] == r].iloc[0]
            related_event_type = related_event_row["type"]
            related_event_player_id = related_event_row["player_id"]
            related_event_player_position = related_event_row["position"]
            if related_event_type == "Ball Receipt*" and pass_receiver_id == related_event_player_id:
                return related_event_player_position

    except TypeError:
        pass


def player_passing_networks(focus_player_id):
    """
    create 2 pass networks for one player
    one to show the links to where they receive the ball and one to show where they pass the ball too
    :param focus_player_id:
    :return:
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

    focus_player_team = player_events_df[player_events_df["player_id"] == focus_player_id]["team"].iloc[0]

    pass_events_df = player_events_df[player_events_df["type"] == "Pass"].copy()

    pass_events_df[['location_x', 'location_y']] = pass_events_df.apply(
        lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

    pass_events_df[
        ['end_location_x', 'end_location_y']] = pass_events_df.apply(
        lambda _row_: pd.Series(get_pass_end_locations(_row_)), axis=1)

    focus_player_open_play_pass_events_df = pass_events_df[
        (pass_events_df["player_id"] == focus_player_id)
        & (pass_events_df["type"] == "Pass")
        & (pass_events_df["pass_outcome"].isnull())
        & ~(pass_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))]

    focus_player_open_play_pass_recipient_events_df = pass_events_df[
        (pass_events_df["pass_recipient_id"] == focus_player_id)
        & (pass_events_df["type"] == "Pass")
        & (pass_events_df["pass_outcome"].isnull())
        & ~(pass_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))]

    focus_player_name = focus_player_open_play_pass_events_df["player"].iloc[0]
    focus_player_open_play_pass_counts = focus_player_open_play_pass_events_df.shape[0]

    # FIGURE
    fig = plt.figure(figsize=(22, 18), dpi=100)
    title_text_color = "black"

    for n, pass_type in enumerate(["passes_to", "passes_from"]):

        ax = fig.add_subplot(1, 2, n + 1)

        # if passes to the average position of the focus player is the end location of passes
        if pass_type == "passes_to":
            title_text = f"Passes to {focus_player_name}"
            x_location_text = "end_location_x"
            y_location_text = "end_location_y"
            pass_df = focus_player_open_play_pass_recipient_events_df.copy()

            # if in passes to loop the positions will be the positions of the players passing the ball
            position_counts = pass_df["position"].value_counts().rename("pass_counts")
            position_x_average = pass_df.groupby("position")["location_x"].mean().rename("average_x")
            position_y_average = pass_df.groupby("position")["location_y"].mean().rename("average_y")
            positions_df = pd.concat([position_counts, position_x_average, position_y_average], axis=1).reset_index()

        else:
            title_text = f"Passes from {focus_player_name}"
            x_location_text = "location_x"
            y_location_text = "location_y"
            pass_df = focus_player_open_play_pass_events_df.copy()

            # if in the passes from loop the positions will be of the players receiving the ball
            pass_df["pass_receiver_position"] = pass_df.apply(
                lambda row_: get_receiver_position(row_, player_events_df), axis=1)

            position_counts = pass_df["pass_receiver_position"].value_counts().rename("pass_counts")
            position_x_average = pass_df.groupby(
                "pass_receiver_position")["end_location_x"].mean().rename("average_x")
            position_y_average = pass_df.groupby(
                "pass_receiver_position")["end_location_y"].mean().rename("average_y")

            positions_df = pd.concat([position_counts, position_x_average, position_y_average], axis=1).reset_index()
            positions_df.rename(columns={"pass_receiver_position": "position"}, inplace=True)

        ax_text(x=40, y=124, s=title_text.upper(),
                highlight_textprops=[],
                textalign="center", vsep=2, color=title_text_color,
                ha="center", va="center", family="avenir next condensed", fontsize=32)

        pitch = VerticalPitch(pitch_type="statsbomb",
                              pitch_color='none',
                              half=False, line_zorder=2, corner_arcs=True,
                              linewidth=1, line_alpha=1, line_color='black',
                              pad_left=0, pad_right=0, pad_bottom=0, pad_top=0)

        pitch.draw(ax=ax)

        ax.set_facecolor("#FEFAF1")

        x_plot_points = [18, 30, 50, 62]
        y_plot_points = [18, 39, 60, 80, 102]
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

        # average location of focus player

        focus_player_average_x = pass_df[x_location_text].mean()
        focus_player_average_y = pass_df[y_location_text].mean()

        pitch.scatter(focus_player_average_x, focus_player_average_y,
                      s=1000, color="powderblue", edgecolors="black", linewidth=1,
                      zorder=8, alpha=1, ax=ax)

        print(positions_df.to_string())
        for index, row in positions_df.iterrows():
            position = row["position"]
            position_name_short = position_rename[position]
            count = row["pass_counts"]
            x_location = row["average_x"]
            y_location = row["average_y"]

            pitch.scatter(x_location, y_location,
                          s=500, color="lightgrey", edgecolors="black", linewidth=1,
                          zorder=2, alpha=1, ax=ax)

            pitch.text(x_location, y_location,
                       s=position_name_short, ha="center", va="center", ax=ax, zorder=5)

    fig.text(x=.5125, y=.92, s=f"Pass Networks".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=60, ha="center", va="center")

    fig.text(x=.5125, y=.885,
             s=f"{focus_player_name}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=34, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_passing_networks_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()

# player_passing_networks(6655)
