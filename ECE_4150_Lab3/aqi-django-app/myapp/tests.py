from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseBadRequest
from django.shortcuts import redirect
from django.conf import settings
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Count, Min, Sum, Avg
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
# from dateutil.tz import tzoffset

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

table = dynamodb.Table('AirQualityData')
table_output = dynamodb.Table('AirQualityDataOutput')

def download_csv(request):

    now=int(time.time())
    timestampold=now-86400

    response = table.scan(
        FilterExpression=Attr('timestamp').gt(timestampold)
    )


    items = response['Items']
    for x in range (len(items)):
        keys = list(items[x]['data'].keys())
        for key in keys:
            items[x][key]=items[x]['data'][key]
        items[x] = items[x].pop("data", None)
        

    
    df=pd.DataFrame(items)
    df.to_csv('~/downloads/output.csv',index=False)
    print(df)

    return redirect('/rawdata')
    
