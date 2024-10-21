from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, func, extract, and_
import random
from datetime import datetime, date, timedelta
import jwt
import json
from flask_cors import CORS, cross_origin
from functools import wraps

current_year = datetime.now().year
current_month = datetime.now().month

app = Flask(__name__)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'this is secret'
db = SQLAlchemy(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
api = Api(app)

class Payment(db.Model):
    payment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=True)
    
    splits = db.relationship('Split', backref='payment', lazy=True)

    def __repr__(self):
        return f"Payment('{self.payment_id}', '{self.amount}', '{self.time}')"
    
    def serialize(self):
        return {
            'payment_id': self.payment_id,
            'user_id': self.user_id,
            'amount': round(self.amount, 2),
            'time': datetime.strftime(self.time, "%d-%m-%Y"),
            'purpose': self.purpose,
            'status': self.status
        }

class Split(db.Model):
    split_id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.payment_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User receiving the split
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User paying the split
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Boolean, nullable=True)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"Split('{self.split_id}', '{self.amount}', '{self.time}')"
    
    def serialize(self):
        return {
            'split_id': self.split_id,
            'payment_id': self.payment_id,
            'purpose': Payment.query.filter(Payment.payment_id == self.payment_id).first().purpose,
            'user': User.query.filter(User.id == self.user_id).first().serialize(),
            'payer_id': User.query.filter(User.id == self.payer_id).first().serialize(),
            'amount': round(self.amount, 2),
            'paid': self.status,
            'status': self.status,
            'time': datetime.strftime(self.time, "%d-%m-%Y"),
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    confirmed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"User('{self.id}', '{self.name}', '{self.email}')"
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'username': self.username
        }
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if request.headers.get('x-access-token'):
            token = request.headers['x-access-token']
        if not token:
            return make_response(jsonify({'message': 'Token is missing!'}), 401)
        try:
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(
                id=data['public_id']).first()
        except:
            return make_response(jsonify({'message': 'Token is invalid!'}), 401)
        return f(current_user.id, *args, **kwargs)
    return decorated

# Check if API is working with each template render
class apiCheck(Resource):

    # Check API
    def get(self):
        return make_response(jsonify({'status': 'Success'}), 200)

api.add_resource(apiCheck, '/apiCheck')

# Register new user
class registerUser(Resource):

    # Register new user
    def post(self):
        data = request.args
        if User.query.filter_by(email=data['email']).first() or User.query.filter_by(username=data['username']).first():
            return make_response(jsonify({'message': 'Email or username already exists'}), 400)
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            name=data['name'],
            email=data['email'],
            username=data['username'],
            password=hashed_password,
            active=True,
            confirmed_at=datetime.now()
        )
        db.session.add(new_user)
        db.session.commit()
        return make_response(jsonify({'message': 'New user created!'}), 201)

api.add_resource(registerUser, '/api/register')

# User login
class Login(Resource):

    # Login a user and obtain JWT token
    def post(self):
        auth = request.args
        email = auth['email']
        password = auth['password']
        if not email or not password:
            return make_response(jsonify({'message': 'Please enter all fields!', 'status': 'error'}), 401)
        user = User.query.filter_by(email=email).first()
        if not user:
            return make_response(jsonify({'message': 'User does not exist!', 'status': 'error'}), 404)
        if check_password_hash(user.password, password):
            token = jwt.encode({'public_id': user.id, 'exp': datetime.now() + timedelta(minutes=30)},
                                  app.config['SECRET_KEY'], algorithm="HS256")
            return make_response(jsonify({'token': token, 'user_data': user.serialize(), 'status': 'success'}), 200)
        return make_response(jsonify({'message': 'Incorrect password!', 'status': 'error'}), 401)

api.add_resource(Login, '/api/login')


class searchUser(Resource):

        # Search for a user by username or email
        @token_required
        def get(self, current_user, search):
            users = User.query.filter(
                or_(User.name.like(f'%{search}%'), User.email.like(f'%{search}%'))
            ).all()
            users = [user.serialize() for user in users]
            return make_response(jsonify({'users': users}), 200)
        
api.add_resource(searchUser, '/api/search/<string:search>')

class userDetails(Resource):
    
        # Get user's details
        @token_required
        def get(self, current_user):
            return make_response(jsonify({'user': current_user.serialize()}), 200)
        
api.add_resource(userDetails, '/api/user')

class splits(Resource):

    # Get all splits where user_id maybe current user or payee might be current user
    @token_required
    def get(self, current_user):
        data = request.headers.get('x-access-token')
        payer_id = jwt.decode(data, app.config['SECRET_KEY'], algorithms=["HS256"])["public_id"]
        splits = Split.query.filter(
            or_(
                and_(Split.user_id == payer_id, Split.payer_id != payer_id),
                and_(Split.payer_id == payer_id, Split.user_id != payer_id)
            )
        ).order_by(Split.time.desc()).all()
        splits = [split.serialize() for split in splits]
        return make_response(jsonify({'splits': splits}), 200)
    
    @token_required
    def put(self, current_user):
        data = request.args
        try:
            assert 'split_id' in data.keys(), "Missing keys"
            split = Split.query.filter_by(split_id=data['split_id']).first()
            split.status = True
            db.session.commit()
            return make_response(jsonify({'message': 'Split settled!'}), 200)
        except Exception as e:
            return make_response(jsonify({'message': str(e)}), 400)
    
api.add_resource(splits, '/api/splits')

