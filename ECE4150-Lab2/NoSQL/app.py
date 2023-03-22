#!flask/bin/python
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, PHOTOGALLERY_S3_BUCKET_NAME, DYNAMODB_TABLE,USER_DYNAMODB_TABLE
from flask import Flask, jsonify, abort, request, make_response, url_for, session
from flask import render_template, redirect
import time
import exifread
import json
import uuid
import boto3  
from boto3.dynamodb.conditions import Key, Attr
import pymysql.cursors
from datetime import datetime
import pytz
import bcrypt
from itsdangerous import URLSafeTimedSerializer
from botocore.exceptions import ClientError
import time

"""
    INSERT NEW LIBRARIES HERE (IF NEEDED)
"""





"""
"""

app = Flask(__name__, static_url_path="")

app.secret_key='Less Go'

ses= boto3.client('ses',region_name=AWS_REGION,
                  aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

user_table=dynamodb.Table(USER_DYNAMODB_TABLE)
table = dynamodb.Table(DYNAMODB_TABLE)

UPLOAD_FOLDER = os.path.join(app.root_path,'static','media')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getExifData(path_name):
    f = open(path_name, 'rb')
    tags = exifread.process_file(f)
    ExifData={}
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            key="%s"%(tag)
            val="%s"%(tags[tag])
            ExifData[key]=val
    return ExifData

def s3uploading(filename, filenameWithPath, uploadType="photos"):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
                       
    bucket = PHOTOGALLERY_S3_BUCKET_NAME
    path_filename = uploadType + "/" + filename

    s3.upload_file(filenameWithPath, bucket, path_filename)  
    s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=path_filename)
    return f'''http://{PHOTOGALLERY_S3_BUCKET_NAME}.s3.amazonaws.com/{path_filename}'''


"""
    INSERT YOUR NEW FUNCTION HERE (IF NEEDED)
"""

"""
"""
"""
    INSERT YOUR NEW ROUTE HERE (IF NEEDED)
"""
@app.route('/login', methods=['GET','POST'])

def login():

    if request.method=='POST':
        email=request.form['username']
        password=str(request.form['password'])

        pass_bytes=bytes(password,'utf-8')

        try:
            response = user_table.scan(FilterExpression=Attr('Email').eq(email))
            items=response['Items']
            items=items[0]

            salt=items['salt']
            salt=salt[2:len(salt)-1]
            salt=bytes(salt,'utf-8')

            password_table=items['password']
            password_table=password_table[2:len(password_table)-1]
            password_table=bytes(password_table,'utf-8')

            password=bcrypt.hashpw(pass_bytes,salt)

            activated=items['active']

        #print(salt)

            if password_table==password and activated==True:
                session['email']=email
                session['createdat']=time.time()
            
                return redirect('/')
            else:
                print("Wrong password")
        except:
            print("Email does not exist")
        
    return render_template('login.html')


@app.route('/signup', methods=['GET','POST'])

def sinup():

    if request.method=='POST':
        username=uuid.uuid4()
        password=request.form['password']
        name=request.form['name']
        email=request.form['email']
        password1=request.form['password1']
        createdat=datetime.now().astimezone()
        salt=bcrypt.gensalt()
        email_send='zts929@gmail.com'
        email_receive=email
        key='Ooga Booga'

        serializer=URLSafeTimedSerializer(key)
        token= serializer.dumps

        response = user_table.scan(FilterExpression=Attr('Email').eq(email))

        if password==password1:
            password=bytes(password, "utf-8")
            hashed = bcrypt.hashpw(password, salt)

            if response['Items']!=[]:
                response = user_table.scan(FilterExpression=Attr('Email').eq(email))
                print("Username or email already exists")
            else:
                user_table.put_item(
                Item={
                    "Username": str(username),
                    "Email": email,
                    "password": str(hashed),
                    "active": False,
                    "albums": {},
                    "name": name,
                    "createdAt": str(createdat),
                    "salt": str(salt)
                    }
                    )
                ID='{} {}'.format(email,username)
                serializer=URLSafeTimedSerializer('Ooga Booga')
                token= serializer.dumps(ID,salt='secret')

                URL='ec2-3-87-202-190.compute-1.amazonaws.com:5000/confirm/{}'.format(token)

                try:
                    response= ses.send_email(
                        Destination={
                            'ToAddresses': [email_receive],
                                    },
                        Message={
                            'Body': {
                                'Text':{
                                    'Data':URL,
                                    },
                                },
                            'Subject':{
                                'Data': 'User Verification Email'
                                },
                            },
                        Source=email_send)
                except ClientError as e:
                    print(e.response['Error']['Message'])
        else:
            print("Passwords Do not Match")
                

            
    return render_template('signup.html')

