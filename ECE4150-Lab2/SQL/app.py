#!flask/bin/python
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, PHOTOGALLERY_S3_BUCKET_NAME, RDS_DB_HOSTNAME, RDS_DB_USERNAME, RDS_DB_PASSWORD, RDS_DB_NAME
from flask import Flask, jsonify, abort, request, make_response, url_for, session
from flask import render_template, redirect
import time
import exifread
import json
import uuid
import boto3  
import pymysql.cursors
from datetime import datetime
from pytz import timezone
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

def get_database_connection():
    conn = pymysql.connect(host=RDS_DB_HOSTNAME,
                             user=RDS_DB_USERNAME,
                             password=RDS_DB_PASSWORD,
                             db=RDS_DB_NAME,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
    return conn

def send_email(email, body):
    try:
        ses = boto3.client('ses', aws_access_key_id=AWS_ACCESS_KEY,
                                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                region_name=REGION)
        ses.send_email(
            Source=os.getenv('SES_EMAIL_SOURCE'),
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': 'Photo Gallery: Confirm Your Account'},
                'Body': {
                    'Text': {'Data': body}
                }
            }
        )

    except ClientError as e:
        print(e.response['Error']['Message'])

        return False
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

        return True


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
            conn=get_database_connection()
            
            cursor = conn.cursor ()
            
            statement = f'''SELECT * FROM photogallerydb.User WHERE email="{email}";'''
            cursor.execute(statement)
            items=cursor.fetchall()

            print(items)
            items=items[0]
            

            salt=items['salt']
            salt=salt[2:len(salt)-1]
            salt=bytes(salt,'utf-8')

            password_table=items['password']
            password_table=password_table[2:len(password_table)-1]
            password_table=bytes(password_table,'utf-8')

            table_active=items['active']

            password=bcrypt.hashpw(pass_bytes,salt)

            activated=items['active']


        #print(salt)

            if password==password_table and activated=='True':
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
        active=False

        serializer=URLSafeTimedSerializer(key)
        token= serializer.dumps

        conn=get_database_connection()
        cursor = conn.cursor ()
        statement = f'''SELECT * FROM photogallerydb.User WHERE email="{email}";'''
        cursor.execute(statement)
        results=cursor.fetchall()

        if password==password1:
            password=bytes(password, "utf-8")
            hashed = bcrypt.hashpw(password, salt)
            
            if results == ():
                print('ok')
                salt=str(salt)
                password=str(password)
                statement = f'''INSERT INTO photogallerydb.User (userID, email, name, password, active, salt) VALUES ("{username}", "{email}", "{name}","{hashed}", "{active}", "{salt}");'''
                cursor.execute(statement)
                conn.commit()
                conn.close()
                
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
                print("email already in use")
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

       email=email.split(' ')
       user=email[1]
       user_email=email[0]

       conn=get_database_connection()
       cursor = conn.cursor ()
       statement = f'''SELECT * FROM photogallerydb.User WHERE email="{user_email}";'''
       cursor.execute(statement)
       results=cursor.fetchall()


       print(results)
       print(type(results))

       results=results[0]
       active=True
       table_active=results['active']


       statement=f'''UPDATE photogallerydb.User SET active = "{active}" WHERE email = "{user_email}"'''
       cursor.execute(statement)

       conn.commit()
       conn.close()
       session['email']=user_email
       session['createdat']=time.time()
       return redirect('/')
        
       #myemailaddress@gatech.edu
   except:
       print("expired token")
       return redirect('/login')


@app.route("/deleteuser")

def deleteuser():

    user_email=session['email']
    conn=get_database_connection()
    cursor = conn.cursor ()

    statement= f'''DELETE FROM photogallerydb.Album WHERE user = "{user_email}";'''
    cursor.execute(statement)

    statement=f'''DELETE From photogallerydb.User Where email= "{user_email}";'''
    cursor.execute(statement)
    conn.commit()
    conn.close()
                        
    return redirect('/login')


@app.route('/album/<string:albumID>/photo/<string:photoID>/delete_photo', methods=['POST'])
#@login_required
def delete_photo(albumID, photoID):

    conn=get_database_connection()
    cursor = conn.cursor ()

    statement=f'''DELETE FROM photogallerydb.Photo WHERE photoID="{photoID}";'''
    cursor.execute(statement)

    conn.commit()
    conn.close()
	# Show the remaining photos of the album
    return redirect(f'''/album/{albumID}''')

