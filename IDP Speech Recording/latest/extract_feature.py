import json
import os
import math
import librosa
import boto3
import soundfile as sf
from pydub import AudioSegment
from app import *
from io import BytesIO
import io
from werkzeug.utils import secure_filename
import mysql.connector

BUCKET_NAME = "idp2g7"
ACCESS_KEY_ID = ""
SECRET_ACCESS_KEY = ""
s3 = boto3.resource('s3',aws_access_key_id= ACCESS_KEY_ID,aws_secret_access_key= SECRET_ACCESS_KEY)
bucket = s3.Bucket(BUCKET_NAME)
location = "ap-southeast-1"

JSON_PATH = "data_nolabel.json" #change ur json file name here
SAMPLE_RATE = 22050
TRACK_DURATION = 5  # measured in seconds
SAMPLES_PER_TRACK = SAMPLE_RATE * TRACK_DURATION #=220500

def segmentfile(audio):
    
    Audio = AudioSegment.from_wav(audio)
    if Audio.duration_seconds>=5.0:
        first_5_seconds = Audio[:5000]
        # first_5_seconds.export("C:/Users/OOi QI HAO/Desktop/Audio/audio.wav", format="wav")
        return first_5_seconds
    else:
        return audio


def save_mfcc(json_path, AUDIO,filename, num_mfcc=13, n_fft=2048, hop_length=512,num_segments=5):
    """Extracts MFCCs from audio and saves them into a json file
        :param json_path (str): Path to json file used to save MFCCs
        :param num_mfcc (int): Number of coefficients to extract
        :param n_fft (int): Interval we consider to apply FFT. Measured in # of samples
        :param hop_length (int): Sliding window for FFT. Measured in # of samples
        :param: num_segments (int): Number of segments we want to divide sample tracks into
        :return:
        """

    # dictionary to store mapping, labels, and MFCCs
    data = {
        "mfcc": []
    }

    samples_per_segment = int(SAMPLES_PER_TRACK / num_segments) #=44100
    num_mfcc_vectors_per_segment = math.ceil(samples_per_segment/ hop_length) #=87
    
    for d in range(num_segments):

        # calculate start and finish sample for current segment
        start = samples_per_segment * d
        finish = start + samples_per_segment

        # extract mfcc
        dir = r"C:\Users\OOi QI HAO\Desktop\idp2\IDP latest"
        filepath = os.path.join(dir,filename)
        signal , sample_rate = librosa.load(filepath, sr = SAMPLE_RATE)
        mfcc = librosa.feature.mfcc(signal[start:finish],
                                    sr=sample_rate,
                                    n_mfcc=num_mfcc,
                                    n_fft=n_fft,
                                    hop_length=hop_length
                                    )
        mfcc = mfcc.T

        # store only mfcc feature with expected number of vectors
        if len(mfcc) == num_mfcc_vectors_per_segment:
            data["mfcc"].append(mfcc.tolist())
            # data["labels"].append(i - 1)
            # print("{}, segment:{}".format(file_path, d + 1))


    # save MFCCs to json file
    with open(json_path, "w") as fp:
        json.dump(data, fp, indent=4)
