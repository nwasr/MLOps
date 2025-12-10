import pickle
import os
from flask import Flask, request, render_template

app = Flask(__name__)

# Load the model
MODEL_PATH = "model/iris_model.pkl"
if not os.path.exists(MODEL_PATH):
    raise Exception(
        "Model file not found. Make sure to train the model by running 'train.py'."
    )

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# Home route to display the form
@app.route("/")
def home():
    return render_template("index.html")


# Prediction route to handle form submissions
@app.route("/predict", methods=["POST"])
def predict():
    # Get the input features from the form
    features = [float(x) for x in request.form.values()]

    # Make a prediction using the model
    prediction = model.predict([features])[0]

    # Display the prediction on the same page
    return render_template(
        "index.html", prediction_text=f"Predicted Iris Class: {prediction}"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