@app.route('/album/<string:albumID>/photo/<string:photoID>/update_photo', methods=['POST','GET'])
def update_photo(albumID, photoID):

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')

    
    conn=get_database_connection()
    cursor = conn.cursor ()
	
    if request.method == 'POST':
        conn=get_database_connection()
        cursor = conn.cursor ()
        new_title = request.form['title']
        new_description = request.form['description']
        new_tags = request.form['tags']

        try:
            statement=f'''UPDATE photogallerydb.Photo SET title = "{new_title}", description="{new_description}", tags="{new_tags}" WHERE photoID = "{photoID}"'''
            cursor.execute(statement)

            conn.commit()
            conn.close()

            
           
        except ClientError as er:
            raise er

        return redirect(f'''/album/{albumID}''')
	
    else:
        statement = f'''SELECT * FROM photogallerydb.Album WHERE albumID="{albumID}";'''
        cursor.execute(statement)
        albumMeta = cursor.fetchall()

        statement = f'''SELECT * FROM photogallerydb.Photo WHERE photoID="{photoID}";'''
        cursor.execute(statement)
        results=cursor.fetchall()

        conn.close()

        return render_template('updatePhotoForm.html', albumID=albumID, photoID=photoID, albumName=albumMeta[0]['name'], photo_name=results[0]['title'])

    
@app.route('/album/<string:albumID>/delete_album', methods=['POST',"GET"])
def delete_album(albumID):

    
    conn=get_database_connection()
    cursor = conn.cursor ()

    statement=f'''DELETE FROM photogallerydb.Photo WHERE albumID="{albumID}";'''
    cursor.execute(statement)

    statement=f'''DELETE FROM photogallerydb.Album WHERE albumID="{albumID}";'''
    cursor.execute(statement)

    conn.commit()
    conn.close()
	
    return redirect('/')

"""
"""

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
    """ Home page route.

    get:
        description: Endpoint to return home page.
        responses: Returns all the albums.
    """
    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    
    conn=get_database_connection()
    cursor = conn.cursor ()
    cursor.execute("SELECT * FROM photogallerydb.Album;")
    results = cursor.fetchall()
    conn.close()
    
    items=[]
    for item in results:
        album={}
        album['albumID'] = item['albumID']
        album['name'] = item['name']
        album['description'] = item['description']
        album['thumbnailURL'] = item['thumbnailURL']

        createdAt = datetime.strptime(str(item['createdAt']), "%Y-%m-%d %H:%M:%S")
        createdAt_UTC = timezone("UTC").localize(createdAt)
        album['createdAt']=createdAt_UTC.astimezone(timezone("US/Eastern")).strftime("%B %d, %Y")

        items.append(album)

    return render_template('index.html', albums=items)



@app.route('/createAlbum', methods=['GET', 'POST'])
def add_album():
    """ Create new album route.

    get:
        description: Endpoint to return form to create a new album.
        responses: Returns all the fields needed to store new album.

    post:
        description: Endpoint to send new album.
        responses: Returns user to home page.
    """

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
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
            user=session['email']
            
            uploadedFileURL = s3uploading(str(albumID), filenameWithPath, "thumbnails");

            conn=get_database_connection()
            cursor = conn.cursor ()
            statement = f'''INSERT INTO photogallerydb.Album (albumID, name, description, thumbnailURL, user) VALUES ("{albumID}", "{name}", "{description}", "{uploadedFileURL}","{user}");'''
            
            result = cursor.execute(statement)
            conn.commit()
            conn.close()

        return redirect('/')
    else:
        return render_template('albumForm.html')



@app.route('/album/<string:albumID>', methods=['GET'])
def view_photos(albumID):
    """ Album page route.

    get:
        description: Endpoint to return an album.
        responses: Returns all the photos of a particular album.
    """

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')

    
    conn=get_database_connection()
    cursor = conn.cursor ()
    # Get title
    statement = f'''SELECT * FROM photogallerydb.Album WHERE albumID="{albumID}";'''
    cursor.execute(statement)
    albumMeta = cursor.fetchall()
    
    # Photos
    statement = f'''SELECT photoID, albumID, title, description, photoURL FROM photogallerydb.Photo WHERE albumID="{albumID}";'''
    cursor.execute(statement)
    results = cursor.fetchall()
    conn.close() 
    
    items=[]
    for item in results:
        photos={}
        photos['photoID'] = item['photoID']
        photos['albumID'] = item['albumID']
        photos['title'] = item['title']
        photos['description'] = item['description']
        photos['photoURL'] = item['photoURL']
        items.append(photos)

    return render_template('viewphotos.html', photos=items, albumID=albumID, albumName=albumMeta[0]['name'])