@app.route('/confirm/<string:ID>', methods=['GET'])

def confirm(ID):



   serializer=URLSafeTimedSerializer('Ooga Booga')
   try:
       token=ID
       print(token)
       email = serializer.loads(
           token,
           salt='secret',
           max_age=600
        )

       print(email)
       email=email.split(' ')
       user=email[1]
       user_email=email[0]

       print(user)
       print(user_email)

       response=user_table.get_item(Key={'Username':user,'Email':user_email})

       item=response["Item"]
       item['active']=True

       user_table.put_item(Item=item)
       session['email']=email
       session['createdat']=time.time()
       return redirect('/')
        
       #myemailaddress@gatech.edu
   except:
       print("expired Token")
       return redirect('/login')


        
@app.route("/deleteuser")

def deleteuser():
    
    response = table.scan(FilterExpression=Attr('user').eq(session['email']))
    results = response['Items']


    for item in results:

        table.delete_item(
            Key={
                "albumID":item['albumID'],
                "photoID":item['photoID']
                }
            )

    response=user_table.scan(FilterExpression=Attr('Email').eq(session['email']))
    results=response['Items']
    results=results[0]

    user_table.delete_item(
        Key={
            "Email":session['email'],
            "Username":results["Username"]
            }
        )
                        
    return redirect('/login')


@app.route('/album/<string:albumID>/photo/<string:photoID>/delete_photo', methods=['POST'])
#@login_required
def delete_photo(albumID, photoID):
    try:
        table.delete_item(
            Key={
                "albumID":str(albumID),
                "photoID":str(photoID)
                }
            )
    except ClientError as er:
        raise er
	
	# Show the remaining photos of the album
    return redirect(f'''/album/{albumID}''')

@app.route('/album/<string:albumID>/photo/<string:photoID>/update_photo', methods=['POST','GET'])
def update_photo(albumID, photoID):

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    
    response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
    results = response['Items']
	
    if request.method == 'POST':
        new_title = request.form['title']
        new_description = request.form['description']
        new_tags = request.form['tags']

        updatedAtlocalTime = datetime.now().astimezone()
        updatedAtUTCTime = updatedAtlocalTime.astimezone(pytz.utc)
        try:
            table.update_item(
                Key={
                    "albumID" : str(albumID),
                    "photoID": str(photoID)
                },
                UpdateExpression="set title=:t, description=:d, tags=:g, updatedAt=:u",
                ExpressionAttributeValues={
                    ':t': new_title,
                    ':d': new_description,
                    ':g': new_tags,
                    ':u': updatedAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
                },
                ReturnValues="UPDATED_NEW"
            )
	
        except ClientError as er:
            raise er

        return redirect(f'''/album/{albumID}''')
	
    else:
        albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
        albumMeta = albumResponse['Items']

        return render_template('updatePhotoForm.html', albumID=albumID, photoID=photoID, albumName=albumMeta[0]['name'], photo_name=results[0]['title'])

    
@app.route('/album/<string:albumID>/delete_album', methods=['POST',"GET"])
def delete_album(albumID):
    album_response = table.scan(FilterExpression=Attr('albumID').eq(albumID))
    items = album_response['Items']
		
    for item in items:
        try:
            table.delete_item(
                Key={
		    "albumID" : str(albumID),
		    "photoID": str(item['photoID'])
		    }
		)
        except ClientError as er:
            raise er
	
    return redirect('/')

