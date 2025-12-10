import pickle
import os
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load the Iris dataset
iris = load_iris()
X, y = iris.data, iris.target

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train a Random Forest model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Create the 'model' directory if it doesn't exist
os.makedirs("model", exist_ok=True)

# Save the trained model to a file
with open("model/iris_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")
