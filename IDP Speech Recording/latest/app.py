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
import time
import librosa, librosa.display
import matplotlib.pyplot as plt
from flask_mysqldb import MySQL
import mutagen
from mutagen.wave import WAVE
import json
import os
import math
import librosa
import boto3
import soundfile as sf
from pydub import AudioSegment
from app import *
from flask_mysqldb import MySQL
from io import BytesIO
import io
from werkzeug.utils import secure_filename
from six.moves.urllib.request import urlopen
#import mysql.connector
from deploy import *
from extract_feature import *

JSON_PATH = "data_nolabel.json" #change ur json file name here

app = Flask(__name__)
mysql = MySQL(app)
#model = pickle.load(open('model.pkl','rb'))

app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = '9rBnbH2yWN'
app.config['MYSQL_PASSWORD'] = 'obqUHk85vy'
app.config['MYSQL_DB'] = '9rBnbH2yWN'

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
location = "ap-southeast-1"
s3 = boto3.client('s3',aws_access_key_id= ACCESS_KEY_ID,aws_secret_access_key= SECRET_ACCESS_KEY)

# record = []

def feature_extraction(AUDIO,filename):
    print(type(AUDIO))
    # AUDIO=segmentfile(AUDIO)
    save_mfcc(JSON_PATH, AUDIO,filename)

def model_deployment():
    DATA_PATH = "data_nolabel.json"
    vmodel = keras.models.load_model(r"C:\Users\OOi QI HAO\Desktop\idp2\IDP latest\rnn_model")#options=load_options)
    myprediction = predict(vmodel, DATA_PATH) #[1,3,4,5,13,12,.....]
    print(myprediction)
    #x = len(myprediction)/5
    #myprediction = np.array_split(myprediction, x)
    label = np.bincount(myprediction).argmax()
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT filename FROM test WHERE timestamp = (SELECT MAX(timestamp) FROM test)") 
    f_name = cursor.fetchone()[0]
    print(f_name)
    save_prediction(f_name,int(label))

@app.route('/upload',methods=['post'])
def upload():
    if request.method == 'POST':
        audio = request.files['files']
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
            obj_url = "https://%s.s3.%s.amazonaws.com/%s" % ( 'idp2g7',location, key)

            #mysql upload
            cur = mysql.connection.cursor()
            audiofile = WAVE(filename)
            audio_info = audiofile.info
            duration = int(audio_info.length)
            data = [filename,duration,obj_url]
            query = 'INSERT INTO test (filename,timestamp,duration,s3_obj_url) VALUES(%s,NOW(),%s,%s)'
            cur.execute(query,data)
            mysql.connection.commit()
            cur.close() 
            msg = "Upload Done!"

            feature_extraction(audio,filename)
            model_deployment()
    
            
    
    
    return render_template("index.html",msg =msg)

plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.autolayout"] = True
@app.route('/print-plot')
def plot_png():
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT filename FROM test WHERE timestamp = (SELECT MAX(timestamp) FROM test)") 
    f_name = cursor.fetchone()[0]
    print(f_name)
    dir = r'C:\Users\OOi QI HAO\Desktop\idp2\IDP latest'
    filepath = os.path.join(dir,f_name)
    print(filepath)
    signal,sample_rate = librosa.load(filepath)
    librosa.display.waveshow(signal,sr=22050)
    

    #fig = Figure()
    #axis = fig.add_subplot(1, 1, 1)
    #legend = 'Monthly Data'
    #labels = ["Fans", "Valves", "Pump", "Slider"]
    #values = [5, 1, 9, 3]
    # xs = labels
    # ys = values
    # axis.plot(xs, ys)
    # output = io.BytesIO()
    # FigureCanvas(fig).print_png(output)
    # return Response(output.getvalue(), mimetype='image/png')

@app.route('/predict')
def showprediction():
     
     cursor = mysql.connection.cursor()
     cursor.execute("SELECT normal FROM test WHERE timestamp = (SELECT MAX(timestamp) FROM test)")
     result = cursor.fetchone()[0]
     print(result)
     if result == '0': yy = 'FAN ANOMALY TYPE 1'
     elif result =='1': yy = 'FAN ANOMALY TYPE 2'
     elif result =='2': yy = 'FAN ANOMALY TYPE 3'
     elif result =='3': yy = 'PUMP ANOMALY TYPE 1'
     elif result =='4': yy = 'PUMP ANOMALY TYPE 2'
     elif result =='5': yy = 'PUMP ANOMALY TYPE 3'
     elif result =='6': yy = 'SLIDE RAIL ANOMALY TYPE 1'
     elif result =='7': yy = 'SLIDE RAIL ANOMALY TYPE 2'
     elif result =='8': yy = 'VALVE ANOMALY TYPE 1'
     elif result =='9': yy = 'VALVE ANOMALY TYPE 2'
     elif result =='10': yy = 'NORMAL FAN'
     elif result =='11': yy = 'NORMAL PUMP'
     elif result =='12': yy = 'NORMAL SLIDE RAIL'
     elif result =='13': yy = 'NORMAL VALVE'
     return render_template('plot_png.html', condition=yy)
    


#def extractdata():
#    cur = mysql.connection.cursor()
#    query = "SELECT normal, fault, filename FROM test WHERE normal IS NOT NULL"
#    cur.execute(query)
#    cur.fetchall()
#    mysql.connection.commit()
#    cur.close()

#app = dash.Dash(__name__)

#app.layout = html.Div(
#    children=[
#        html.H1(children="Anomaly Stats",),
#        html.P(
#            children="Types of Anomalies and their Characteristics",
#        ),
#        dcc.Graph(
#            figure={ 
#                "data": [
#                    {
#                        "x": data["timestamp"],
#                        "y": data["normal"],
#                        "type": "lines",
 #                   },
#               ],
#               "layout": {"title": "Types of Anomalies and their Characteristics"},
#            },
#        ),
#        dcc.Graph(
#            figure={
#                "data": [
#                    {
#                        "x": data["Date"],
#                        "y": data["Total Volume"],
#                        "type": "lines",
#                    },
#                ],
#                "layout": {"title": "Types of Anomalies and their Characteristics"},
#            },
#        ),
#    ]
#)

# if __name__ == "__main__":
app.run(debug=True, threaded=True)
