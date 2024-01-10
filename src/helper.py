import matplotlib.pyplot as plt
import json
from IPython import display

plt.ion()

def plot(scores, mean_scores, y_label="Score", x_label = "Number of Games", title="Score over games"):
    display.clear_output(wait=True)
    display.display(plt.gcf())
    plt.clf()
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.plot(scores)
    plt.plot(mean_scores)
    plt.ylim(ymin=0)
    plt.text(len(scores)-1, scores[-1], str(scores[-1]))
    plt.text(len(mean_scores)-1, mean_scores[-1], str(mean_scores[-1]))
    plt.show(block=False)
    plt.pause(.1)




def save_values(
        plot_scores, 
        plot_mean_scores, 
        plot_reward, 
        plot_mean_reward, 
        n_games, 
        record, 
        record_reward,
        filename='training_data.json'
):
    data = {
        'plot_scores': plot_scores,
        'plot_mean_scores': plot_mean_scores,
        'plot_reward': plot_reward,
        'plot_mean_reward': plot_mean_reward,
        'n_games': n_games,
        'record': record,
        "record_reward": record_reward,
    }
    with open(filename, 'w') as f:
        json.dump(data, f)
    
    plot(plot_scores, plot_mean_scores, y_label="Score", x_label = "Number of Games", title="Score over games")


def load_values(filename='training_data.json'):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return (data['plot_scores'], data['plot_mean_scores'], data['plot_reward'], 
                data['plot_mean_reward'], data['n_games'], data['record'], data['record_reward'])
    except FileNotFoundError:
        # Return default values if file not found
        return ([], [], [], [], 0, 0, 0)