@app.errorhandler(400)
def bad_request(error):
    """ 400 page route.

    get:
        description: Endpoint to return a bad request 400 page.
        responses: Returns 400 object.
    """
    return make_response(jsonify({'error': 'Bad request'}), 400)



@app.errorhandler(404)
def not_found(error):
    """ 404 page route.

    get:
        description: Endpoint to return a not found 404 page.
        responses: Returns 404 object.
    """
    return make_response(jsonify({'error': 'Not found'}), 404)


'''
Added an if statement that takes the current time and subtracts if from
the time of login, it will logout if the time is greater than
5 minutes. This happened on every viewable page

Also edited the add photo and add album so that it keeps track of the user

'''



@app.route('/', methods=['GET'])
def home_page():

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    """ Home page route.

    get:
        description: Endpoint to return home page.
        responses: Returns all the albums.
    """
    print(session)
    response = table.scan(FilterExpression=Attr('photoID').eq("thumbnail"))
    results = response['Items']

    if len(results) > 0:
        for index, value in enumerate(results):
            createdAt = datetime.strptime(str(results[index]['createdAt']), "%Y-%m-%d %H:%M:%S")
            createdAt_UTC = pytz.timezone("UTC").localize(createdAt)
            results[index]['createdAt'] = createdAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y")

    return render_template('index.html', albums=results)



@app.route('/createAlbum', methods=['GET', 'POST'])
def add_album():

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    """ Create new album route.

    get:
        description: Endpoint to return form to create a new album.
        responses: Returns all the fields needed to store new album.

    post:
        description: Endpoint to send new album.
        responses: Returns user to home page.
    """
    if request.method == 'POST':
        uploadedFileURL=''
        file = request.files['imagefile']
        name = request.form['name']
        description = request.form['description']

        if file and allowed_file(file.filename):
            albumID = uuid.uuid4()
            
            filename = file.filename
            filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filenameWithPath)
            
            uploadedFileURL = s3uploading(str(albumID), filenameWithPath, "thumbnails");

            createdAtlocalTime = datetime.now().astimezone()
            createdAtUTCTime = createdAtlocalTime.astimezone(pytz.utc)

            table.put_item(
                Item={
                    "albumID": str(albumID),
                    "photoID": "thumbnail",
                    "name": name,
                    "description": description,
                    "thumbnailURL": uploadedFileURL,
                    "createdAt": createdAtUTCTime.strftime("%Y-%m-%d %H:%M:%S"),
                    "user" : session['email']
                }
            )

        return redirect('/')
    else:
        return render_template('albumForm.html')



@app.route('/album/<string:albumID>', methods=['GET'])
def view_photos(albumID):

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    """ Album page route.

    get:
        description: Endpoint to return an album.
        responses: Returns all the photos of a particular album.
    """
    albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
    albumMeta = albumResponse['Items']

    response = table.scan(FilterExpression=Attr('albumID').eq(albumID) & Attr('photoID').ne('thumbnail'))
    items = response['Items']

    return render_template('viewphotos.html', photos=items, albumID=albumID, albumName=albumMeta[0]['name'])



@app.route('/album/<string:albumID>/addPhoto', methods=['GET', 'POST'])
def add_photo(albumID):

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    """ Create new photo under album route.

    get:
        description: Endpoint to return form to create a new photo.
        responses: Returns all the fields needed to store a new photo.

    post:
        description: Endpoint to send new photo.
        responses: Returns user to album page.
    """
    if request.method == 'POST':    
        uploadedFileURL=''
        file = request.files['imagefile']
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']

        if file and allowed_file(file.filename):
            photoID = uuid.uuid4()
            filename = file.filename
            filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filenameWithPath)            
            
            uploadedFileURL = s3uploading(filename, filenameWithPath);
            
            ExifData=getExifData(filenameWithPath)
            ExifDataStr = json.dumps(ExifData)

            createdAtlocalTime = datetime.now().astimezone()
            updatedAtlocalTime = datetime.now().astimezone()

            createdAtUTCTime = createdAtlocalTime.astimezone(pytz.utc)
            updatedAtUTCTime = updatedAtlocalTime.astimezone(pytz.utc)

            table.put_item(
                Item={
                    "albumID": str(albumID),
                    "photoID": str(photoID),
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "photoURL": uploadedFileURL,
                    "EXIF": ExifDataStr,
                    "createdAt": createdAtUTCTime.strftime("%Y-%m-%d %H:%M:%S"),
                    "updatedAt": updatedAtUTCTime.strftime("%Y-%m-%d %H:%M:%S"),
                    "user": session['email']
                }
            )

        return redirect(f'''/album/{albumID}''')

    else:

        albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
        albumMeta = albumResponse['Items']

        return render_template('photoForm.html', albumID=albumID, albumName=albumMeta[0]['name'])



