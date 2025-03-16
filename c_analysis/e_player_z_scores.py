import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from helpers.position_group_metrics import profile_metrics_dict


def add_player_z_score(row, metric, df, weightings_dict):
    metric_weight = weightings_dict[metric]
    player_value = row[metric]
    metric_average = df[metric].mean()
    metric_std = df[metric].std()

    player_std_from_mean = (player_value - metric_average) / metric_std
    weighted_std_from_mean = player_std_from_mean * metric_weight

    return weighted_std_from_mean


def scale_weighted_average(row, df):
    player_z_weighted_average = row["z_score_weighted_average"]
    max_z_weighted = df["z_score_weighted_average"].max()
    min_z_weighted = df["z_score_weighted_average"].min()
    scaled_z_score = (player_z_weighted_average - min_z_weighted) / (max_z_weighted - min_z_weighted)
    return scaled_z_score


def create_player_z_scores(profile, position_group, min_minutes, focus_player_id):
    cmap_list = ["#FEFAF1", "#9cb7d8", "#1974b1"]
    cmap = LinearSegmentedColormap.from_list("", cmap_list)

    data_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_aggregated_data.csv")

    data_df = data_df[
        (data_df["total_time_minutes"] >= min_minutes)
        & (data_df["position_group"] == position_group)]

    focus_player_name = data_df[(data_df["player_id"] == focus_player_id)]["player"].iloc[0]

    position_group_metrics_as_list = [i for i in profile_metrics_dict[profile].keys()]
    metric_weightings = {}
    metric_renames = {}

    for p_m in position_group_metrics_as_list:
        weight = profile_metrics_dict[profile][p_m]["weight"]
        rename = profile_metrics_dict[profile][p_m]["rename"]
        metric_weightings[p_m] = weight
        metric_renames[p_m] = rename

    # adding percentiles and z-scores
    metric_z_score_names_weighted = []
    for met in position_group_metrics_as_list:
        data_df[f"{met}_z_score_weighted"] = data_df.apply(
            lambda _row: add_player_z_score(_row, met, data_df, metric_weightings), axis=1)
        metric_z_score_names_weighted.append(f"{met}_z_score_weighted")

    # checking min / max z scores
    # for name in metric_z_score_names_weighted:
    #     min_z_score = data_df[name].min()
    #     max_z_score = data_df[name].max()
    #     print(f"max {round(max_z_score, 2)} min {min_z_score}")

    # FIGURE
    fig = plt.figure(figsize=(18, 4), dpi=150)
    ax = fig.add_subplot()

    ax.set_xlim(0, len(metric_z_score_names_weighted) + .1)
    ax.set_ylim(-3.5, 3.5)

    # ax.yaxis.set_ticks([])
    ax.xaxis.set_ticks([])

    ax.grid(axis="y", color="black", ls="--", alpha=0.25)
    ax.set_ylabel("player z-score".upper(), family="avenir next condensed", fontsize=15)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # plot 0 line
    ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [0, 0],
            color="black", lw=.5, alpha=.75, zorder=1)

    # plot each metric and teams z-score
    x_start = 0.5
    for z_metric in position_group_metrics_as_list:
        metric_rename = metric_renames[z_metric]
        z_score_column_name = f"{z_metric}_z_score_weighted"

        ax.text(x=x_start, y=ax.get_ylim()[1], s=metric_rename.upper(),
                ha="center", va="bottom", family="avenir next condensed", fontsize=14)

        for index, row in data_df.iterrows():
            player_id = row["player_id"]
            player_z_score = row[z_score_column_name]
            player_value = row[z_metric]

            if player_id == focus_player_id:
                z_ref = 5
                size_ref = 350
                alpha_ref = 1
                color_ref = "powderblue"

                ax.text(x=x_start, y=player_z_score - 0.55,
                        s=f"{round(player_value, 2)}", ha="center", va="center", zorder=5,
                        bbox=dict(facecolor=color_ref, alpha=1, boxstyle='round,pad=0.2'),
                        family="avenir next condensed", fontsize=14)

            else:
                z_ref = 3
                size_ref = 100
                alpha_ref = 0.6
                color_ref = "lightgrey"

            ax.scatter(x=x_start, y=player_z_score, s=size_ref,
                       color=color_ref, edgecolor="black", lw=.5, zorder=z_ref, alpha=alpha_ref)

        x_start += 1

    fig.text(x=.5125, y=1.15, s=f"{focus_player_name} - {profile.replace('_', ' ')}".upper(),
             color="black",
             family="avenir next condensed",
             fontsize=26, ha="center", va="center")

    fig.text(x=.5125, y=1.05,
             s=f"z-scores of {focus_player_name} Compared to {position_group}s in Euro 2024 and Copa America 2024\n"
               f"min {min_minutes} Minutes".upper(),
             color="black",
             family="avenir",
             fontsize=12, ha="center", va="center")

    ax.set_facecolor("#FEFAF1")
    fig.set_facecolor("None")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_z_scores_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=True)

    plt.close()


create_player_z_scores("box_to_box", "Central / Defensive Midfielder", 300, 6655)
