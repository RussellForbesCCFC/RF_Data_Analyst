import pandas as pd


def create_player_per_90_data():
    player_minute_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_minutes.csv").set_index(
        ["player_id", "player", "position_group", "competition_name", "team"])

    player_minute_df["player_90s_played"] = player_minute_df["total_time_minutes"] / 90

    player_metric_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_metric_totals.csv").set_index(
        ["player_id", "player", "position_group", "competition_name", "team"])

    player_aggregated_df = pd.concat([player_minute_df, player_metric_df], axis=1).reset_index().drop(
        columns="Unnamed: 0")

    player_aggregated_df["deep_progressions"] = (
            player_aggregated_df["carries_into_final_third"] +
            player_aggregated_df["passes_into_final_third"])

    player_aggregated_df["total_np_xg_plus_op_xga"] = player_aggregated_df[
        ["total_np_xg", "open_play_xga"]].sum(axis=1)

    player_aggregated_df = player_aggregated_df[(player_aggregated_df["total_time_minutes"] >= 90)]

    per_90_columns = player_aggregated_df.columns.tolist()
    exclude_from_per_90_columns = ["player_id", "player", "position_group", "competition_name",
                                   "team", "total_time_minutes", "player_90s_played", "expected_completed_passes"]

    for exc_col in exclude_from_per_90_columns:
        per_90_columns.remove(exc_col)

    for per_90_col in per_90_columns:
        player_aggregated_df[f"{per_90_col}_per_90"] = (
                player_aggregated_df[per_90_col] /
                player_aggregated_df["player_90s_played"])

    # ratio metrics
    player_aggregated_df["pass_completion_ratio"] = (
            player_aggregated_df["completed_passes"] /
            player_aggregated_df["total_passes"])

    player_aggregated_df["expected_pass_completion_ratio"] = (
            player_aggregated_df["expected_completed_passes"] /
            player_aggregated_df["total_passes"])

    player_aggregated_df["difference_to_expected_pass_completion_ratio"] = (
            player_aggregated_df["pass_completion_ratio"] -
            player_aggregated_df["expected_pass_completion_ratio"])

    player_aggregated_df["tackle_ratio"] = (
            player_aggregated_df["successful_tackles"] /
            player_aggregated_df["total_tackles"])

    player_aggregated_df["ball_retention_under_pressure"] = (
            player_aggregated_df["ball_retained_under_pressure"] /
            (player_aggregated_df["ball_lost_under_pressure"] +
             player_aggregated_df["ball_retained_under_pressure"]))

    player_aggregated_df["open_play_forward_pass_percentage"] = (
            player_aggregated_df["open_play_forward_passes"] /
            player_aggregated_df["open_play_total_passes"])

    player_aggregated_df.to_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_aggregated_data.csv")

    player_aggregated_df.to_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/d_shiny_app/player_aggregated_data.csv")


create_player_per_90_data()
