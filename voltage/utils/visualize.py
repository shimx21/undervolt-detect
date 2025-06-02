import matplotlib.pyplot as plt
import os, pickle, keras, json
from keras.utils import plot_model

import visualkeras
from PIL import ImageFont

def load_model(load_dir):
    model = keras.models.load_model(os.path.join(load_dir, "model.keras"))
    return model

def load_history(load_dir) -> keras.callbacks.History:
    with open(os.path.join(load_dir, "history.pkl"), "rb") as fp:
        history = pickle.load(fp)
    return history

def plot_training_history(dir: str):
    """
    Plot the training history from a model dir.
    """
    history = load_history(dir)
    # os.makedirs(os.path.join(dir, "figures"), exist_ok=True)
    # for key in history.history.keys():
    #     if key.startswith("val_"): continue
    #     plt.plot(history.history[key])
    #     plt.plot(history.history["val_" + key])
    #     plt.title(f'Model {dir} {key}')
    #     plt.ylabel(key)
    #     plt.xlabel('Epoch')
    #     plt.legend(['Train', 'Test'], loc='upper left')
    #     plt.savefig(os.path.join(dir, "figures", f"{key}.png"))
    #     plt.close()
    
    import json
    with open(os.path.join(dir, "history.json"), "w") as fp:
        json.dump(history.history, fp, indent=4)

def plot_model_from(dir):
    plot_model(
        load_model(dir),
        to_file=os.path.join(dir, "figures", "model.png"),
        show_shapes=False,
        show_layer_names=False
    )

def text_callable(layer_index, layer):
    # Every other piece of text is drawn above the layer, the first one below
    above = bool(layer_index%2)

    # Get the output shape of the layer
    output_shape = [x for x in list(layer.output_shape) if x is not None]

    # If the output shape is a list of tuples, we only take the first one
    if isinstance(output_shape[0], tuple):
        output_shape = list(output_shape[0])
        output_shape = [x for x in output_shape if x is not None]

    # Variable to store text which will be drawn    
    output_shape_txt = ""

    # Create a string representation of the output shape
    for ii in range(len(output_shape)):
        output_shape_txt += str(output_shape[ii])
        if ii < len(output_shape) - 2: # Add an x between dimensions, e.g. 3x3
            output_shape_txt += "x"
        if ii == len(output_shape) - 2: # Add a newline between the last two dimensions, e.g. 3x3 \n 64
            output_shape_txt += "\n"

    # Add the name of the layer to the text, as a new line
    output_shape_txt += f"\n{layer.name}"

    # Return the text value and if it should be drawn above the layer
    return output_shape_txt, above

def plot_beauty_model(dir):
    model = load_model(dir)
    fname = os.path.join(dir, "figures", "model_beauty.png")
    print(fname)
    
    module = visualkeras.layered_view(
        model,
        to_file=fname,
        # text_callable=text_callable,
        legend=True,
        font=ImageFont.truetype("DejaVuSans.ttf", 12),
        spacing=20,
        # draw_volume=False,
    )

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python visualize.py [model|history] <dir>")
        sys.exit(1)
    pth = sys.argv[2]
    
    if sys.argv[1] == "model":
        # plot_model_from(pth)
        plot_beauty_model(pth)
    elif sys.argv[1] == "history":
        plot_training_history(pth)
    else:
        print("Unknown command, use 'model' or 'history'.")
        sys.exit(1)
    