class payments(Resource):

    # Get all payments where user_id maybe current user
    @token_required
    def get(self, current_user):
        data = request.headers.get('x-access-token')
        token_data = jwt.decode(data, app.config['SECRET_KEY'], algorithms=["HS256"])
        payments = Payment.query.filter_by(user_id=token_data["public_id"]).order_by(Payment.time.desc()).all()
        payments = [payment.serialize() for payment in payments]
        return make_response(jsonify({'payments': payments}), 200)
    
    @token_required
    def post(self, current_user):
        try:
            data = request.headers.get('x-access-token')
            payer_id = jwt.decode(data, app.config['SECRET_KEY'], algorithms=["HS256"])["public_id"]
            data = request.args

            assert all(key in data.keys() for key in [
                'amount', 'description', 'date', 'splitWith', 'splitMode', 'payer']), "Missing keys"
            
            payer = data.get('payer')
            
            amount = 0 # Amount of the payment
            try: amount = int(data['amount'])
            except ValueError: amount = 1
            assert amount > 0, "Amount must be greater than 0"

            purpose = data['description'] # Purpose of the payment

            try:
                date_format = "%Y-%m-%d"
                payment_date = datetime.strptime(data['date'], date_format) # Date of the payment
            except:
                return make_response(jsonify({'message': 'Invalid date format'}), 400)

            splitMode = data['splitMode'] # Equal/ Percentage or exact amount
            assert splitMode in ["equal", "percentage", "exact"], "Invalid split mode"

            split = {} # Split for each username

            if splitMode == "equal":
                splitWith = data['splitWith'] # Users to split with usernames separated by commas (including current user)

                try: # Check for format
                    members = splitWith.split(",")
                except:
                    return make_response(jsonify({'message': 'Invalid format for splitWith'}), 400)

                for member in members: # Here 'member' contains usernames
                    member = member.strip()
                    user = User.query.filter_by(username=member).first()

                    if not user: # User existance
                        return make_response(jsonify({'message': f'User {member} does not exist!'}), 400)
                    
                    if member in split.keys(): # User already in list
                        return make_response(jsonify({'message': f'User {member} is repeated!'}), 400)
                    
                    split[member] = round(amount/len(members), 2) # Add user to split list with equal amount

            elif splitMode == "percentage":
                splitWith = data['splitWith']

                try:
                    members = eval(splitWith)
                except:
                    return make_response(jsonify({'message': 'Invalid format for splitWith'}), 400)

                total_percentage = 0

                for member, percentage in members.items():
                    user = User.query.filter_by(username=member).first()

                    if not user: # User existance
                        return make_response(jsonify({'message': f'User {member} does not exist!'}), 400)

                    if total_percentage + percentage > 100: # Correct percentage
                        return make_response(jsonify({'message': 'Total percentage must be equal to 100'}), 400)
                    
                    try:
                        calculatedAmount = amount * (float(percentage) / 100)
                    except:
                        return make_response(jsonify({'message': 'Invalid percentage'}), 400)
                
                    total_percentage += percentage
                    split[member] = round(calculatedAmount, 2) # Add user to split list with percentage amount

            elif splitMode == "exact":
                splitWith = data['splitWith']

                try:
                    members = eval(splitWith)
                except:
                    return make_response(jsonify({'message': 'Invalid format for splitWith'}), 400)

                total_amount = 0

                for member, a in members.items():
                    user = User.query.filter_by(username=member).first()

                    if not user:
                        return make_response(jsonify({'message': f'User {member} does not exist!'}), 400)
                    
                    if total_amount + a > amount and total_amount < amount: # Correct amount
                        return make_response(jsonify({'message': 'Total amount must be equal to total amount'}), 400)
                    else:
                        try:
                            a = float(a)
                        except:
                            return make_response(jsonify({'message': 'Invalid amount'}), 400)
                        
                    total_amount += a
                    split[member] = a
        
            new_payment_id = random.randint(0, 999999)
            new_payment = Payment(payment_id=new_payment_id, user_id=payer_id, amount=amount,
                                    time=payment_date, purpose=purpose, status=False)
            
            for user, amount in split.items():
                userDetails = User.query.filter_by(username=user).first()
                new_split = Split(payment_id=new_payment_id, user_id=userDetails.id, amount=amount,
                                    time=payment_date, payer_id=payer_id, status=False)
                db.session.add(new_split)
                
            db.session.add(new_payment)
            db.session.commit()

        except Exception as e:
            return make_response(jsonify({'message': str(e)}), 400)
        return make_response(jsonify({'message': 'Payment added!'}), 201)
    
    @token_required
    def delete(self, current_user):
        data = request.args
        try:
            assert all(key in data.keys() for key in ['payment_id']), "Missing keys"
            payment = Payment.query.filter_by(payment_id=data['payment_id']).first()
            splits = Split.query.filter_by(payment_id=data['payment_id']).all()
            for split in splits:
                db.session.delete(split)
            db.session.delete(payment)
            db.session.commit()
            return make_response(jsonify({'message': 'Payment deleted!'}), 200)
        except Exception as e:
            return make_response(jsonify({'message': str(e)}), 400)
    
api.add_resource(payments, '/api/payments')

class checkAuth(Resource):

    # Check if user is authenticated
    @token_required
    def get(self, current_user):
        return make_response(jsonify({'message': 'User is authenticated!'}), 200)
    
api.add_resource(checkAuth, '/api/auth')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)