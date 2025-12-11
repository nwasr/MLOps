# tests/test_model.py
import os
import subprocess
import pickle
import numpy as np

MODEL_PATH = "model/iris_model.pkl"

def ensure_model():
    # If model missing, train it in-place (idempotent)
    if not os.path.exists(MODEL_PATH):
        # Use python3 explicitly in CI
        subprocess.check_call(["python3", "train.py"])

# Ensure model exists before importing app (so app doesn't raise on import)
ensure_model()

# import app after model exists
from app import app  # noqa: E402 (import after non-import code intentionally)

def test_model_prediction():
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    input_data = [5.1, 3.5, 1.4, 0.2]
    prediction = model.predict([input_data])
    assert prediction is not None
    assert isinstance(prediction[0], (int, np.integer))

def test_flask_predict():
    # app already loaded after ensure_model()
    with app.test_client() as client:
        form_data = {
            'sepal_length': 5.1,
            'sepal_width': 3.5,
            'petal_length': 1.4,
            'petal_width': 0.2
        }
        response = client.post('/predict', data=form_data)
        assert response.status_code == 200
        assert 'Predicted Iris Class' in response.get_data(as_text=True)