@app.route('/album/<string:albumID>/photo/<string:photoID>', methods=['GET'])
def view_photo(albumID, photoID):
    """ photo page route.

    get:
        description: Endpoint to return a photo.
        responses: Returns a photo from a particular album.
    """

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    
    albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
    albumMeta = albumResponse['Items']

    response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
    results = response['Items']
    #print(results)
    #print(response)

    if len(results) > 0:
        photo={}
        photo['photoID'] = results[0]['photoID']
        photo['title'] = results[0]['title']
        photo['description'] = results[0]['description']
        photo['tags'] = results[0]['tags']
        photo['photoURL'] = results[0]['photoURL']
        photo['EXIF']=json.loads(results[0]['EXIF'])

        createdAt = datetime.strptime(str(results[0]['createdAt']), "%Y-%m-%d %H:%M:%S")
        updatedAt = datetime.strptime(str(results[0]['updatedAt']), "%Y-%m-%d %H:%M:%S")

        createdAt_UTC = pytz.timezone("UTC").localize(createdAt)
        updatedAt_UTC = pytz.timezone("UTC").localize(updatedAt)

        photo['createdAt']=createdAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y at %-I:%M:%S %p")
        photo['updatedAt']=updatedAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y at %-I:%M:%S %p")
        
        tags=photo['tags'].split(',')
        exifdata=photo['EXIF']
        
        return render_template('photodetail.html', photo=photo, tags=tags, exifdata=exifdata, albumID=albumID, albumName=albumMeta[0]['name'])
    else:
        return render_template('photodetail.html', photo={}, tags=[], exifdata={}, albumID=albumID, albumName="")



@app.route('/album/search', methods=['GET'])
def search_album_page():
    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    """ search album page route.

    get:
        description: Endpoint to return all the matching albums.
        responses: Returns all the albums based on a particular query.
    """ 
    query = request.args.get('query', None)    

    response = table.scan(FilterExpression=Attr('name').contains(query) | Attr('description').contains(query))
    results = response['Items']

    items=[]
    for item in results:
        if item['photoID'] == 'thumbnail':
            album={}
            album['albumID'] = item['albumID']
            album['name'] = item['name']
            album['description'] = item['description']
            album['thumbnailURL'] = item['thumbnailURL']
            items.append(album)

    return render_template('searchAlbum.html', albums=items, searchquery=query)



@app.route('/album/<string:albumID>/search', methods=['GET'])
def search_photo_page(albumID):

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    """ search photo page route.

    get:
        description: Endpoint to return all the matching photos.
        responses: Returns all the photos from an album based on a particular query.
    """ 
    query = request.args.get('query', None)    

    response = table.scan(FilterExpression=Attr('title').contains(query) | Attr('description').contains(query) | Attr('tags').contains(query) | Attr('EXIF').contains(query))
    results = response['Items']

    items=[]
    for item in results:
        if item['photoID'] != 'thumbnail' and item['albumID'] == albumID:
            photo={}
            photo['photoID'] = item['photoID']
            photo['albumID'] = item['albumID']
            photo['title'] = item['title']
            photo['description'] = item['description']
            photo['photoURL'] = item['photoURL']
            items.append(photo)

    return render_template('searchPhoto.html', photos=items, searchquery=query, albumID=albumID)



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
