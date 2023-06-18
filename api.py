from flask_restful import Api, Resource, request
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import uuid, os, datetime as dt, base64, re
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager

from __init_app__ import app
from models import db, User, Post

api = Api(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

db.init_app(app)
app.app_context().push()

#-------------------------------------UTILITY FUNCTIONS-------------------------------------------
user_username_validate = re.compile('^[a-zA-Z0-9]*$')
user_name_validate = re.compile('^[a-zA-Z]*\s?[a-zA-Z]*$')

def check_file(file):
    if '.' not in file:
        return False
    allowed_extensions = ['jpg', 'png', 'jpeg']
    extension = file.split('.')[1].lower()

    if extension not in allowed_extensions:
        return False
    return True


def check_user_exist(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return True
    return False

def delete_image(filename):
    if filename is None or filename == '':
        return
    os.remove(os.path.join(app.config['UPLOADS'], filename))

#-----------------------------------------APIs-----------------------------------------------

class SignUpAPI(Resource):
    def post(self):
        form = request.form
        username = form.get('username')
        name = form.get('name')
        password = form.get('password')
        bio = form.get('bio')

        if not username:
            return 'Username required', 409
        if check_user_exist(username):
            return 'Username already exists', 409
        if not name:
            return 'Name required', 409
        if not password:
            return 'Password required', 409
        if password.strip() == '' or password[0] == ' ' or password[-1] == ' ':
            return 'Invalid password', 409
        password = password.strip()

        if len(username) < 4 or len(username) > 20 or not user_username_validate.match(username):
            return 'Invalid Username', 409
        if len(name) < 2 or len(name) > 50 or not user_name_validate.match(name):
            return 'Invalid Name', 409
        if len(password) < 4:
            return 'Password too small', 409
        if len(password) > 20:
            return 'Password too long', 409

        hashed_password = bcrypt.generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, name=name, role='USER')
        image = request.files.get('image')
        if image:
            image = form.get('image')
            f_name=secure_filename(image.filename)
            if not check_file(f_name):
                return {"error_code": "IMGERROR", "error_message": "Image extension not supported"}, 400
            
            filename = str(uuid.uuid4())+"."+f_name.split('.')[1]
            new_user.pic = filename

            image.save(os.path.join(app.config['UPLOADS'], filename))
        if bio:
            new_user.bio = bio  
        try:
            db.session.add(new_user)
        except:
            db.session.rollback()
        else:
            db.session.commit()
            return 'User created successfully', 201

class AccessTokenAPI(Resource):
    def post(self):
        request_body = request.get_json()
        username = request_body.get('username')
        password = request_body.get('password')
        if username is None:
            return {'error_code': 'USER01', 'error_message': 'Username required'}
        if password is None:
            return {'error_code': 'PASS01', 'error_message': 'Password required'}

        user = User.query.filter_by(username=username).first()
        if user is None:
            return 'User not found', 409
        if bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=username)
            return {'token': access_token}, 200
        else:
            return 'Incorrect password', 409

class UserAPI(Resource):
    def get(self, username):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return 'User not found', 404

        posts = []

        for post in user.posts:
            posts.append({'post_id': post.post_id, 'title': post.title, 'content': post.content, 'like_count': len(post.likes), 'comment_count': len(post.comments), 'image': post.img})
        
        return {'user_id': user.user_id, 'username': user.username, 'name': user.name, 'bio': user.bio, 'pic': user.pic, 'follower_count': len(user.followers), 'following_count': len(user.following), 'posts': posts}, 200

    @jwt_required()
    def put(self, username):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return 'User not found', 404

        identify_token_username = get_jwt_identity()
        if identify_token_username != username:
            return 'You are not permitted!', 403
        
        form = request.form
        name = form.get('name')
        bio = form.get('bio')
        if not name:
            return {'error_code': 'USER01', 'error_message': 'Name is required'}, 400

        if name.strip() == '':
            return {'error_code': 'USER02', 'error_message': 'Name cannot be null'}, 400

        user.name = name
        user.bio = bio
        image = request.files.get('image')

        if image:
            f_name=secure_filename(image.filename)
            if not check_file(f_name):
                return {"error_code": "IMGERROR", "error_message": "Image extension not supported"}, 400

            
            filename = str(uuid.uuid4())+"."+f_name.split('.')[1]
            image.save(os.path.join(app.config['UPLOADS'], filename))

            delete_image(user.pic)
            user.pic = filename

        db.session.add(user)
        db.session.commit()
        return 'User updated successfully', 200

    @jwt_required()
    def delete(self, username):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return 'User not found', 404

        identify_token_username = get_jwt_identity()
        if identify_token_username != username:
            return 'You are not permitted!', 403

        db.session.delete(user)
        db.session.commit()
        return 'Successfully Deleted', 200

