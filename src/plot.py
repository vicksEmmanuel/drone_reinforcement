

from helper import load_values, plot


plot_scores, plot_mean_scores, plot_reward, plot_mean_reward, n_games, record = load_values()


plot(plot_scores, plot_mean_scores, y_label="Score", x_label = "Number of Games", title="Score over games")
# plot(plot_reward, plot_mean_reward, y_label="Reward", x_label = "Number of Games", title="Reward over games")