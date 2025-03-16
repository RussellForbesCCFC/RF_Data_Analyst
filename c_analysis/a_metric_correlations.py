import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from helpers.position_group_metrics import profile_metrics_dict


def metric_correlation_check(profile, position_group):
    data_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_aggregated_data.csv")

    data_df = data_df[(data_df["total_time_minutes"] >= 300) & (data_df["position_group"] == position_group)]

    position_group_metrics_as_list = [i for i in profile_metrics_dict[profile].keys()]

    # correlation check
    filtered_data_df = data_df[position_group_metrics_as_list]

    plt.figure(figsize=(15, 6))

    # Create a mask for the upper triangle
    correlation_matrix = filtered_data_df.corr()

    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))

    # Store heatmap object in a variable to easily access it when you want to include more features (such as title).
    # Set the range of values to be displayed on the colormap from -1 to 1, and set the annotation to True to display the correlation values on the heatmap.
    heatmap = sns.heatmap(filtered_data_df.corr(), vmin=-1, vmax=1, annot=True, cmap="RdBu", linewidths=.5,
                          square=True, mask=mask, cbar_kws={"shrink": .75}, annot_kws={"size": 7})

    # Give a title to the heatmap. Pad defines the distance of the title from the top of the heatmap.
    heatmap.set_title(f'{profile}-{position_group}', fontdict={'fontsize': 12}, pad=12)

    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/{profile}_metric_correlations",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


metric_correlation_check("box_to_box", "Central / Defensive Midfielder")