class PostAPI(Resource):
    @jwt_required()
    def post(self, username):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return 'User not found', 404
        
        identify_token_username = get_jwt_identity()
        if identify_token_username != username:
            return 'You are not permitted!', 403

        form = request.form
        title = form.get('title')
        if title is None:
            return {'error_code': 'POST01', 'error_message': 'Title is required'}, 400
        if title.strip() == '':
            return {'error_code': 'POST02', 'error_message': 'Title cannot be null'}, 400
        content = form.get('content')
        if content is None:
            return {'error_code': 'POST03', 'error_message': 'Content is required'}, 400
        if content.strip() == '':
            return {'error_code': 'POST04', 'error_message': 'Content cannot be null'}, 400
        
        time=dt.datetime.now()
        post = Post(author=user.user_id, title=title, content=content, created_on=time)

        if request.files.get('image'):
            image = request.files.get('image')
            f_name=secure_filename(image.filename)
            if not check_file(f_name):
                return {"error_code": "IMGERROR", "error_message": "Image extension not supported"}, 400
            
            filename = str(uuid.uuid4())+"."+f_name.split('.')[1]
            image.save(os.path.join(app.config['UPLOADS'], filename))
            post.img = filename

        db.session.add(post)
        db.session.commit()

        img = None
        if post.img:
            img_file = open(os.path.join(app.config['UPLOADS'], post.img), 'rb')
            img = base64.b64encode(img_file.read()).decode('utf-8')

        return {'post_id': post.post_id, 'title': post.title, 'content': post.content, 'like_count': len(post.likes), 'comment_count': len(post.comments), 'image': img}, 201
        
    
    def get(self, post_id):
        post = Post.query.filter_by(post_id=post_id).first()
        if post is None:
            return 'Post not found', 404

        img = None
        if post.img:
            img_file = open(os.path.join(app.config['UPLOADS'], post.img), 'rb')
            img = base64.b64encode(img_file.read()).decode('utf-8')

        return {'post_id': post.post_id, 'title': post.title, 'content': post.content, 'like_count': len(post.likes), 'comment_count': len(post.comments), 'image': img}, 200

    @jwt_required()
    def put(self, username, post_id):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return 'User not found', 404
        identify_token_username = get_jwt_identity()
        if identify_token_username != username:
            return 'You are not permitted!', 403

        post = Post.query.filter_by(post_id=post_id).first()
        if post is None:
            return 'Post not found', 404
        if identify_token_username != post.created_by.username:
            return 'You are not permitted!', 403

        form = request.form
        content = form.get('content')
        if content is None:
            return {'error_code': 'POST03', 'error_message': 'Content is required'}, 400
        if content.strip() == '':
            return {'error_code': 'POST04', 'error_message': 'Content cannot be null'}, 400
        
        if request.files.get('image'):
            image = request.files.get('image')
            f_name=secure_filename(image.filename)
            if not check_file(f_name):
                return {"error_code": "IMGERROR", "error_message": "Image extension not supported"}, 400
            
            filename = str(uuid.uuid4())+"."+f_name.split('.')[1]
            image.save(os.path.join(app.config['UPLOADS'], filename))
            post.img = filename
        
        post.content = content

        db.session.add(post)
        db.session.commit()

        img = None
        if post.img:
            img_file = open(os.path.join(app.config['UPLOADS'], post.img), 'rb')
            img = base64.b64encode(img_file.read()).decode('utf-8')

        return {'post_id': post.post_id, 'title': post.title, 'content': post.content, 'like_count': len(post.likes), 'comment_count': len(post.comments), 'image': img}, 201

    @jwt_required()
    def delete(self, username, post_id):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return 'User not found', 404
        identify_token_username = get_jwt_identity()
        if identify_token_username != username:
            return 'You are not permitted!', 403

        post = Post.query.filter_by(post_id=post_id).first()
        if post is None:
            return 'Post not found', 404
        if identify_token_username != post.created_by.username:
            return 'You are not permitted!', 403

        delete_image(post.img)
        db.session.delete(post)
        db.session.commit()
        return 'Post deleted successfully', 200

api.add_resource(SignUpAPI, '/api/signup')
api.add_resource(AccessTokenAPI, '/api/access_token')
api.add_resource(UserAPI, '/api/user/<string:username>')
api.add_resource(PostAPI, '/api/user/<string:username>/post','/api/post/<int:post_id>', '/api/user/<string:username>/post/<int:post_id>')

if __name__=='__main__':
    app.run(debug=True)