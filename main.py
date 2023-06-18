from flask import request, render_template, redirect, url_for, abort
from werkzeug.utils import secure_filename
from flask_login import login_required, login_user, logout_user, current_user
import uuid, os
import datetime as dt
from sqlalchemy import desc

from __init_app__ import app
from models import db, User, Follow, Post, Like, Comment, Notification
from auth import login_manager, bcrypt, LoginForm, SignupForm, EditProfileForm

db.init_app(app)
app.app_context().push()
with app.app_context(): 
    db.create_all()

#--------------------------------------------UTILITY FUNCTIONS------------------------------------------
def check_file(file):
    if '.' not in file:
        return False
    allowed_extensions = ['jpg', 'png', 'jpeg']
    extension = file.split('.')[1].lower()

    if extension not in allowed_extensions:
        return False
    return True

def check_size(size):
    if int(size) > 10000000:
        return False
    return True

def time_stamp(t):
    diff = dt.datetime.now() - t
    t_diff=0
    flag='s'
    if diff.seconds < 60:
        t_diff = int(diff.seconds)
        return [t_diff, flag]
    else:
        t_diff = round(diff.seconds / 60)
        flag='min'
        if t_diff >= 60:
            if diff.days >= 1:
                t_diff = round(diff.days)
                flag='d'
            elif diff.days >= 7:
                t_diff = round(diff.days / 7)
                flag='w'
                if t_diff >= 4:
                    t_diff = round(t_diff / 4)
                    flag='mo'
                if t_diff >= 12:
                    t_diff = dt.datetime.strptime(t, "%d %m %y")
                    flag=''
            else:
                t_diff = round(t_diff / 60)
                flag='h'
    return [t_diff, flag]

def delete_image(filename):
    if filename is None or filename == '':
        return
    os.remove(os.path.join(app.config['UPLOADS'], filename))

def trigger_notification(user, type, context, value, current_user):
    timestamp = dt.datetime.now()
    if type=='user':
        action = '/profile/'+str(value)
        content = '{} started following you'.format(current_user.username)
    if type=='post':
        action = '/post/'+str(value)
        if context=='like':
            content = '{} liked your post'.format(current_user.username)
        if context=='comment':
            content = '{} commented on your post'.format(current_user.username)
    
    n = Notification(timestamp=timestamp, to_notify=user, content=content, action=action)
    return n

#--------------------------------------------ROUTES----------------------------------------------------------
@app.route('/')
@app.route('/feed') 
@app.route('/home') 
@app.route('/index') 
@app.route('/main', methods=['GET'])
@login_required
def feed():
    users=[]
    for user in current_user.following:
        users.append(user.user_id)
    posts = Post.query.filter(Post.archieved==False).filter(Post.author.in_(users)).order_by(desc(Post.created_on)).all()
    time_var=[]
    time_diff = []
    for post in posts:
        if len(post.title) > 42:
            post.title = post.title[0:43]+'...'
        if len(post.content) > (56*3-9):
            post.content = post.content[0:158]+'...'
        output = time_stamp(post.created_on)
        time_diff.append(output[0])
        time_var.append(output[1])
    return render_template('index.html', posts=posts, time_diff=time_diff, time_var=time_var, current_user=current_user)

