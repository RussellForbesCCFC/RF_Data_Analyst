import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer import VerticalPitch
from highlight_text import fig_text
import matplotlib
import matplotlib.patheffects as path_effects
from matplotlib import gridspec
from matplotlib.colors import Normalize
import matplotlib.cm as cm

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import get_start_locations, get_carry_end_locations, get_pass_end_locations, \
    calculate_action_distance, assign_zone_to_start_thirds


def player_forward_passes_map(focus_player_id):
    """
    create a pitch of the players forwards passes
    :param focus_player_id:
    :return:
    """
    cmap_list = ["#FEFAF1", "#95b0d1", "#1974b1"]
    cmap = LinearSegmentedColormap.from_list("", cmap_list)
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

    # print(player_events_df[player_events_df["team"] == "Spain"][["player_id", "player"]].value_counts().to_string())

    # print(player_events_df[player_events_df["team"] == "Spain"][["player", "player_id"]].value_counts().to_string())
    focus_player_open_play_pass_events_df = player_events_df[
        (player_events_df["player_id"] == focus_player_id)
        & (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

    focus_player_name = focus_player_open_play_pass_events_df["player"].iloc[0]
    focus_player_open_play_pass_counts = focus_player_open_play_pass_events_df.shape[0]

    # player passing sonar
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

    player_passes_forwards = focus_player_open_play_pass_events_df[
        (focus_player_open_play_pass_events_df['pass_angle'] >= -0.77)
        & (focus_player_open_play_pass_events_df['pass_angle'] <= .77)].copy()

    player_passes_forwards[['location_x', 'location_y']] = player_passes_forwards.apply(
        lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

    player_passes_forwards[
        ['end_location_x', 'end_location_y']] = player_passes_forwards.apply(
        lambda _row_: pd.Series(get_pass_end_locations(_row_)), axis=1)

    player_passes_forwards["start_zone"] = player_passes_forwards.apply(
        assign_zone_to_start_thirds, axis=1)

    player_passes_forwards["pass_outcome"] = player_passes_forwards["pass_outcome"].fillna("complete")

    # CREATING DF OF ZONE REFERENCES -----------------------------------------------------------------------------------
    positional_y_range = [0, 18, 30, 50, 62]
    positional_y_step = [18, 12, 20, 12, 18]
    positional_x_range = [0, 18, 40, 60, 80, 102]
    positional_x_step = [18, 22, 20, 20, 22, 18]

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

            zone_dict = {"x_start": y_start, "x_end": y_end, "y_start": x_start, "y_end": x_end,
                         "zone_name": count}
            zone_list.append(zone_dict)

    y_plotted = [0]
    x_plotted = [0]
    for r in zone_list:
        x_start = r["x_start"]
        x_end = r["x_end"]
        y_start = r["y_start"]
        y_end = r["y_end"]

        y_plotted.append(y_start)
        x_plotted.append(x_start)

    # ZONE SHADING
    zone_df = pd.DataFrame(zone_list)
    zone_df["x_range"] = zone_df["x_end"] - zone_df["x_start"]
    zone_df["x_center"] = zone_df["x_start"] + (zone_df["x_range"] / 2)

    zone_df["y_range"] = zone_df["y_end"] - zone_df["y_start"]
    zone_df["y_center"] = zone_df["y_start"] + (zone_df["y_range"] / 2)

    start_zone_counts = player_passes_forwards["start_zone"].value_counts().reset_index()
    max_start_zone = start_zone_counts["count"].max()

    for index, row in start_zone_counts.iterrows():
        zone_ref = row["start_zone"]
        count = row["count"]
        count_per_max = (count / max_start_zone)

        # Shading the Zone
        end_zone_reference = zone_df[zone_df["zone_name"] == zone_ref]

        end_x_start = end_zone_reference["x_start"].iloc[0]
        end_y_start = end_zone_reference["y_start"].iloc[0]

        end_x_end = end_zone_reference["x_end"].iloc[0]
        end_y_end = end_zone_reference["y_end"].iloc[0]

        c_fill = cmap(count_per_max)

        ax.fill_between([end_x_start, end_x_end],
                        end_y_start,
                        end_y_end,
                        color=c_fill, alpha=.6, zorder=1, linewidth=0, edgecolor="white")

    for index, row in player_passes_forwards.iterrows():
        pass_outcome = row["pass_outcome"]
        location_x = row["location_x"]
        location_y = row["location_y"]
        end_location_x = row["end_location_x"]
        end_location_y = row["end_location_y"]

        if pass_outcome == "complete":
            line_color = "palegreen"
        else:
            line_color = "indianred"

        pitch.arrows(location_x, location_y,
                     end_location_x, end_location_y,
                     color=line_color, ec='black', linewidth=.5,
                     ax=ax, width=2, headwidth=4.5, headlength=4.5, alpha=1, zorder=2)

    # legend
    forwards_completed_passes = player_passes_forwards[
        (player_passes_forwards["pass_outcome"] == "complete")].shape[0]

    forwards_pass_completion = (forwards_completed_passes / player_passes_forwards.shape[0])
    print(forwards_pass_completion)

    # FIGURE
    fig.text(x=.5125, y=.935, s=f"Forward Passes".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=32, ha="center", va="center")

    fig.text(x=.5125, y=.9125,
             s=f"Pitch Shows all forwards passes made by {focus_player_name}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=13, ha="center", va="center")

    fig.text(x=.5125, y=.895,
             s=f"Forwards Pass Completion %: {int(round(forwards_pass_completion * 100))}%".upper(),
             color="palegreen",
             family="avenir next condensed",
             fontsize=13, ha="center", va="center",
             path_effects=[path_effects.Stroke(linewidth=1, foreground="black", alpha=1),
                           path_effects.Normal()])

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_forward_passes_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


player_forward_passes_map(6655)
