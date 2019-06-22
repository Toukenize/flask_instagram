from flask import Flask, render_template, url_for, flash, redirect, request, abort
from forms import RegistrationForm, LoginForm, FollowForm, UpdateAccountForm, PostForm, SearchForm
from PIL import Image

import secrets
import requests
import os

application = app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
user_details = dict()
user_details['authenticated'] = False

@app.route("/register", methods=['GET', 'POST'])
def register():
    global user_details
    
    if user_details['authenticated']:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        
        signup_details = dict()
        signup_details['usernamesignup'] = form.username.data
        signup_details['passwordsignup'] = form.password.data
        signup_details['emailsignup'] = form.email.data
        
        status = requests.post('http://la-entrada.ap-southeast-1.elasticbeanstalk.com/user/create', json=signup_details)
        
        if status.status_code != 200:
            flash('Something went wrong, please creating your account again', 'danger')
        else:
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, user_details=user_details)

@app.route("/", methods=['GET', 'POST'])    
@app.route("/home")
def home():
    global user_details
    if not user_details['authenticated']:
        return redirect(url_for('login'))
        
    status = requests.get(f'http://la-nube.ap-southeast-1.elasticbeanstalk.com/loginuser/{user_details["username"]}')
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        posts = status.json()
        
    posts = sorted(posts, key=lambda x : x['datetime'], reverse=True)
    
    return render_template('home.html', posts=posts, user_details=user_details)

    
@app.route("/login", methods=['GET', 'POST'])
def login():
    global user_details
    if user_details['authenticated']:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        
        login_details = dict()
        
        login_details['usernamesignup'] = form.username.data
        login_details['passwordsignup'] = form.password.data
        
        status = requests.post('http://la-entrada.ap-southeast-1.elasticbeanstalk.com/user/signin', json=login_details)
        
        if status.status_code != 200:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
        else:
            
            for k, v in status.json().items():
                user_details[k] = v
            
            user_details['authenticated'] = True
            
            return redirect(url_for('home'))
    return render_template('login.html', title='Login', form=form, user_details=user_details)

def post_picture(form_picture): 
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images', picture_fn)

    #output_size = (125, 125)
    i = Image.open(form_picture)
    #i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

    
@app.route("/new_post", methods=['POST','GET'])
def new_post():
    global user_details
    form = PostForm()
    if form.validate_on_submit():
        picture_file = post_picture(form.content.data)
        
        picture_details = dict()
        picture_details['username'] = user_details['username']
        picture_details['title'] = form.title.data
        picture_details['large_url'] = picture_file
        
        status = requests.post('http://la-nube.ap-southeast-1.elasticbeanstalk.com/picture', json=picture_details)
        
        if status.status_code != 200:
            flash('Something went wrong, please try again', 'danger')
        else:
            flash('Your picture has been posted!', 'success')
            return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post', user_details=user_details)

@app.route("/account", methods=['POST','GET'])
def account():
    global user_details
    status = requests.get(f'http://la-nube.ap-southeast-1.elasticbeanstalk.com/loginuser/{user_details["username"]}')
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        posts = status.json()
        
    posts = [x for x in posts if x['by'] == user_details['username']]
    posts = sorted(posts, key=lambda x : x['datetime'], reverse=True)
 
    return render_template('account.html', title='My Account', posts=posts, user_details=user_details)

@app.route("/search_user", methods=['POST','GET'])
def search_user():
    global user_details
    form = SearchForm()
    if form.validate_on_submit():
        query = form.username.data
        return redirect(url_for('search_results', query=query))
    
    return render_template('search_user.html', title='Search User', form=form, user_details=user_details)

@app.route("/search_results/<string:query>", methods=['POST','GET'])
def search_results(query):
    global user_details
    status = requests.get(f'http://la-nube.ap-southeast-1.elasticbeanstalk.com/loginuser/queryuser/{user_details["username"]}/{query}')
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        query_results = status.json()      

    return render_template('search_results.html', title='Search Results', user_details=user_details, query_results=query_results, query=query)

@app.route("/follow/<string:user>", methods=['POST','GET'])
def follow_user(user):
    global user_details
    print(user_details)
    status = requests.put(f'http://la-nube.ap-southeast-1.elasticbeanstalk.com/loginuser/follow/{user}', json={'username':user_details["username"]})
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        return redirect(request.referrer)      

@app.route("/unfollow/<string:user>", methods=['POST','GET'])
def unfollow_user(user):
    global user_details
    print(user_details)
    status = requests.put(f'http://la-nube.ap-southeast-1.elasticbeanstalk.com/loginuser/unfollow/{user}', json={'username':user_details["username"]})
    if status.status_code != 200:
        flash('Something went wrong...','Danger')
    else:
        return redirect(request.referrer) 
    
@app.route("/logout", methods=['POST','GET'])
def logout():
    global user_details
    return render_template('logout.html', title='Logout', user_details=user_details)

@app.route("/user/<string:username>", methods=['POST','GET'])
def user_posts(username):
    global user_details
    return render_template('user_posts.html', title=f"{username}'s Posts", user_details=user_details)

@app.route("/like/<string:thumb_id>", methods=['POST','GET'])
def like(thumb_id):
    global user_details
    put_details = {'username':user_details['username']}
    status = requests.put(f'http://la-nube.ap-southeast-1.elasticbeanstalk.com/picture/like/{thumb_id}', json=put_details)
    print(status.status_code, thumb_id)
    return redirect(request.referrer)

@app.route("/unlike/<string:thumb_id>", methods=['POST','GET'])
def unlike(thumb_id):
    global user_details
    put_details = {'username':user_details['username']}
    status = requests.put(f'http://la-nube.ap-southeast-1.elasticbeanstalk.com/picture/unlike/{thumb_id}', json=put_details)
    return redirect(request.referrer)

if __name__ == '__main__':
    app.run(debug=True)