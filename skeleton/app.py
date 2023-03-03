######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for, session
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'oliver29'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():

	try:
		email=request.form.get('email')
		password=request.form.get('password')
		fname=request.form.get('fname')
		lname=request.form.get('lname')
		hometown = request.form.get('hometown')
		birthday = request.form.get('DoB')
		gender = request.form.get('gender')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)

	if test:
		print(cursor.execute("INSERT INTO Users (email, password, fname, lname, hometown, birthday, gender) VALUES ('{0}', '{1}', '{2}','{3}', '{4}', '{5}', '{6}')".format(email, password,fname,lname, hometown, birthday, gender)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register', supress = False))

@app.route("/contributors", methods=['GET'])
def contributors():
	top_contributors = compute_contribution_scores()
	return render_template('contributors.html', top_contributors=top_contributors)
def compute_contribution_scores():
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, COUNT(*) as num_photos FROM Pictures GROUP BY user_id")
    photo_counts = dict(cursor.fetchall())
    cursor.execute("SELECT user_id, COUNT(*) as num_comments FROM Comments GROUP BY user_id")
    comment_counts = dict(cursor.fetchall())
    
    contribution_scores = {}
    for user_id in photo_counts.keys():
        score = photo_counts[user_id] + comment_counts.get(user_id, 0)
        contribution_scores[user_id] = score
	
    sorted_scores = sorted(contribution_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    top_users = [x[0] for x in sorted_scores]
    top_user_emails = [getEmailFromUserId(uid) for uid in top_users]
    
    return top_user_emails


def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]
def getAllPhotos():
	cursor = conn.cursor()
	photos = []
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures".format())
	for row in cursor.fetchall():
		photo = row[0]
		id = row[1]
		caption = row[2]
		image_data = base64.b64encode(photo).decode('utf-8')
		cursor.execute("SELECT tag_text FROM Tags WHERE picture_id = %s", (id,))
		tags = [tag[0] for tag in cursor.fetchall()]
		cursor.execute("SELECT comment_text FROM Comments WHERE picture_id = %s", (id))
		comments = [comment[0] for comment in cursor.fetchall()]
		cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = %s", id)
		total_likes = cursor.fetchone()[0]
		cursor.execute("SELECT user_id FROM Likes WHERE picture_id = %s", id)
		users_liked = [user[0] for user in cursor.fetchall()]
		user_emails = [getEmailFromUserId(user_id) for user_id in users_liked]
		photos.append({'id': id, 'image_data': image_data, 'caption': caption, 'tags': tags, 'comments': comments, 'total_likes': total_likes, 'users_liked': user_emails})
	return photos
def getUsersAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT album_name FROM Albums WHERE user_id = '{0}'".format(uid))
    R = cursor.fetchall()
    row = [item[0] for item in R]
    return row

######IF USER DOESNT EXIST RETURN NONE REMEMBER
def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getFriends():
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT friend_id FROM Friends WHERE user_id = '{0}')".format(getUserIdFromEmail(flask_login.current_user.id)))
	return cursor.fetchall()

def getAlbumId(album_name, uid):
    cursor = conn.cursor()
    cursor.execute("SELECT album_id FROM Albums WHERE album_name = '{0}'".format(album_name))
    result = cursor.fetchone()
    if result is not None:
        return result[0]
    else:
        return None

def getAlbumPhotos(album_name, uid):
    photos = []
    cursor = conn.cursor()
    album_id = getAlbumId(album_name, uid)
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = %s", (album_id,))
    for row in cursor.fetchall():
        id = row[1]
        photo = row[0]
        caption = row[2]
        image_data = base64.b64encode(photo).decode('utf-8')
        cursor.execute("SELECT tag_text FROM Tags WHERE picture_id = %s", (id,))
        tags = [tag[0] for tag in cursor.fetchall()]
        photos.append({'id': id, 'image_data': image_data, 'caption': caption, 'tags': tags})
    return photos


def getPhotoIdFromName(name, uid, aid):
	cursor = conn.cursor()
	cursor.execute("SELECT picture_id FROM Pictures WHERE album_id = '{0}' AND caption = '{1}'".format(aid, name))
	return cursor.fetchone()[0]
def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", friends = getFriends(), profile = True)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/comments',methods = ['GET', 'POST'])
def search_comments():
    if request.method == 'POST':
        query = request.form['search']
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, COUNT(*) as count FROM Comments WHERE comment_text = %s GROUP BY user_id ORDER BY count DESC", (query,))
        matching_users = cursor.fetchall()
        matching_users = [(getEmailFromUserId(user[0]), user[1]) for user in matching_users]
        matching_users = sorted(matching_users, key=lambda x: x[1], reverse=True)
        matching_users = [user[0] for user in matching_users]
        if not matching_users:
            res = True
        else:
            res = False
        return render_template('searchcomments.html', users=matching_users, result=res)
    else:
        return render_template('searchcomments.html')




@app.route('/photos/<album_name>')
@flask_login.login_required
def view_album(album_name):
	photos = getAlbumPhotos(album_name, flask_login.current_user.id)
	return render_template('photos.html', album_name = album_name, photos = photos)

@flask_login.login_required
def isAlbumUnique(album_name):
    cursor = conn.cursor()
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    result = cursor.execute("SELECT album_name FROM Albums WHERE user_id = %s AND album_name = %s", (user_id, album_name))
    if cursor.fetchone() is None:
        return True
    else:
        print("Album already exists for this user")
        return False

@app.route('/makealbum', methods=['GET','POST'])
@flask_login.login_required
def make_album():
	if request.method == 'POST':
		render_template
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_name = request.form.get('album_name')
		if not isAlbumUnique(album_name):
			return render_template('makealbum.html', albums = getUsersAlbums(uid), message = "Album name already taken")
		else:
			session['album_name'] = album_name
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Albums (album_name, user_id) VALUES (%s, %s)''', (album_name, uid))
			conn.commit()
			return render_template('upload.html', album_name = album_name)
		# return render_template('hello.html', name=flask_login.current_user.id, message='album created', photos=getUsersPhotos(uid), base64=base64)
		#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('makealbum.html', albums = getUsersAlbums(uid))
	
@app.route('/browsephotos', methods=['GET'])
def browse_photos():
    photos = getAllPhotos()
    return render_template('browsephotos.html', photos=photos, base64=base64)

def getPhotosWithTag(tag):
	photos = []
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id IN (SELECT picture_id FROM Tags WHERE tag_text = '{0}')".format(tag))
	for row in cursor.fetchall():
		id = row[1]
		photo = row[0]
		caption = row[2]
		image_data = base64.b64encode(photo).decode('utf-8')
		cursor.execute("SELECT tag_text FROM Tags WHERE picture_id = %s", (id,))
		tags = [tag[0] for tag in cursor.fetchall()]
		photos.append({'id': id, 'image_data': image_data, 'caption': caption, 'tags': tags})
	return photos
def getPopularTags():
	cursor = conn.cursor()
	cursor.execute("SELECT tag_text, COUNT(tag_text) FROM Tags GROUP BY tag_text ORDER BY COUNT(tag_text) DESC LIMIT 5")
	return [tag[0] for tag in cursor.fetchall()]
@app.route('/tagSearch', methods=['GET', 'POST'])
def tag_search():
	poptags = getPopularTags()
	if request.method == 'POST':
		tag = request.form.get('tag')
		tags = tag.split()
		photos = []
		for temp in tags:
			photos += getPhotosWithTag(temp)
		return render_template('tagsearch.html', photos=photos, populartags= poptags, base64=base64)
	return render_template('tagsearch.html', populartags = poptags,base64=base64)

@app.route('/popular_tags/<tag>',methods=['GET'])
def popular_tags(tag):
	photos = getPhotosWithTag(tag)
	poptags = getPopularTags()
	return render_template('tagsearch.html', photos = photos, populartags = poptags, base64=base64)

@app.route('/addLike/<photo_id>', methods=['GET','POST'])
@flask_login.login_required
def add_like(photo_id):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Likes WHERE user_id = %s AND picture_id = %s", (uid, photo_id))
    count = cursor.fetchone()[0]
    if count > 0:
        return render_template("hello.html", name=flask_login.current_user.id, message="You've already liked this photo!", base64=base64)
    cursor.execute('''INSERT INTO Likes (user_id, picture_id) VALUES (%s, %s)''', (uid, photo_id))
    conn.commit()
    
    return render_template("hello.html", name=flask_login.current_user.id, message="Photo liked!", base64=base64)



@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		album_name = session.get('album_name')
		cursor = conn.cursor()
		aid = getAlbumId(album_name,uid)
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, aid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
		#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
	


#end photo uploading code
@app.route('/addfriends', methods=['GET','POST'])
@flask_login.login_required
def add_friends():
	if request.method == 'POST':
		friend_id = request.form.get("friend_id")
		fid = getUserIdFromEmail(friend_id)
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		#check to see if friend is already inserted into table
		cursor.execute("SELECT * FROM Friends WHERE user_id = '{0}' AND friend_id = '{1}'".format(user_id, fid))
		if cursor.fetchone():
			return render_template('hello.html', name=flask_login.current_user.id, message='Friend already added!')
		else:
			cursor.execute("INSERT INTO Friends (user_id, friend_id) VALUES ('{0}', '{1}')".format(user_id, fid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Friend added!')
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('addfriends.html')

@app.route('/addTags/<caption>/<id>', methods=['GET','POST'])
@flask_login.login_required
def add_tags(caption,id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		tagt = request.form.get("Tag")
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM Tags WHERE picture_id = '{0}' AND tag_text = '{1}'".format(id, tagt))
		if cursor.fetchone():
			return render_template('hello.html', name=flask_login.current_user.id, message='Tag already added!')
		else:
			cursor.execute("INSERT INTO Tags (picture_id, user_id,tag_text) VALUES ('{0}', '{1}', '{2}')".format(id, uid,tagt))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Tag added!')
	else:
		return render_template('addTags.html')
	
@app.route('/addComments/<caption>/<id>', methods=['GET','POST'])
def add_comments(caption, id):
    if request.method == 'POST':
        comt = request.form.get("comment")
        cursor = conn.cursor()
        if flask_login.current_user.is_authenticated:
            uid = getUserIdFromEmail(flask_login.current_user.id)
            cursor.execute("INSERT INTO Comments (picture_id, user_id, comment_text) VALUES (%s, %s, %s)", (id, uid, comt))
            conn.commit()
            return render_template('hello.html', name=flask_login.current_user.id, message='Comment added!')
        else:
            cursor.execute("INSERT INTO Comments (picture_id, user_id, comment_text) VALUES (%s, NULL, %s)", (id, comt))
            conn.commit()
            return render_template('hello.html', message='Comment added!')
    else:
        return render_template('addComments.html')


@app.route('/mytags', methods=['GET','POST'])
@flask_login.login_required
def my_tags():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT tag_text FROM Tags WHERE user_id = %s", (uid,))
	new_tag = []
	tags = cursor.fetchall()
	for tags in tags:
		new_tag.append(tags[0])
	return render_template('mytaggedphotos.html', tags= new_tag)
@app.route('/browsemytaggedphotos/<tag>', methods=['GET','POST'])
@flask_login.login_required
def my_tagged_photos(tag):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT picture_id FROM Tags WHERE user_id = %s AND tag_text = %s", (uid, tag))
    pic_ids = cursor.fetchall()
    pic_ids = [pic[0] for pic in pic_ids]
    if not pic_ids:
        return render_template('hello.html', name=flask_login.current_user.id, message='No photos tagged with this tag!')
    cursor.execute("SELECT imgdata, caption, picture_id FROM Pictures WHERE picture_id IN %s", (tuple(pic_ids),))
    photos = []
    for row in cursor.fetchall():
        id = row[2]
        photo = row[0]
        image_data = base64.b64encode(photo).decode('utf-8')
        caption = row[1]
        cursor.execute("SELECT tag_text FROM Tags WHERE picture_id = %s", (id,))
        tags = [tag[0] for tag in cursor.fetchall()]
        photos.append({'id': id, 'image_data': image_data, 'caption': caption, 'tags': tags})
    return render_template('browsemytagphotos.html', photos=photos, base64=base64)


def getEmailFromUserId(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id = %s", (uid,))
	email = cursor.fetchone()[0]
	return email
@flask_login.login_required
def friendRecommendations(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT friend_id FROM Friends WHERE user_id = %s", (uid,))
    friends = cursor.fetchall()
    friend_ids = [friend[0] for friend in friends]
    if not friend_ids:
        return []
    cursor.execute("SELECT user_id, COUNT(*) as count FROM Friends WHERE friend_id IN %s AND user_id NOT IN (SELECT friend_id FROM Friends WHERE user_id = %s) AND user_id != %s GROUP BY user_id ORDER BY count DESC", (tuple(friend_ids), uid, uid))
    friend_recommendations = cursor.fetchall()
    friend_recommendations = [(getEmailFromUserId((friend[0])), friend[1]) for friend in friend_recommendations]
    friend_recommendations = sorted(friend_recommendations, key=lambda x: x[1], reverse=True)
    friend_recommendations = [friend[0] for friend in friend_recommendations]
    return friend_recommendations


@flask_login.login_required
def postRecommendations(uid):
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Users WHERE user_id = %s", (uid,))
    result = cursor.fetchone()
    if result[0] == 0:
        return []
    
    cursor.execute("SELECT tag_text, COUNT(*) as tag_count FROM Tags WHERE user_id = %s GROUP BY tag_text ORDER BY tag_count DESC LIMIT 3", (uid,))
    tags = cursor.fetchall()
    tag_list = tuple(tag[0] for tag in tags)
    
    cursor.execute("SELECT user_id, picture_id, imgdata, caption FROM Pictures WHERE picture_id IN (SELECT picture_id FROM Tags WHERE tag_text IN %s)", (tag_list,))
    photos = cursor.fetchall()
    results = []
    for photo in photos:
        if photo[0] != uid:
            results.append({
                'id': photo[1],
                'image_data': base64.b64encode(photo[2]).decode('utf-8'),
                'caption': photo[3],
                'tags': [tag[0] for tag in tags],
            })
    return results




@app.route('/recommendation', methods=['GET', 'POST'])
@flask_login.login_required
def recommendation():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    friends = friendRecommendations(uid)
    posts = postRecommendations(uid)
    return render_template('recommendations.html', posts=posts, friends = friends)



#default page
@app.route("/", methods=['GET'])
def hello():	
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
