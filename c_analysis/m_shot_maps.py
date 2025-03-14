import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from highlight_text import ax_text
from matplotlib.colors import LinearSegmentedColormap
from numpy.ma.core import left_shift

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import get_start_locations, get_carry_end_locations, get_pass_end_locations, \
    calculate_action_distance, assign_zone_to_start_thirds


def player_shot_maps(focus_player_id):
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

    focus_player_name = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]["player"].iloc[0]

    focus_player_team = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]["team"].iloc[0]

    focus_player_competition = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]["competition_name"].iloc[0]

    # print(player_events_df[
    #           (player_events_df["team"] == "Spain")][["player", "player_id"]].value_counts().to_string())

    # get all team possession that contain a shot

    player_np_shots = player_events_df[
        (player_events_df["player_id"] == focus_player_id)
        & (player_events_df["type"] == "Shot")
        & (player_events_df["shot_type"] != "Penalty")].copy()

    player_np_shots[
        ['location_x', 'location_y']] = player_np_shots.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    player_np_shots["start_zone"] = player_np_shots.apply(
        assign_zone_to_start_thirds, axis=1)

    count_of_shots = player_np_shots.shape[0]
    xg_of_shots = player_np_shots["shot_statsbomb_xg"].sum()
    player_goals = player_np_shots[player_np_shots["shot_outcome"] == "Goal"].shape[0]

    fig = plt.figure(figsize=(12, 5), dpi=100)
    ax = fig.add_subplot()

    pitch = VerticalPitch(pitch_type="statsbomb", pitch_color='#FEFAF1',
                          half=True, line_zorder=3, corner_arcs=True,
                          linewidth=1, line_alpha=1, line_color='black',
                          pad_left=0, pad_right=0, pad_bottom=0, pad_top=0)

    pitch.draw(ax=ax)

    x_plot_points = [18, 30, 50, 62]
    y_plot_points = [80, 102]
    for y in y_plot_points:
        ax.plot([0, 80], [y, y], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

    for x in x_plot_points:
        ax.plot([x, x], [0.1, 120], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

    title_text_color = "black"

    positive_cmap_list = ["#FEFAF1", "#95b0d1", "#1974b1"]
    positive_cmap = LinearSegmentedColormap.from_list("", positive_cmap_list)

    player_stats_text = f"SHOTS: <{int(count_of_shots)}> | xG: <{round(xg_of_shots, 2)}> | GOALS: <{int(player_goals)}>"
    ax_text(x=40, y=122, s=player_stats_text, ha="center", va="center",
            family="avenir", fontsize=13,
            highlight_textprops=[{"family": "avenir next condensed"},
                                 {"family": "avenir next condensed"},
                                 {"family": "avenir next condensed"}])

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

    start_zone_counts = player_np_shots["start_zone"].value_counts().reset_index()
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

        c_fill = positive_cmap(count_per_max)

        ax.fill_between([end_x_start, end_x_end],
                        end_y_start,
                        end_y_end,
                        color=c_fill, alpha=.6, zorder=1, linewidth=0, edgecolor="white")

    for index, row in player_np_shots.iterrows():
        location_x = row["location_x"]
        location_y = row["location_y"]
        shot_xg = row["shot_statsbomb_xg"]
        shot_outcome = row["shot_outcome"]
        body_part = row["shot_body_part"]

        if body_part == "Head":
            marker = "h"
        else:
            marker = "o"

        marker_size_scale = [50, 1000]
        marker_range = marker_size_scale[1] - marker_size_scale[0]

        marker_size = (shot_xg * marker_range) + marker_size_scale[0]

        if shot_outcome == "Goal":
            col = "palegreen"
            circle_z = 6
        else:
            col = "powderblue"
            circle_z = 4

        pitch.scatter(x=location_x, y=location_y,
                      color=col, zorder=circle_z, s=marker_size,
                      marker=marker,
                      edgecolor="black",
                      linewidth=.5, ax=ax)

    # legend
    pitch.scatter(x=-10, y=-10,
                  color="lightgrey", zorder=5, s=250,
                  marker="h",
                  edgecolor="black",
                  label="HEAD",
                  linewidth=.5, ax=ax)

    pitch.scatter(x=-10, y=-10,
                  color="lightgrey", zorder=5, s=250,
                  marker="o",
                  edgecolor="black",
                  label="FOOT",
                  linewidth=.5, ax=ax)

    ax.legend(bbox_to_anchor=(0.3, -0.2, 0.4, 0.5),
              loc='center', frameon=True, ncols=2, labelcolor='black',
              mode='expand', borderaxespad=.2, handlelength=1, handleheight=1, handletextpad=0.5,
              prop={"family": "avenir next condensed", "size": 12})
    # figure text
    fig.text(x=.5125, y=1, s=f"Shots".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=28, ha="center", va="center")

    fig.text(x=.5125, y=.95,
             s=f"{focus_player_name} Shots for {focus_player_team} at {focus_player_competition}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=10, ha="center", va="center")

    fig.text(x=.5125, y=.06,
             s=f"SIZE OF MARKERS REPRESENTS THE xG OF THE CHANCE",
             color=title_text_color,
             family="avenir",
             fontsize=10, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_shot_maps_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


player_shot_maps(6655)
