import os

from flask import Flask, render_template, url_for, redirect, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Length, ValidationError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(12).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wishlist.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    gifts = db.relationship('Gift', backref='author', lazy=True)


class Gift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reserved_by = db.Column(db.String(100), nullable=True)
    comments = db.Column(db.String(200), nullable=True)


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Этот ник уже использован. Пожалуйста выбери другой.')


class GiftForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    link = StringField('Ссылка', validators=[DataRequired()])
    price = DecimalField('Цена', validators=[DataRequired()])
    submit = SubmitField('Добавить подарок')


class ReservationForm(FlaskForm):
    name = StringField('Ваше Имя (можно написать Аноним)', validators=[DataRequired()])
    comments = TextAreaField('Комментарий')
    submit = SubmitField('Зарезервировать')


@app.route('/')
def home():
    gifts = Gift.query.all()
    return render_template('home.html', gifts=gifts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('add_gift'))
        else:
            flash('Войти не удалось. Пожалуйста, проверь имя и пароль.', 'danger')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Аккаунт создан успешно. Теперь ты можешь войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/add_gift', methods=['GET', 'POST'])
@login_required
def add_gift():
    form = GiftForm()
    if form.validate_on_submit():
        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        gift = Gift(title=form.title.data, description=form.description.data, link=form.link.data,
                    price=form.price.data, image=filename, created_by=current_user.id)
        db.session.add(gift)
        db.session.commit()
        flash('Подарок добавлен успешно!', 'success')
        return redirect(url_for('home'))
    return render_template('add_gift.html', form=form)


@app.route('/gift/<int:gift_id>', methods=['GET', 'POST'])
def reserve_gift(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    if gift.reserved_by:
        flash('Этот подарок уже был зарезервирован.', 'warning')
        return redirect(url_for('home'))
    form = ReservationForm()
    if form.validate_on_submit():
        gift.reserved_by = form.name.data
        gift.comments = form.comments.data
        db.session.commit()
        flash('Подарок зарезервирован успешно!', 'success')
        return redirect(url_for('home'))
    return render_template('reserve_gift.html', gift=gift, form=form)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == '__main__':
    app.run(debug=True)
