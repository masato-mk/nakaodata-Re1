import boto3
import pandas as pd
from io import StringIO
import os

# @st.cache(allow_output_mutation=True)
def s3_data():

    s3 = boto3.resource('s3')

    ACCESS_KEY = os.environ['ACCESS_KEY']
    SECRET_KEY = os.environ['SECRET_KEY']


    client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    paginator = client.get_paginator('list_objects')
    pageresponse = paginator.paginate(Bucket=os.environ['Bucket'])

    readers = pd.DataFrame()

    for pageobject in pageresponse:
        for file in pageobject["Contents"]:
            obj = client.get_object(Bucket=os.environ['Bucket'], Key=file["Key"])
            content = obj['Body'].read().decode('shift-jis')
            reader = pd.read_csv(StringIO(content))
            reader.columns = reader.loc[0]
            reader.index = reader.loc[:,'時刻']
            reader = reader.drop(index='時刻')
            reader = reader.drop(columns = ['時刻'])
            readers = readers.append(reader)
    
    return readers
