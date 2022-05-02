from flask import Flask, render_template, request, redirect, Response, url_for, send_from_directory, render_template
import speech_recognition as sr
import boto3, botocore
from werkzeug.utils import secure_filename
import io
import sys
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from keras.models import load_model
from werkzeug.utils import secure_filename
import time
import librosa, librosa.display
import numpy as np
import matplotlib.pyplot as plt
from flask_mysqldb import MySQL
import mutagen
from mutagen.wave import WAVE

app = Flask(__name__)
mysql = MySQL(app)
#model = pickle.load(open('model.pkl','rb'))

app.config['MYSQL_HOST'] = '192.168.0.100'
app.config['MYSQL_USER'] = 'idp'
app.config['MYSQL_PASSWORD'] = 'idp2g7'
app.config['MYSQL_DB'] = 'idp2g7'

@app.route("/", methods=["GET", "POST"])
def index():
    transcript = ""
    if request.method == "POST":
        print("FORM DATA RECEIVED")

        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            recognizer = sr.Recognizer()
            audioFile = sr.AudioFile(file)
            with audioFile as source:
                data = recognizer.record(source)
            transcript = recognizer.recognize_google(data, key=None)

    return render_template('index.html', transcript=transcript)

BUCKET_NAME = "idp2g7"
ACCESS_KEY_ID = ""
SECRET_ACCESS_KEY = ""

s3 = boto3.client('s3',
                    aws_access_key_id= ACCESS_KEY_ID,
                    aws_secret_access_key= SECRET_ACCESS_KEY,
                     )

@app.route('/upload',methods=['post'])
def upload():
    if request.method == 'POST':
        audio = request.files['file']
        if audio.filename == "":
            return redirect(request.url)

        if audio:
                filename = secure_filename(audio.filename)
                audio.save(filename)

                #s3 upload
                key = 'test/' + filename
                s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=filename,
                    Key = key)
                location = boto3.client('s3').get_bucket_location(Bucket='idp2g7')['LocationConstraint']
                obj_url = "https://s3-%s.amazonaws.com/%s/%s" % (location, 'idp2g7', key)

                #mysql upload
                cur = mysql.connection.cursor()
                audiofile = WAVE(filename)
                audio_info = audiofile.info
                duration = int(audio_info.length)
                data = [filename,duration,obj_url]
                query = 'INSERT INTO test (audio_filename,timestamp,duration,s3_object_url) VALUES(%s,NOW(),%s,%s)'
                cur.execute(query,data)
                mysql.connection.commit()
                cur.close() 
                msg = "Upload Done!"

    return render_template("index.html",msg =msg)




@app.route('/results', methods=['GET'])
def classify_and_show_results():
    filename = request.args['filename']
    # Compute audio signal features
    features = extract_features(filename)
    features = np.expand_dims(features, 0)
    # Load model and perform inference
    model = load_model('models/best_model.hdf5')
    predictions = model.predict(features)[0]
    # Process predictions and render results
    predictions_probability, prediction_classes = process_predictions(predictions,
                                                                    'config_files/classes.json')

    predictions_to_render = {prediction_classes[i]:"{}%".format(
                                round(predictions_probability[i]*100, 3)) for i in range(3)}
    # Delete uploaded file
    os.remove(filename)
    # Render results
    return render_template("results.html",
        filename=filename,
        predictions_to_render=predictions_to_render)


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
