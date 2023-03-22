import sys, os
# import pwd
# import grp
# import json, simplejson
# from datetime import datetime, date, timedelta
# from dateutil import relativedelta
import time
from django.shortcuts import render
# import csv
# import requests
# import operator
# from lxml.html import fromstring
# import glob
# import zipfile
# import random
# import re
# import sha
# from .models import *
import boto3
from django.utils import timezone
# import json
from boto3.dynamodb.conditions import Key, Attr
import pandas as pd
# import datetime
from dateutil.tz import tzoffset
import matplotlib.pyplot as plt
import matplotlib.animation as animation

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

table = dynamodb.Table('AirQualityData')
table_output = dynamodb.Table('AirQualityDataOutput')


track=input("Which Gas do you want to Track (so2,co,pm10,pm2.5)?: ")
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

x_102=[]
y_102=[]
now=int(time.time())
origin=now
timestampold=now-120


def animate(i):

    global x_102,y_102,origin
    now=int(time.time())
    timestampold=now-30


    response = table.query(
        KeyConditionExpression=Key('timestamp').gt(timestampold) & Key('stationID').eq('ST105')
        )
    
    items=response['Items'][-1]
    y_102.append(items['data'][track])
    x_102.append(items['timestamp']-origin)



    xs1 = x_102[-10:-1]
    ys1 = y_102[-10:-1]

    ax.clear()
    ax.plot(xs1,ys1)

    
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title("{} emissions over time".format(track.upper()))
    plt.ylabel(track.upper())
    plt.xlabel('time')



response = table.query(
KeyConditionExpression=Key('timestamp').gt(timestampold) & Key('stationID').eq('ST105')
)

items = response['Items']

for item in items:
    y_102.append(item['data'][track])
    x_102.append(item['timestamp']-origin)




ani = animation.FuncAnimation(fig, animate, fargs=(), interval=1000)
plt.show()
    

    

