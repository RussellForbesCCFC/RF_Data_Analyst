import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from highlight_text import ax_text
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as path_effects

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import (get_start_locations, get_pass_end_locations,
                                      calculate_action_distance,
                                      assign_zone_to_start_thirds, assign_zone_to_pass_carry_shot_thirds)


def player_final_third_passes(focus_player_id):
    positive_cmap_list = ["#FEFAF1", "#9cb7d8", "#1974b1"]
    positive_cmap = LinearSegmentedColormap.from_list("", positive_cmap_list)
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

    focus_player_open_play_pass_events_df = player_events_df[
        (player_events_df["player_id"] == focus_player_id)
        & (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

    focus_player_name = focus_player_open_play_pass_events_df["player"].iloc[0]
    focus_player_open_play_pass_counts = focus_player_open_play_pass_events_df.shape[0]

    focus_player_open_play_pass_events_df[['location_x', 'location_y']] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

    focus_player_open_play_pass_events_df[
        ['end_location_x', 'end_location_y']] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(get_pass_end_locations(_row_)), axis=1)

    focus_player_open_play_pass_events_df[["start_zone", "end_zone"]] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(assign_zone_to_pass_carry_shot_thirds(_row_)), axis=1)

    focus_player_name = focus_player_open_play_pass_events_df["player"].iloc[0]

    final_third_passes = focus_player_open_play_pass_events_df[
        (focus_player_open_play_pass_events_df["location_x"] >= 80)].copy()

    final_third_passes["pass_outcome"] = final_third_passes["pass_outcome"].fillna("complete")

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

    fig = plt.figure(figsize=(12, 5), dpi=100)
    title_text_color = "black"

    zone_loop_dict = {"start_zone": "Start Locations",
                      "end_zone": "End Locations"}
    zone_loop_list = [i for i in zone_loop_dict.keys()]

    ax = fig.add_subplot()

    pitch = VerticalPitch(pitch_type="statsbomb",
                          pitch_color='none',
                          half=True, line_zorder=2, corner_arcs=True,
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

    zone = "start_zone"
    zone_reference_counts = final_third_passes[zone].value_counts().reset_index()
    max_start_zone = zone_reference_counts["count"].max()

    for index, row in zone_reference_counts.iterrows():
        zone_ref = row[zone]
        count = row["count"]
        count_per_max = (count / max_start_zone)

        # Shading the Zone
        zone_reference = zone_df[zone_df["zone_name"] == zone_ref]

        x_start = zone_reference["x_start"].iloc[0]
        y_start = zone_reference["y_start"].iloc[0]

        x_end = zone_reference["x_end"].iloc[0]
        y_end = zone_reference["y_end"].iloc[0]

        x_center = zone_reference["x_center"].iloc[0]
        y_center = zone_reference["y_center"].iloc[0]

        c_fill = positive_cmap(count_per_max)

        ax.fill_between([x_start, x_end],
                        y_start, y_end,
                        color=c_fill, alpha=.6, zorder=1, linewidth=0, edgecolor="white")

        zone_percentage = count / final_third_passes.shape[0]
        zone_percentage_string = f"{int(round(zone_percentage * 100))}%"
        # ax.text(x=x_center, y=y_center, s=zone_percentage_string,
        #         ha="center", va="center", family="avenir next condensed", fontsize=16,
        #         color="#fefaf1",
        #         path_effects=[path_effects.Stroke(linewidth=2, foreground="black", alpha=1),
        #                       path_effects.Normal()])

    for _index, _row in final_third_passes.iterrows():
        location_x = _row["location_x"]
        location_y = _row["location_y"]
        end_location_x = _row["end_location_x"]
        end_location_y = _row["end_location_y"]
        pass_outcome = _row["pass_outcome"]
        if pass_outcome == "complete":
            line_color = "palegreen"
        else:
            line_color = "indianred"

        pitch.arrows(location_x, location_y,
                     end_location_x, end_location_y,
                     color=line_color, ec='black', linewidth=.5,
                     ax=ax, width=1.5, headwidth=4.5, headlength=4.5, alpha=.25, zorder=2)

    # FIGURE
    fig.text(x=.5125, y=.955, s=f"Final Third Passes".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=28, ha="center", va="center")

    fig.text(x=.5125, y=.915,
             s=f"Pitch Shows the start locations of passes made in the final third by {focus_player_name}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=10, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_final_third_passes_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


player_final_third_passes(6655)
