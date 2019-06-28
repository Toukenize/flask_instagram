from flask import Flask, render_template, url_for, flash, redirect, request, abort, session
from forms import RegistrationForm, LoginForm, PostForm, SearchForm
from PIL import Image

import requests
import base64
import time
import io
import secrets
import os

application = app = Flask(__name__)
app.config['SECRET_KEY'] = 'some_super_random_key_that_youu_willl_neverr_guesss_correctlyy'

@app.route("/register", methods=['GET', 'POST'])
def register():
    
    form = RegistrationForm()
    if form.validate_on_submit():
        
        signup_details = dict()
        signup_details['username'] = form.username.data
        signup_details['password'] = form.password.data
        
        status = requests.post('https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/user/create', json=signup_details)
        
        if status.status_code != 200:
            flash('Something went wrong, please creating your account again', 'danger')
        else:
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/", methods=['GET', 'POST'])    
@app.route("/home")
def home():
        
    if 'username' not in session:
        return redirect(url_for('login'))
        
    status = requests.get(f'https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/loginuser/{session["username"]}',
    headers={'content-type':'application/json','authorization':session['token']})
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        try:
            posts = status.json()
            posts = sorted(posts, key=lambda x : x['datetime'], reverse=True)
        except:
            flash('Something went wrong...','Danger')
    
    return render_template('home.html', posts=posts)

    
@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        
        login_details = dict()
        
        login_details['username'] = form.username.data
        login_details['password'] = form.password.data
        
        status = requests.post('https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/user/signin', json=login_details)
        
        if status.status_code != 200 or (status.json()['status'] == 'fail'):
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
        else:
            session['username'] = login_details['username']
            session['authenticated'] = True
            session['token'] = status.json()['id_token']
                        
            return redirect(url_for('home'))
    return render_template('login.html', title='Login', form=form)
    
def resize_encode_img(image_data):
    
    output_size = (800,800)
    temp_file_name = secrets.token_hex(8) + '.jpg'
    
    image = Image.open(image_data)
    image.thumbnail(output_size)
    image.save(temp_file_name)

    with open(temp_file_name,'rb') as image_handle:
        encoded_string = base64.b64encode(image_handle.read())
        
    os.remove(temp_file_name)
    
    return encoded_string
    
@app.route("/new_post", methods=['POST','GET'])
def new_post():
    
    if 'username' not in session:
        return redirect(url_for('login'))
    
    form = PostForm()
    if form.validate_on_submit():
                
        encoded_string = resize_encode_img(form.content.data)
        picture_details = dict()
        picture_details['username'] = session['username']
        picture_details['title'] = form.title.data
        picture_details['image_base64'] = encoded_string.decode()
        
        status = requests.post('https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/postpicture', json=picture_details, headers={'content-type':'application/json','authorization':session['token']})
        
        if status.status_code != 200 or (status.json().get('statusCode') != 200) or (status.json().get('message') == 'Unauthorized'):
            flash('Something went wrong, please try again', 'danger')
        else:
            flash('Your picture has been posted!', 'success')
            time.sleep(3)
            return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')

@app.route("/account", methods=['POST','GET'])
def account():
    if 'username' not in session:
        return redirect(url_for('login'))

    status = requests.get(f'https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/loginuser/queryuserpictureby/{session["username"]}', headers={'content-type':'application/json','authorization':session['token']})
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        try:
            posts = status.json()
            if len(posts) > 0:
                posts = [x for x in posts if x['by'] == session['username']]
                posts = sorted(posts, key=lambda x : x['datetime'], reverse=True)
        except:
            posts = []
 
    return render_template('account.html', title='My Account', posts=posts)

@app.route("/search_user", methods=['POST','GET'])
def search_user():
    
    if 'username' not in session:
        return redirect(url_for('login'))
    
    form = SearchForm()
    if form.validate_on_submit():
        query = form.username.data
        return redirect(url_for('search_results', query=query))
    
    return render_template('search_user.html', title='Search User', form=form)

@app.route("/search_results/<string:query>", methods=['POST','GET'])
def search_results(query):

    if 'username' not in session:
        return redirect(url_for('login'))
    
    status = requests.get(f'https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/loginuser/queryuser/{session["username"]}/{query}', headers={'content-type':'application/json','authorization':session['token']})
    if status.status_code != 200 or (type(status.json()) != list):
        flash('Something went wrong...','Danger')
    else:
        query_results = status.json()      

    return render_template('search_results.html', title='Search Results', query_results=query_results, query=query)

@app.route("/follow/<string:user>", methods=['POST','GET'])
def follow_user(user):

    if 'username' not in session:
        return redirect(url_for('login'))
    
    status = requests.put(f'https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/loginuser/follow/{user}', json={'username':session["username"]}, headers={'content-type':'application/json','authorization':session['token']})
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        return redirect(request.referrer)      

@app.route("/unfollow/<string:user>", methods=['POST','GET'])
def unfollow_user(user):

    if 'username' not in session:
        return redirect(url_for('login'))
    
    status = requests.put(f'https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/loginuser/unfollow/{user}', json={'username':session["username"]}, headers={'content-type':'application/json','authorization':session['token']})
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        return redirect(request.referrer) 
    
@app.route("/logout", methods=['POST','GET'])
def logout():
    session.pop('username', None)    
    session.pop('token', None)
    session.pop('authenticated', None)
    flash('You have successfully logged out.','success')
    
    return redirect(url_for('login'))

@app.route("/user/<string:username>", methods=['POST','GET'])
def user_posts(username):
    
    if 'username' not in session:
        return redirect(url_for('login'))
    
    status = requests.get(f'https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/loginuser/queryuserpictureby/{username}', headers={'content-type':'application/json','authorization':session['token']})
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        try:
            posts = status.json()
            if len(posts) > 0:
                posts = [x for x in posts]
                posts = sorted(posts, key=lambda x : x['datetime'], reverse=True)
        except:
            posts = []
    
    return render_template('user_account.html', title=f"{username}'s Posts", posts=posts)

@app.route("/like/<string:thumb_id>", methods=['POST','GET'])
def like(thumb_id):
    
    if 'username' not in session:
        return redirect(url_for('login'))

    put_details = {'username':session['username']}
    status = requests.put(f'https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/picture/like/{thumb_id}', json=put_details, headers={'content-type':'application/json','authorization':session['token']})
    return redirect(request.referrer)

@app.route("/unlike/<string:thumb_id>", methods=['POST','GET'])
def unlike(thumb_id):
    
    if 'username' not in session:
        return redirect(url_for('login'))
    
    put_details = {'username':session['username']}
    status = requests.put(f'https://mnu7f7vb6l.execute-api.ap-southeast-1.amazonaws.com/ISS/picture/unlike/{thumb_id}', json=put_details, headers={'content-type':'application/json','authorization':session['token']})
    return redirect(request.referrer)

@app.route("/picture/<string:title>/<string:url_id>", methods=['POST','GET'])
def picture(title, url_id):
    
    if 'username' not in session:
        return redirect(url_for('login'))
    
    image_url_id = url_id.split('resized-')[-1]
    
    high_res_url = 'https://5239original.s3-ap-southeast-1.amazonaws.com/image/' + image_url_id
    
    print(high_res_url)
    
    return render_template('image.html', title=title, high_res_url=high_res_url)

    
if __name__ == '__main__':
    app.run(debug=True)