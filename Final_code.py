from sklearn.metrics import r2_score, mean_squared_error
import numpy as np
import pandas as pd

import datetime

from sklearn.cluster import KMeans
from matplotlib import pyplot as plt
import seaborn as sns

import time

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression


import paho.mqtt.client as mqtt
import json




import os.path

file_path = 'predictions.csv'
if os.path.exists(file_path):
    data = pd.read_csv(file_path)
else:
    print(f"Error: File '{file_path}' not found.")


# Split X_data and y_data into individual columns
X_columns = ['current', 'voltage', 'temperature', 'humidity', 'vibration']
y_columns = ['current_aft5', 'volt_aft5', 'temp_aft5', 'hum_aft5', 'vib_aft5']

X_data = data[X_columns]
y_data = data[y_columns]

# Initialize empty dictionaries to store the models and predictions
models = {}
predicted_values = {}

# Train separate linear regression models for each pair of X and y columns
for i, (X_col, y_col) in enumerate(zip(X_columns, y_columns)):
    # Train the model
    model = LinearRegression()
    model.fit(X_data[[X_col]], y_data[[y_col]])
    models[i] = model

    # Predict using the test set
    y_pred = model.predict(X_data[[X_col]])
    predicted_values[y_col] = y_pred

    # Evaluate the model
    r_squared = r2_score(y_data[[y_col]], y_pred)
    mse = mean_squared_error(y_data[[y_col]], y_pred)
    print(f"For column {y_col}:")
    print(f"  R-squared: {r_squared}")
    print(f"  Mean Squared Error: {mse}")

def create_X_new(test_data, i):
    X_new = pd.DataFrame({
        'current': [float(test_data['sensor/Current'][i])],
        'voltage': [float(test_data['sensor/Voltage'][i])],
        'temperature': [float(test_data['sensor/DHT11/temperature_celsius'][i])],
        'humidity': [float(test_data['sensor/DHT11/humidity'][i])],
        'vibration': [float(test_data['sensor/vibration'][i])]
        # Add values for other columns...
    })
    result = predict_values(X_new)
    system_status = "System works"
    if (result['current_aft5'] > max(data['current']) + 2
            or result['volt_aft5'] > max(data['voltage']) + 100
            or result['temp_aft5'] > max(data['temperature']) + 5
            or result['hum_aft5'] > max(data['humidity']) + 20
            or result['vib_aft5'] > max(data['vibration']) + 1):
        system_status = "System fails"
    
    # Print the system status
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Include date and time in the system status message
    system_status_with_time = f"{current_time}: {system_status}"

    # Print the system status with time
    print(system_status_with_time)

    # Publish the system status with time to an MQTT topic
    client.publish("system_status", system_status_with_time)


def predict_values(X_new):
    predicted_values = {}
    for i, (X_col, y_col) in enumerate(zip(X_columns, y_columns)):
        # Get the corresponding model for the pair of X and y columns
        model = models[i]
        predicted_values[y_col] = float((model.predict(X_new[[X_col]]))[0][0])
    
    return predicted_values


i = 0
test = []
test_data = {
    'sensor/Current': [],
    'sensor/Voltage': [],
    'sensor/DHT11/temperature_celsius': [],
    'sensor/DHT11/humidity': [],
    'sensor/vibration': []
}
count = 0
test1=0

def on_message(client, userdata, message):
    global i, test, test_data, count ,test1
    data = json.loads(message.payload.decode("utf-8"))
    topic = message.topic

    # Append data to the respective topic in test_data
    if (i < 5):
        topic = message.topic
        test_data[topic] = [data]
        i += 1
        if (i == 5):
            i = 0
            # count += 1
            # print("\n\nFor count = ", count,end="\n")
            # print(test_data,end="\n\n")
            # print("system status :",)
            create_X_new(test_data, i)
            test_data = {key: [] for key in topics}
            test1+=1


# Set up MQTT client
client = mqtt.Client()
client.on_message = on_message

# Connect to the MQTT broker
client.connect("192.168.196.23", 1883)
topics = ["sensor/Current", "sensor/Voltage", "sensor/DHT11/temperature_celsius",
          "sensor/DHT11/humidity",  "sensor/vibration"]

 # Add your topics here

for topic in topics:
    client.subscribe(topic)

# Start the MQTT loop to receive messages
client.loop_forever()