@app.route('/create', methods=['GET','POST'])
@login_required
def create():
    if request.method=='POST':
        form = request.form
        title = form['title']
        content = form['content']
        time=dt.datetime.now()
        post = Post(author=current_user.user_id, title=title, content=content, created_on=time)

        if request.files:
            image = request.files["img"]
            f_name=secure_filename(image.filename)
            if f_name != '':
                if not check_file(f_name):
                    return 'Image extension not supported', 404

                if not check_size(request.cookies['size']):
                    return 'Image size exceeded!', 404
                
                filename = str(uuid.uuid4())+"."+f_name.split('.')[1]

                image.save(os.path.join(app.config['UPLOADS'], filename))
                post.img = filename
        
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('post', post_id=post.post_id))
    
    else:
        return render_template('create.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'GET':
        return render_template('search.html')
    else: 
        form = request.form
        if form['query']:
            query=form['query']
            users = User.query.filter((User.user_id != current_user.user_id) & (User.username.like(query+'%') | User.name.like(query+'%'))).all()
            if len(users) == 0:
                users=False
        return render_template('search.html', results=users)

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/<username>', methods=['GET'])
@login_required
def view_profile(username):
    if username == current_user.username:
        return redirect(url_for('profile'))
    user = User.query.filter_by(username=username).first()
    if user is None:
        return abort(404)
    following=True
    if current_user not in user.followers:
        following=False
    post_count = 0
    for post in user.posts:
        if post.archieved == False:
            post_count += 1
    return render_template('view_profile.html', user=user, following=following, post_count = post_count)

@app.route('/follow/<username>', methods=['GET'])
@login_required
def follow_action(username):
    user = User.query.filter_by(username=username).first()
    follow_act = Follow(follower=current_user.user_id, following=user.user_id)
    db.session.add(follow_act)
    db.session.commit()
    n=trigger_notification(user=user.user_id, type='user', context='follow', value=current_user.username, current_user=current_user)
    db.session.add(n)
    db.session.commit()
    return redirect(url_for('view_profile', username=username))

@app.route('/unfollow/<username>', methods=['GET'])
@login_required
def unfollow_action(username):
    user = User.query.filter_by(username=username).first()
    follow_act = Follow.query.filter_by(follower=current_user.user_id, following=user.user_id).first()
    db.session.delete(follow_act)
    db.session.commit()
    return redirect(url_for('view_profile', username=username))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        if form.image.data:
            image = form.image.data
            f_name=secure_filename(image.filename)
            if f_name != '':
                if not check_file(f_name):
                    return 'Image extension not supported', 404

                if not check_size(request.cookies['size']):
                    return 'Image size exceeded!', 404
                
                filename = str(uuid.uuid4())+"."+f_name.split('.')[1]
                image.save(os.path.join(app.config['UPLOADS'], filename))
                if current_user.pic:
                    delete_image(current_user.pic)
                current_user.pic = filename

        if form.bio.data:
            current_user.bio = form.bio.data
        else:
            current_user.bio = None    
        try:
            db.session.add(current_user)
        except:
            db.session.rollback()
        else:
            db.session.commit()
        return redirect(url_for('profile'))

    form.name.data = current_user.name
    form.bio.data = current_user.bio
    return render_template('edit_profile.html', form=form, user=current_user)

@app.route('/delete_profile', methods=['GET'])
def delete_profile():
    Follow.query.filter_by(follower=current_user.user_id).delete()
    Follow.query.filter_by(following=current_user.user_id).delete()
    Like.query.filter_by(liked_by=current_user.user_id).delete()
    if current_user.pic:
        delete_image(current_user.pic)
    for post in current_user.posts:
        if post.img:
            delete_image(post.img)
        Like.query.filter_by(post_id=post.post_id).delete()
    db.session.delete(current_user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/post/<post_id>', methods=['GET'])
@login_required
def post(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    if post is None:
        return abort(404)
    if post.created_by != current_user and post.archieved==True:
        return abort(404)
    author = User.query.filter_by(user_id=post.author).first()
    return render_template('post.html', post=post, author=author, current_user_id=current_user.user_id)

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    if post is None:
        return abort(404)
    if post.created_by != current_user:
            return abort(403)
    if request.method == 'GET':
        return render_template('edit_post.html', post=post)
    else:
        form = request.form
        if form:
            new_content = form['content']
        if len(new_content) > 310:
            return 'Content Length Exceeded', 403
        post.content = new_content
        if request.files:
            image = request.files["img"]
            f_name=secure_filename(image.filename)
            if f_name != '':
                if not check_file(f_name):
                    return 'Image extension not supported', 404

                if not check_size(request.cookies['size']):
                    return 'Image size exceeded!', 404
                
                filename = str(uuid.uuid4())+"."+f_name.split('.')[1]
                image.save(os.path.join(app.config['UPLOADS'], filename))

                if post.img:
                    delete_image(post.img)
                post.img = filename
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('post', post_id=post.post_id))

@app.route('/delete_post/<post_id>', methods=['GET'])
@login_required
def delete_post(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    if post is None:
        return abort(404)
    if post.created_by != current_user:
        return abort(404)
    if post.img:
        delete_image(post.img)
    Like.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    return redirect('/profile')

# PROFILE ROUTES
@app.route('/followers/<username>', methods=['GET'])
def followers(username):
    user = User.query.filter_by(username=username).first()
    followers=[]
    for u in user.followers:
        followers.append(u)
    return render_template('users_renderer.html', users=followers, title='Followers')

@app.route('/following/<username>', methods=['GET'])
def following(username):
    user = User.query.filter_by(username=username).first()
    following=[]
    for u in user.following:
        following.append(u)
    return render_template('users_renderer.html', users=following, title='Following')

@app.route('/like/<post_id>', methods=['GET'])
@login_required
def like(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    if post is None:
        return abort(404)
    if post.archieved == True and post.created_by != current_user:
        return abort(404)
    if current_user not in post.likes:
        like = Like(post_id=post_id, liked_by=current_user.user_id)
        db.session.add(like)
        db.session.commit()
        if post.author != current_user.user_id:
            n=trigger_notification(user=post.author, type='post', context='like', value=post.post_id, current_user=current_user)
            db.session.add(n)
            db.session.commit()
        return {'message':'Liked'}, 200
    else:
        post.likes.remove(current_user)
        db.session.add(post)
        db.session.commit()
        return {'message':'Disliked'}, 200


@app.route('/likes/<post_id>', methods=['GET'])
@login_required
def likes(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    if post is None:
        return abort(404)
    return render_template('users_renderer.html', users=post.likes, title='Likes')

@app.route('/comment/<post_id>', methods=['POST'])
@login_required
def comment(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    if post is None:
        return abort(404)
    if post.archieved == True:
        return abort(404)
    form = request.form
    text = form['comment']
    if len(text) > 200:
        return 'Comment length exceeded', 403
    comment = Comment(comment_by=current_user.user_id, comment=text)
    post.comments.append(comment)
    db.session.add(post)
    db.session.commit()
    if post.author != current_user.user_id:
        n = trigger_notification(user=post.author, type='post', context='comment', value=post.post_id, current_user=current_user)
        db.session.add(n)
        db.session.commit()
    return redirect(url_for('post', post_id=post_id))

@app.route('/remove_comment/<comment_id>', methods=['GET'])
@login_required
def remove_comment(comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    post_id = comment.post.post_id
    if comment.commentor == current_user or comment.post.created_by == current_user:
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for('post', post_id=post_id))
    else:
        return abort(404)

@app.route('/archieve/<post_id>', methods=['GET'])
@login_required
def archieve(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    if post is None or post.created_by != current_user:
        return abort(404)
    
    if post.archieved == True:
        post.archieved = False
    else:
        post.archieved=True
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/archieved', methods=['GET'])
@login_required
def archieved():
    archieved_posts=[]
    for post in current_user.posts:
        if post.archieved == True:
            archieved_posts.append(post)
    return render_template('posts_renderer.html', posts=archieved_posts, title='Archieved')

@app.route('/notifications', methods=['GET'])
@login_required
def notifications():
    n=current_user.notifications
    for i in n:
        i.seen = True
    db.session.add(current_user)
    db.session.commit()
    notifications=[]
    timestamp=[]
    for i in range(len(n)-1,-1,-1):
        time = time_stamp(n[i].timestamp)
        timestamp.append(str(time[0])+" "+time[1])
        notifications.append(n[i])
    return render_template('notification.html', notifications=notifications, timestamp=timestamp)

@app.route('/clear/<not_id>', methods=['GET'])
@login_required
def clear(not_id):
    n = Notification.query.filter_by(notification_id=not_id).first()
    if n.to_notify != current_user.user_id:
        return abort(403)
    db.session.delete(n)
    db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/clear_all', methods=['GET'])
@login_required
def clear_all():
    for i in range(len(current_user.notifications)):
        current_user.notifications.pop()
    db.session.add(current_user)
    db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/n-badge', methods=['GET'])
def n_badge():
    count = 0
    for n in current_user.notifications:
        if n.seen==False:
            count+=1
    return {'count': count}, 200

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ------------------------------------------AUTH ROUTES--------------------------------------------------
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        login_user(user)
        if 'next' in request.args:
            return redirect(request.args['next'])
        else:
            return redirect(url_for('feed'))
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET','POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password, name=form.name.data, role='USER')
        if form.image.data:
            image = form.image.data
            f_name=secure_filename(image.filename)
            if not check_file(f_name):
                return 'Image extension not supported', 404

            if not check_size(request.cookies['size']):
                return 'Image size exceeded!', 404
            
            filename = str(uuid.uuid4())+"."+f_name.split('.')[1]
            new_user.pic = filename

            image.save(os.path.join(app.config['UPLOADS'], filename))
        if form.bio.data:
            new_user.bio = form.bio.data    
        try:
            db.session.add(new_user)
        except:
            db.session.rollback()
        else:
            db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)

#-----------------------------------ERROR HANDLERS-----------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# Running the app
if __name__=='__main__':
    app.run(debug=True)
