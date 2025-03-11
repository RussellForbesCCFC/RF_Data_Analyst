import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from a_metric_correlations import full_metric_list, metric_groups

from helpers.helper_dictionaries import metric_renames


def cluster_players(position_group_list):
    data_df = pd.read_csv(
        "/a_data/b_aggregated_data/player_aggregated_data.csv")

    data_df = data_df[
        (data_df["total_time_minutes"] >= 180)
        & (data_df["position_group"].isin(position_group_list))]

    # basic cluster analysis to try and identify groups within the wider position group
    X = data_df[full_metric_list]
    kmeans = KMeans(3)
    kmeans.fit(X)
    identified_clusters = kmeans.fit_predict(X)

    data_df["player_cluster_group"] = identified_clusters

    # elbow method to check for number of clusters - 3 seems appropriate
    wcss = []
    for i in range(1, data_df.shape[0] + 1):
        kmeans = KMeans(i)
        kmeans.fit(X)
        wcss_iter = kmeans.inertia_
        wcss.append(wcss_iter)

    num_clusters = range(1, data_df.shape[0] + 1)
    plt.plot(num_clusters, wcss)
    # plt.show()

    full_metric_list_with_player = full_metric_list.copy()
    insert_metrics = ["player_id", "player", "competition_name",
                      "team", "total_time_minutes", "player_90s_played",
                      "player_cluster_group"]
    insert_metrics = insert_metrics[::-1]
    for i in insert_metrics:
        full_metric_list_with_player.insert(0, i)

    # print(data_df[full_metric_list_with_player].to_string())
    # produce radars for what each cluster looks like - get an idea if one is 'box-to-box'

    # add player percentiles to show on radars
    for metric in full_metric_list:
        data_df[f"{metric}_percentile"] = data_df[metric].rank(pct=True, ascending=True)

    # base figure
    fig = plt.figure(figsize=(22, 10), dpi=100)

    in_poss_metrics = metric_groups["in_possession"]

    # create a radar for each cluster
    for i in range(0, 3):
        ax = fig.add_subplot(1, 3, i + 1, projection='polar')
        ax.set_title(f"group {i}".upper(), y=1.125,
                     family="avenir next condensed", fontsize=20, ha="center", va="center")

        players_in_group = data_df[
            (data_df["player_cluster_group"] == i)]

        print(f"GROUP {i}")
        print(players_in_group[["player", "team", "competition_name"]].to_string())

        count_of_players = players_in_group.shape[0]

        ax.text(x=0, y=1.2, s=f"Players: {count_of_players}", ha="center", va="center", family="avenir")

        ax.set_theta_offset(np.deg2rad(90))
        ax.set_theta_direction(-1)
        ax.spines['polar'].set_edgecolor('black')

        ax.set_yticks([])
        ax.set_xticks([])
        ax.set_yticklabels([])
        ax.set_xticklabels([])

        ax.set_ylim(-0.25, 1)

        # Edge Circle
        theta = np.linspace(0, 2 * np.pi, 100)
        r = np.ones(100)

        ax.plot(theta, r * .2, color="#FEFAF1",
                linewidth=1, alpha=1, zorder=3)
        ax.plot(theta, r * .4, color="#FEFAF1",
                linewidth=1, alpha=1, zorder=3)
        ax.plot(theta, r * .6, color="#FEFAF1",
                linewidth=1, alpha=1, zorder=3)
        ax.plot(theta, r * .8, color="#FEFAF1",
                linewidth=1, alpha=1, zorder=3)

        indexes = list(range(0, len(full_metric_list)))
        width = 2 * np.pi / len(full_metric_list)
        angles = [element * width for element in indexes]

        ax.bar(x=angles, height=1, width=width,
               edgecolor='#FEFAF1', zorder=1, alpha=.24, color="#FEFAF1")

        # clear bars for edges - these can overlay everything else
        ax.bar(x=angles, height=1, width=width,
               edgecolor='black', zorder=5, alpha=1, color="none")

        for n, met in enumerate(full_metric_list):
            player_percentile_average = data_df[
                (data_df["player_cluster_group"] == i)][f"{met}_percentile"].mean()

            if met in in_poss_metrics:
                col = "powderblue"
            else:
                col = "indianred"

            angle_r = angles[n]

            ax.bar(x=angle_r, height=player_percentile_average, width=width,
                   edgecolor='black', zorder=2, alpha=.7, color=col)
            ax.bar(x=angle_r, height=player_percentile_average, width=width,
                   edgecolor='black', zorder=5, alpha=.7, color="none")

        # Adding column_names and data values
        for angle, metric_name in zip(angles, full_metric_list):
            rotation_angle = np.degrees(-angle)
            metric_rename = metric_renames[metric_name]
            player_percentile_average = data_df[
                (data_df["player_cluster_group"] == i)][f"{metric_name}_percentile"].mean()

            if 90 < np.degrees(angle) < 270:
                rotation_angle -= 180
                v_position = "top"
            else:
                rotation_angle -= 0
                v_position = "bottom"

            # column name
            ax.text(angle, 1.02, metric_rename.upper(),
                    ha='center', va=v_position,
                    rotation=rotation_angle, rotation_mode='anchor', fontsize=12, color="black",
                    family='avenir next condensed',
                    zorder=7)

            # average player percentile
            ax.text(angle, .9, f"{round(player_percentile_average, 1)}",
                    ha='center', va=v_position,
                    rotation=rotation_angle, rotation_mode='anchor', fontsize=10, color="black",
                    family='avenir next condensed',
                    zorder=7)

    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visulisations/cluster_group_radars",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


cluster_players(["Central / Defensive Midfielder"])
