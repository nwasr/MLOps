import pytest
import pickle
import numpy as np
from app import app 

# Load your model
with open("model/iris_model.pkl", "rb") as f:
    model = pickle.load(f)

def test_model_prediction():
    # Example test case to check model predictions
    input_data = [5.1, 3.5, 1.4, 0.2]  # Example iris data input
    prediction = model.predict([input_data])
    assert prediction is not None  # Ensure prediction is not empty
    assert isinstance(prediction[0], (int, np.integer))  # Check if the prediction is an integer (for classification)

def test_flask_predict():
    # Create a test client for the Flask app
    with app.test_client() as client:
        # Define form data as a dictionary matching expected form field names
        form_data = {
            'sepal_length': 5.1,
            'sepal_width': 3.5,
            'petal_length': 1.4,
            'petal_width': 0.2
        }
        
        # Send a POST request to the /predict route with form data
        response = client.post('/predict', data=form_data)
        
        # Check if the response contains the expected output
        assert response.status_code == 200
        assert 'Predicted Iris Class' in response.get_data(as_text=True)