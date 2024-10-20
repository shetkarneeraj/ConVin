from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, login_required, \
    UserMixin, RoleMixin, logout_user, current_user
from flask_security.utils import hash_password
from sqlalchemy import or_, func, extract, and_
import random
from datetime import datetime, date

current_year = datetime.now().year
current_month = datetime.now().month

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECURITY_PASSWORD_SALT'] = 'thisisasecretsalt'
app.config['SECURITY_POST_LOGIN_VIEW'] = '/dashboard'
app.config['SECURITY_POST_LOGOUT_VIEW'] = '/login'
app.app_context().push()

db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')))


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

class Group(db.Model):
    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    members = db.relationship('GroupMember', backref='group', lazy=True)
    payments = db.relationship('GroupPayment', backref='group', lazy=True)

    def __repr__(self):
        return f"Group('{self.group_id}', '{self.name}')"

class GroupMember(db.Model):
    member_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"GroupMember('{self.member_id}')"

class GroupPayment(db.Model):
    group_payment_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.payment_id'), nullable=False)

    def __repr__(self):
        return f"GroupPayment('{self.group_payment_id}', '{self.group_id}', '{self.payment_id}')"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    confirmed_at = db.Column(db.DateTime)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    payments = db.relationship('Payment', backref='payer', lazy=True)
    splits_received = db.relationship('Split', foreign_keys='Split.user_id', backref='user', lazy=True)
    splits_paid = db.relationship('Split', foreign_keys='Split.payer_id', backref='payer', lazy=True)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return f"User('{self.id}', '{self.name}', '{self.email}')"
    
    def __str__(self):
        return self.name
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'username': self.username
        }

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(255))

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_datastore.create_user(
            name = request.form.get('name'),
            email=request.form.get('email'),
            username=request.form.get('username'),
            active=True,
            confirmed_at = datetime.now(),
            password=hash_password(request.form.get('password'))
        )
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/search/<string:query>', methods=['GET'])
@login_required
def search(query):
    users = User.query.filter(User.name.like(f'%{query}%')).all()
    users = [user.serialize() for user in users]
    return {'users': users}

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Logs the user out
    return redirect(url_for('security.login'))  # Redirects to the login page after logout

@app.route('/payment', methods=['GET','POST'])
@login_required
def payment():
    if request.method == 'POST':
        data = request.get_json()
        amount = data['amount']
        purpose = data['description']
        date_format = "%Y-%m-%d"
        payment_date = datetime.strptime(data['date'], date_format)
        split = data['splitWith']
        new_payment_id = random.randint(0, 999999)
        print(data)
        new_payment = Payment(amount=int(amount), purpose=purpose, time=payment_date, user_id=current_user.id, payment_id=new_payment_id)
        split.pop(0)
        for user in split:
            new_split = Split(payment_id = new_payment_id, user_id=user["id"], amount=user["amount"],
                              time=payment_date, payer_id=current_user.id, status=False)
            db.session.add(new_split)
        db.session.add(new_payment)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('payment.html')

@app.route('/dashboard')
@login_required
def dashboard():
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.time.desc()).all()
    payments = [payment.serialize() for payment in payments]
    splits = Split.query.filter(
        or_(
            and_(Split.user_id == current_user.id, Split.payer_id != current_user.id),
            and_(Split.payer_id == current_user.id, Split.user_id != current_user.id)
        ),
        and_(extract('year', Split.time) == current_year, extract('month', Split.time) == current_month)
    ).order_by(Split.time.desc()).all()
    splits = [split.serialize() for split in splits][:6]  # Limit to the latest 6 splits
    debt = Split.query.filter_by(user_id=current_user.id, status=False).all()
    debt = sum([int(entity.serialize()["amount"]) for entity in debt])
    debt_owed = Split.query.filter_by(payer_id=current_user.id, status=False).all()
    debt_owed = sum([int(entity.serialize()["amount"]) for entity in debt_owed])
    expense = sum(
        [int(entity.serialize()["amount"]) for entity in Split.query.filter_by(user_id=current_user.id)
         .filter(extract('year', Split.time) == current_year)
         .filter(extract('month', Split.time) == current_month)
         .order_by(Split.time.desc())  # Order by date
         .all()]
    )
    return render_template('dashboard.html', payments=payments, splits=splits, debt=debt, debt_owed=debt_owed, expense=expense)

@app.route('/history')
@login_required
def history():
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.time.desc()).all()
    payments = [payment.serialize() for payment in payments]
    for payment in payments:
        splits = Split.query.filter_by(payment_id=payment['payment_id']).order_by(Split.time.desc()).all()
        splits = [split.serialize() for split in splits]
        payment['splits'] = splits
    splits = Split.query.filter(
        or_(Split.user_id == current_user.id, Split.payer_id == current_user.id)
    ).order_by(Split.time.desc()).all()  # Sort splits by date
    splits = [split.serialize() for split in splits]
    debt = Split.query.filter_by(user_id=current_user.id, status=False).all()
    debt = sum([int(entity.serialize()["amount"]) for entity in debt])
    debt_owed = Split.query.filter_by(payer_id=current_user.id, status=False).all()
    debt_owed = sum([int(entity.serialize()["amount"]) for entity in debt_owed])
    expense = sum(
        [int(entity.serialize()["amount"]) for entity in Split.query.filter_by(user_id=current_user.id)
         .filter(extract('year', Split.time) == current_year)
         .filter(extract('month', Split.time) == current_month)
         .order_by(Split.time.desc())  # Order by date
         .all()]
    )
    return render_template('history.html', payments=payments, splits=splits, debt=debt, debt_owed=debt_owed, expense=expense)

@app.route('/settleSplit/<int:splitId>', methods=['POST'])
@login_required
def settle_split(splitId):
    if request.method == 'POST':
        split = Split.query.filter_by(split_id=splitId).first()
        split.status = True
        db.session.commit()
        return redirect(url_for('history'))


@app.route('/analytics')
@login_required
def analytics():
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.time.desc()).all()
    payments = [payment.serialize() for payment in payments]
    splits = Split.query.filter(
        or_(Split.user_id == current_user.id, Split.payer_id == current_user.id)
    ).order_by(Split.time.desc()).all()  # Sort splits by date
    splits = [split.serialize() for split in splits][:6]  # Limit to the latest 6 splits
    debt = Split.query.filter_by(user_id=current_user.id, status=False).all()
    debt = sum([int(entity.serialize()["amount"]) for entity in debt])
    debt_owed = Split.query.filter_by(payer_id=current_user.id, status=False).all()
    debt_owed = sum([int(entity.serialize()["amount"]) for entity in debt_owed])
    expense = sum(
        [int(entity.serialize()["amount"]) for entity in Split.query.filter_by(user_id=current_user.id)
         .filter(extract('year', Split.time) == current_year)
         .filter(extract('month', Split.time) == current_month)
         .order_by(Split.time.desc())  # Order by date
         .all()]
    )
    return render_template('analytics.html', payments=payments, splits=splits, debt=debt, debt_owed=debt_owed, expense=expense)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)