import json
import numpy as np
import mysql.connector
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model


def predict(model, data_path):
    with open(data_path, "r") as fp:
        data = json.load(fp)

    X = np.array(data["mfcc"])
    # perform prediction
    prediction = model.predict(X) #come out a 2d array, each element is the score for diff genre
    print(prediction)

    # get index with max value
    predicted_index = np.argmax(prediction, axis=1)
    return predicted_index

def save_prediction(file_name,prediction): # fileneame must exist in database
    conn = mysql.connector.connect(user='9rBnbH2yWN', password='obqUHk85vy', host='remotemysql.com', database='9rBnbH2yWN')
    cursor = conn.cursor()
    cursor.execute("UPDATE test SET normal = %s WHERE filename = %s",(prediction,file_name))
    conn.commit()
    conn.close()

# load saved model
#load_options = tf.saved_model.LoadOptions(experimental_io_device='/job:localhost')

    
    


