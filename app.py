import pickle
import os
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Load the model
MODEL_PATH = "model/iris_model.pkl"
if not os.path.exists(MODEL_PATH):
    raise Exception(
        "Model file not found. Make sure to train the model by running 'train.py'."
    )

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# --------------------------
# Health and Readiness Probes
# --------------------------

@app.route("/health")
def health():
    # Basic check to ensure the server is running
    return jsonify({"status": "ok"}), 200


@app.route("/ready")
def ready():
    try:
        # Minimal readiness check: model loaded?
        if model is None:
            return jsonify({"ready": False}), 500
        return jsonify({"ready": True}), 200
    except Exception as e:
        return jsonify({"ready": False, "error": str(e)}), 500


# Home route to display the form
@app.route("/")
def home():
    return render_template("index.html")


# Prediction route to handle form submissions
@app.route("/predict", methods=["POST"])
def predict():
    # Get the input features from the form
    features = [float(x) for x in request.form.values()]
    prediction = model.predict([features])[0]

    return render_template(
        "index.html", prediction_text=f"Predicted Iris Class: {prediction}"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