@app.route('/album/<string:albumID>/addPhoto', methods=['GET', 'POST'])
def add_photo(albumID):
    """ Create new photo under album route.

    get:
        description: Endpoint to return form to create a new photo.
        responses: Returns all the fields needed to store a new photo.

    post:
        description: Endpoint to send new photo.
        responses: Returns user to album page.
    """

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    
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
            user=session['email']
            
            uploadedFileURL = s3uploading(filename, filenameWithPath);
            
            ExifData=getExifData(filenameWithPath)

            conn=get_database_connection()
            cursor = conn.cursor ()
            ExifDataStr = json.dumps(ExifData)
            statement = f'''INSERT INTO photogallerydb.Photo (PhotoID, albumID, title, description, tags, photoURL, user, EXIF) VALUES ("{photoID}", "{albumID}", "{title}", "{description}", "{tags}", "{uploadedFileURL}", "{user}", %s);'''
            
            result = cursor.execute(statement, (ExifDataStr,))
            conn.commit()
            conn.close()

        return redirect(f'''/album/{albumID}''')
    else:
        conn=get_database_connection()
        cursor = conn.cursor ()
        # Get title
        statement = f'''SELECT * FROM photogallerydb.Album WHERE albumID="{albumID}";'''
        cursor.execute(statement)
        albumMeta = cursor.fetchall()
        conn.close()

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
    
    conn=get_database_connection()
    cursor = conn.cursor ()

    # Get title
    statement = f'''SELECT * FROM photogallerydb.Album WHERE albumID="{albumID}";'''
    cursor.execute(statement)
    albumMeta = cursor.fetchall()

    statement = f'''SELECT * FROM photogallerydb.Photo WHERE albumID="{albumID}" and photoID="{photoID}";'''
    cursor.execute(statement)
    results = cursor.fetchall()
    conn.close()

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

        createdAt_UTC = timezone("UTC").localize(createdAt)
        updatedAt_UTC = timezone("UTC").localize(updatedAt)

        photo['createdAt']=createdAt_UTC.astimezone(timezone("US/Eastern")).strftime("%B %d, %Y at %-I:%M:%S %p")
        photo['updatedAt']=updatedAt_UTC.astimezone(timezone("US/Eastern")).strftime("%B %d, %Y at %-I:%M:%S %p")
        
        tags=photo['tags'].split(',')
        exifdata=photo['EXIF']
        
        return render_template('photodetail.html', photo=photo, tags=tags, exifdata=exifdata, albumID=albumID, albumName=albumMeta[0]['name'])
    else:
        return render_template('photodetail.html', photo={}, tags=[], exifdata={}, albumID=albumID, albumName="")



@app.route('/album/search', methods=['GET'])
def search_album_page():
    """ search album page route.

    get:
        description: Endpoint to return all the matching albums.
        responses: Returns all the albums based on a particular query.
    """
    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    
    query = request.args.get('query', None)

    conn=get_database_connection()
    cursor = conn.cursor ()
    statement = f'''SELECT * FROM photogallerydb.Album WHERE name LIKE '%{query}%' UNION SELECT * FROM photogallerydb.Album WHERE description LIKE '%{query}%';'''
    cursor.execute(statement)

    results = cursor.fetchall()
    conn.close()

    items=[]
    for item in results:
        album={}
        album['albumID'] = item['albumID']
        album['name'] = item['name']
        album['description'] = item['description']
        album['thumbnailURL'] = item['thumbnailURL']
        items.append(album)

    return render_template('searchAlbum.html', albums=items, searchquery=query)



@app.route('/album/<string:albumID>/search', methods=['GET'])
def search_photo_page(albumID):
    """ search photo page route.

    get:
        description: Endpoint to return all the matching photos.
        responses: Returns all the photos from an album based on a particular query.
    """

    curr_time=time.time()
    if curr_time-session['createdat']>300:
        return redirect('/login')
    
    query = request.args.get('query', None)

    conn=get_database_connection()
    cursor = conn.cursor ()
    statement = f'''SELECT * FROM photogallerydb.Photo WHERE title LIKE '%{query}%' AND albumID="{albumID}" UNION SELECT * FROM photogallerydb.Photo WHERE description LIKE '%{query}%' AND albumID="{albumID}" UNION SELECT * FROM photogallerydb.Photo WHERE tags LIKE '%{query}%' AND albumID="{albumID}" UNION SELECT * FROM photogallerydb.Photo WHERE EXIF LIKE '%{query}%' AND albumID="{albumID}";'''
    cursor.execute(statement)

    results = cursor.fetchall()
    conn.close()

    items=[]
    for item in results:
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
