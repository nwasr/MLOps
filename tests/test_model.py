import os
import pickle
import numpy as np
import subprocess
from app import app

MODEL_PATH = "model/iris_model.pkl"

def ensure_model():
    if not os.path.exists(MODEL_PATH):
        # train locally
        subprocess.check_call(["python", "train.py"])

def test_model_prediction():
    ensure_model()
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    input_data = [5.1, 3.5, 1.4, 0.2]
    prediction = model.predict([input_data])
    assert prediction is not None
    assert isinstance(prediction[0], (int, np.integer))

def test_flask_predict():
    ensure_model()
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
