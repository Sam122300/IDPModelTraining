import boto3,botocore 
from botocore.client import Config

ACCESS_KEY_ID = 'AKIAVGXBPBYNHBWUAA67'
ACCESS_SECRET_KEY = '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'
BUCKET_NAME = 'idp2g7'
FILE_NAME = 'bitmoji.png';


data = open(FILE_NAME, 'rb')

# S3 Connect
s3 = boto3.resource(
    's3',
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_SECRET_KEY,
    config=Config(signature_version='s3v4')
)

# Image download
s3.Bucket(BUCKET_NAME).download_file(FILE_NAME, './downloads/bitmoji.png'); # Change the second part
# This is where you want to download it too.


print ("Done")


