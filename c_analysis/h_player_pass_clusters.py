import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from highlight_text import ax_text
from matplotlib.colors import LinearSegmentedColormap

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import get_start_locations, get_carry_end_locations, get_pass_end_locations, \
    calculate_action_distance


def create_player_pass_map(focus_player_id):
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

    focus_player_open_play_pass_events_df = player_events_df[
        (player_events_df["player_id"] == focus_player_id)
        & (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

    focus_player_open_play_pass_events_df[['location_x', 'location_y']] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

    focus_player_open_play_pass_events_df[
        ['end_location_x', 'end_location_y']] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(get_pass_end_locations(_row_)), axis=1)

    focus_player_name = focus_player_open_play_pass_events_df["player"].iloc[0]
    focus_player_open_play_pass_counts = focus_player_open_play_pass_events_df.shape[0]

    # only filter where the pass cluster probability is over 60%
    focus_player_open_play_pass_events_df_with_clusters = focus_player_open_play_pass_events_df[
        (focus_player_open_play_pass_events_df["pass_pass_cluster_probability"] > .6)]

    focus_player_cluster_counts = focus_player_open_play_pass_events_df_with_clusters[
        "pass_pass_cluster_id"].value_counts().reset_index()

    # print(focus_player_open_play_pass_events_df.head().to_string())
    # print(focus_player_open_play_pass_events_df.shape[0])

    fig = plt.figure(figsize=(20, 20), dpi=100)
    title_text_color = "black"

    ax_counter = 1
    for index, row in focus_player_cluster_counts.head(6).iterrows():
        ax = fig.add_subplot(2, 3, ax_counter)

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

        pass_id = row["pass_pass_cluster_id"]
        passes_in_cluster = focus_player_open_play_pass_events_df_with_clusters[
            (focus_player_open_play_pass_events_df_with_clusters["pass_pass_cluster_id"] == pass_id)]

        pass_cluster_name = passes_in_cluster["pass_pass_cluster_label"].iloc[0]
        pass_cluster_name_split = pass_cluster_name.split(" - ")

        total_passes_in_cluster = passes_in_cluster.shape[0]
        pitch_title = (f"{pass_cluster_name_split[0]} - {pass_cluster_name_split[4]}\n"
                       f"<Total Passes: {total_passes_in_cluster}>")

        ax_text(x=40, y=126, s=pitch_title.upper(),
                color=title_text_color, highlight_textprops=[{"family": "avenir", "fontsize": 15}],
                textalign="center", vsep=2,
                ha="center", va="center", family="avenir next condensed", fontsize=20)

        pitch.arrows(passes_in_cluster["location_x"], passes_in_cluster["location_y"],
                     passes_in_cluster["end_location_x"], passes_in_cluster["end_location_y"],
                     color="powderblue", ec='black', linewidth=.5,
                     ax=ax, width=2, headwidth=4.5, headlength=4.5, alpha=1, zorder=2)

        ax_counter += 1

    # FIGURE
    fig.text(x=.5125, y=.95, s=f"Most Common Pass Types".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=50, ha="center", va="center")

    fig.text(x=.5125, y=.925,
             s=f"Pitches Show the 6 most common pass types played by {focus_player_name}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=22, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_all_passes_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


# create_player_pass_map(6655)

def pass_clusters_by_pitch_thirds(focus_player_id, pitch_third):
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

    focus_player_open_play_pass_events_df = player_events_df[
        (player_events_df["player_id"] == focus_player_id)
        & (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

    focus_player_open_play_pass_events_df[['location_x', 'location_y']] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

    focus_player_open_play_pass_events_df[
        ['end_location_x', 'end_location_y']] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(get_pass_end_locations(_row_)), axis=1)

    focus_player_name = focus_player_open_play_pass_events_df["player"].iloc[0]
    focus_player_open_play_pass_counts = focus_player_open_play_pass_events_df.shape[0]

    fig = plt.figure(figsize=(20, 16), dpi=100)
    title_text_color = "black"

    third_shading = {"Defensive Third": [-0.1, 40],
                     "Middle Third": [40, 80],
                     "Final Third": [80, 120]}

    third_start = third_shading[pitch_third][0]
    third_end = third_shading[pitch_third][1]

    # only filter where the pass cluster probability is over 60%
    focus_player_open_play_pass_events_df_with_clusters = focus_player_open_play_pass_events_df[
        (focus_player_open_play_pass_events_df["pass_pass_cluster_probability"] > .6)
        & (focus_player_open_play_pass_events_df["location_x"] > third_start)
        & (focus_player_open_play_pass_events_df["location_x"] <= third_end)]

    focus_player_cluster_counts = focus_player_open_play_pass_events_df_with_clusters[
        "pass_pass_cluster_id"].value_counts().reset_index()

    ax = fig.add_subplot()

    pitch = VerticalPitch(pitch_type="statsbomb",
                          pitch_color='none',
                          half=False, line_zorder=2, corner_arcs=True,
                          linewidth=1, line_alpha=1, line_color='black',
                          pad_left=0, pad_right=0, pad_bottom=0, pad_top=0)

    pitch.draw(ax=ax)

    ax.fill_between([0, 80],
                    third_shading[pitch_third][0],
                    third_shading[pitch_third][1],
                    color="lightgrey")

    ax.set_facecolor("#FEFAF1")

    x_plot_points = [18, 30, 50, 62]
    y_plot_points = [18, 40, 60, 80, 102]
    for y in y_plot_points:
        ax.plot([0, 80], [y, y], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

    for x in x_plot_points:
        ax.plot([x, x], [0.1, 120], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

    pitch.arrows(focus_player_open_play_pass_events_df_with_clusters["location_x"],
                 focus_player_open_play_pass_events_df_with_clusters["location_y"],
                 focus_player_open_play_pass_events_df_with_clusters["end_location_x"],
                 focus_player_open_play_pass_events_df_with_clusters["end_location_y"],
                 color="powderblue", ec='black', linewidth=.5,
                 ax=ax, width=2, headwidth=4.5, headlength=4.5, alpha=1, zorder=2)

    # FIGURE
    fig.text(x=.5125, y=.95, s=f"{pitch_third}".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=50, ha="center", va="center")

    fig.text(x=.5125, y=.915,
             s=f"Pitches Show the 5 most common pass types"
               f"\nplayed by {focus_player_name} in the {pitch_third}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=20, ha="center", va="center")

    fig.set_facecolor("none")
    third_title = pitch_third.replace(" ", "_")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_pass_clusters_by_pitch_thirds_{focus_player_id}_{third_title}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()

# pass_clusters_by_pitch_thirds(6655, "Defensive Third")
