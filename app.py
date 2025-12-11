import os
import pickle
import logging
import json
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# structured logger to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('iris_app')

MODEL_PATH = "model/iris_model.pkl"
if not os.path.exists(MODEL_PATH):
    raise Exception("Model file not found. Run train.py or ensure CI has produced the artifact.")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/predict", methods=["POST"])
def predict():
    # Get the input features from the form
    try:
        raw_values = list(request.form.values())
        features = [float(x) for x in raw_values]
    except Exception:
        return render_template("index.html", prediction_text="Invalid input. Provide 4 numeric features."), 400

    if len(features) != 4:
        return render_template("index.html", prediction_text="Provide exactly 4 features."), 400

    try:
        prediction = int(model.predict([features])[0])
    except Exception as e:
        logger.error(json.dumps({"event": "prediction_error", "error": str(e)}))
        return render_template("index.html", prediction_text="Prediction failed."), 500

    logger.info(json.dumps({"event": "prediction", "features": features, "prediction": prediction}))
    return render_template("index.html", prediction_text=f"Predicted Iris Class: {prediction}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
