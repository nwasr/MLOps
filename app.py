import pickle
import os
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# --------------------------
# Load the trained model
# --------------------------

MODEL_PATH = "model/iris_model.pkl"
if not os.path.exists(MODEL_PATH):
    raise Exception(
        "Model file not found. Make sure to train the model by running 'train.py'."
    )

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# Class label mapping
IRIS_CLASSES = {
    0: "Setosa",
    1: "Versicolor",
    2: "Virginica"
}

# --------------------------
# Health and Readiness Probes
# --------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/ready")
def ready():
    try:
        if model is None:
            return jsonify({"ready": False}), 500
        return jsonify({"ready": True}), 200
    except Exception as e:
        return jsonify({"ready": False, "error": str(e)}), 500


# --------------------------
# Main UI Page
# --------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------
# Prediction Route
# --------------------------

@app.route("/predict", methods=["POST"])
def predict():
    try:
        features = [float(x) for x in request.form.values()]
        prediction = model.predict([features])[0]

        # Convert numeric output into Iris class name
        class_name = IRIS_CLASSES.get(prediction, "Unknown")

        return render_template(
            "index.html",
            prediction_text=f"Predicted Iris Class: {class_name}"
        )

    except Exception as e:
        return render_template(
            "index.html",
            prediction_text=f"Error: {str(e)}"
        )


# --------------------------
# Run the Flask App
# --------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
