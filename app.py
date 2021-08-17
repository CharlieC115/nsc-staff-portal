import os
from flask import (Flask, render_template, flash,
                   redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
if os.path.exists('env.py'):
    import env


app = Flask(__name__)


app.config['MONGO_DBNAME'] = os.environ.get('MONGO_DBNAME')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.secret_key = os.environ.get('SECRET_KEY')


mongo = PyMongo(app)


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/profile')
def profile():
    users = mongo.db.users.find()
    return render_template('profile.html', users=users)


@app.route('/edit_profile/<user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    if request.method == 'POST':
        # code to get all fields of the users collection minus
        # username and password
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

        user['first_name'] = request.form.get('first_name')
        user['last_name'] = request.form.get('last_name')
        user['email_address'] = request.form.get('email_address')
        user['address_line_1'] = request.form.get('address_line_1')
        user['address_line_2'] = request.form.get('address_line_2')
        user['address_city'] = request.form.get('address_city')
        user['address_post_code'] = request.form.get('address_post_code')
        user['miles_from_club'] = request.form.get('miles_from_club')

        mongo.db.users.update({'_id': ObjectId(user_id)}, user)
        flash('User successfully Updated')

    users = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return render_template('edit_profile.html', users=users)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {'username': request.form.get('username').lower()})

        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))

        register = {
            'username': request.form.get('username').lower(),
            'password': generate_password_hash(request.form.get('password')),
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email_address': request.form.get('email_address'),
            'address_line_1': request.form.get('address_line_1'),
            'address_line_2': request.form.get('address_line_2'),
            'address_city': request.form.get('address_city'),
            'address_post_code': request.form.get('address_post_code')
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session['user'] = request.form.get('username').lower()
        flash('Registration Successful!')
        return redirect(url_for('profile', username=session['user']))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {'username': request.form.get('username').lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
              existing_user['password'], request.form.get('password')):
                session['user'] = request.form.get('username').lower()
                flash('Welcome, {}'.format(
                    request.form.get('username')))
                return redirect(url_for(
                    'profile', username=session['user']))

            else:
                # invalid password match
                flash('Incorrect Username and/or Password')
                return redirect(url_for('login'))

        else:
            # username doesn't exist
            flash('Incorrect Username and/or Password')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    # remove user from session cookies
    flash('You have been logged out')
    session.pop('user')
    return redirect(url_for('login'))


@app.route('/lessons')
def lessons():
    # get the records from the lessons collection
    lessons = list(mongo.db.lessons.find().sort('datetime_millisec', 1))
    return render_template('lessons.html', lessons=lessons)


@app.route('/search', methods=['GET', 'POST'])
def search():
    # functionality for search bar
    query = request.form.get('query')
    lessons = list(mongo.db.lessons.find(
        {'$text': {'$search': query}}).sort('datetime_millisec', 1))
    return render_template('lessons.html', lessons=lessons)


@app.route('/new_record', methods=['GET', 'POST'])
def new_record():
    if request.method == 'POST':
        lesson_hours = request.form.get('lesson_hours')
        # check if switch is on or off and return yes or no
        lesson_mileage = 'Yes' if request.form.get('lesson_mileage') else 'No'
        lesson_expenses = 'Yes' if request.form.get(
            'lesson_expenses') else 'No'

        # calculate expenses using hours
        if float(lesson_hours) < 1.5:
            expense_due = 7.2
        else:
            expense_due = str(round(float(lesson_hours) * 4.8, 2))

        mileage = 5.0

        # return value only if they want expenses
        if lesson_expenses == 'Yes':
            total_expense = float(expense_due)
        else:
            total_expense = 0.0

        # return mileage only if they want mileage
        if lesson_mileage == 'Yes':
            total_mileage = mileage
        else:
            total_mileage = 0.0

        # calculate the total expense payout
        total_due = total_expense + total_mileage

        # create a full datetime
        date = request.form.get('lesson_date')
        start_time = request.form.get('lesson_start')
        full_date_time = date + ' ' + start_time

        # convert to datetime into milliseconds so this can be put in order
        dateti = datetime.strptime(full_date_time, '%d.%m.%Y %H:%M')
        millisec = dateti.timestamp()

        record = {
            'lesson_date': date,
            'lesson_start': start_time,
            'lesson_finish': request.form.get('lesson_finish'),
            'lesson_hours': lesson_hours,
            'lesson_type': request.form.get('activity_name'),
            'lesson_mileage': lesson_mileage,
            'lesson_expenses': lesson_expenses,
            'entry_by': session['user'],
            'expense_due': expense_due,
            'datetime_millisec': millisec,
            'total_due': total_due
        }

        mongo.db.lessons.insert_one(record)
        flash('Record successfully Added')
        return redirect(url_for('lessons'))

    users = mongo.db.users.find()
    activities = mongo.db.activities.find().sort('activity_name', 1)
    return render_template(
        'new_record.html', activities=activities, users=users)


@app.route('/new_record_admin', methods=['GET', 'POST'])
def new_record_admin():
    if request.method == 'POST':
        lesson_hours = request.form.get('lesson_hours')
        lesson_mileage = 'Yes' if request.form.get('lesson_mileage') else 'No'
        lesson_expenses = 'Yes' if request.form.get(
            'lesson_expenses') else 'No'

        if float(lesson_hours) < 1.5:
            expense_due = 7.2
        else:
            expense_due = str(round(float(lesson_hours) * 4.8, 2))

        mileage = 5.0

        if lesson_expenses == 'Yes':
            total_expense = float(expense_due)
        else:
            total_expense = 0.0

        if lesson_mileage == 'Yes':
            total_mileage = mileage
        else:
            total_mileage = 0.0

        total_due = total_expense + total_mileage

        date = request.form.get('lesson_date')
        start_time = request.form.get('lesson_start')
        full_date_time = date + ' ' + start_time

        dateti = datetime.strptime(full_date_time, '%d.%m.%Y %H:%M')
        millisec = dateti.timestamp()

        record = {
            'lesson_date': date,
            'lesson_start': start_time,
            'lesson_finish': request.form.get('lesson_finish'),
            'lesson_hours': lesson_hours,
            'lesson_type': request.form.get('activity_name'),
            'lesson_mileage': lesson_mileage,
            'lesson_expenses': lesson_expenses,
            'entry_by': request.form.get('user_admin_input'),
            'expense_due': expense_due,
            'datetime_millisec': millisec,
            'total_due': total_due
        }

        mongo.db.lessons.insert_one(record)
        flash('Record successfully Added')
        return redirect(url_for('lessons'))

    users = mongo.db.users.find()
    activities = mongo.db.activities.find().sort('activity_name', 1)
    return render_template(
        'new_record_admin.html', activities=activities, users=users)


@app.route('/edit_record/<lesson_id>', methods=['GET', 'POST'])
def edit_record(lesson_id):
    if request.method == 'POST':
        lesson_hours = request.form.get('lesson_hours')
        # check if switch is on or off and return yes or no
        lesson_mileage = 'Yes' if request.form.get('lesson_mileage') else 'No'
        lesson_expenses = 'Yes' if request.form.get(
            'lesson_expenses') else 'No'

        # calculate expenses using hours
        if float(lesson_hours) < 1.5:
            expense_due = 7.2
        else:
            expense_due = str(round(float(lesson_hours) * 4.8, 2))

        mileage = 5.0

        # return value only if they want expenses
        if lesson_expenses == 'Yes':
            total_expense = float(expense_due)
        else:
            total_expense = 0.0

        # return mileage only if they want mileage
        if lesson_mileage == 'Yes':
            total_mileage = mileage
        else:
            total_mileage = 0.0

        # calculate the total expense payout
        total_due = total_expense + total_mileage

        # create a full datetime
        date = request.form.get('lesson_date')
        start_time = request.form.get('lesson_start')
        full_date_time = date + ' ' + start_time

        # convert to datetime into milliseconds so this can be put in order
        dateti = datetime.strptime(full_date_time, '%d.%m.%Y %H:%M')
        millisec = dateti.timestamp()

        lesson_e = mongo.db.lessons.find_one({'_id': ObjectId(lesson_id)})

        lesson_e['lesson_date'] = date
        lesson_e['lesson_start'] = start_time
        lesson_e['lesson_finish'] = request.form.get('lesson_finish')
        lesson_e['lesson_hours'] = lesson_hours
        lesson_e['lesson_type'] = request.form.get('activity_name')
        lesson_e['lesson_mileage'] = lesson_mileage
        lesson_e['lesson_expenses'] = lesson_expenses
        lesson_e['expense_due'] = expense_due
        lesson_e['datetime_millisec'] = millisec
        lesson_e['total_due'] = total_due

        mongo.db.lessons.update({'_id': ObjectId(lesson_id)}, lesson_e)
        flash('Record successfully Updated')

    lesson = mongo.db.lessons.find_one({'_id': ObjectId(lesson_id)})
    activities = mongo.db.activities.find().sort('activity_name', 1)
    return render_template(
        'edit_record.html', lesson=lesson, activities=activities)


@app.route('/delete_record/<lesson_id>')
def delete_record(lesson_id):
    mongo.db.lessons.remove({'_id': ObjectId(lesson_id)})
    flash('Record Successfully Deleted')
    return redirect(url_for('lessons'))


@app.route('/manage_activities')
def manage_activities():

    hours = mongo.db.lessons.find({}, {'_id': 0, 'lesson_hours': 1})

    # used to calculate total hours
    hours_total = 0
    for hour in hours:
        hour_num = float(hour['lesson_hours'])
        hours_total = hours_total + hour_num

    expenses = mongo.db.lessons.find({}, {'_id': 0, 'expense_due': 1})

    # used to calculate total expenses
    expense_total = round(0, 2)
    for expense in expenses:
        expense_num = float(expense['expense_due'])
        expense_total = expense_total + expense_num

    total_expense = mongo.db.lessons.find({}, {'_id': 0, 'total_due': 1})

    # used to calculate total mileage
    overall_expenses = round(0, 2)
    for t_expense in total_expense:
        overall_expense_num = float(t_expense['total_due'])
        overall_expenses = overall_expenses + overall_expense_num

    total_mileage = round((overall_expenses - expense_total), 2)

    users = mongo.db.users.find()
    activities = list(mongo.db.activities.find().sort('activity_name', 1))
    return render_template(
        'manage_activities.html', activities=activities, users=users,
        hours_total=hours_total, expense_total=expense_total,
        total_mileage=total_mileage)


@app.route('/new_activity', methods=['GET', 'POST'])
def new_activity():
    if request.method == 'POST':
        activities = {
            'activity_name': request.form.get('activity_name')
        }
        mongo.db.activities.insert_one(activities)
        flash('New Activity Added')
        return redirect(url_for('manage_activities'))

    return render_template('new_activity.html')


@app.route('/edit_activity/<activity_id>', methods=['GET', 'POST'])
def edit_activity(activity_id):
    if request.method == 'POST':
        activities = {
            'activity_name': request.form.get('activity_name')
        }
        mongo.db.activities.update({'_id': ObjectId(activity_id)}, activities)
        flash('Activity Successfully Updated')
        return redirect(url_for('manage_activities'))

    activity = mongo.db.activities.find_one({'_id': ObjectId(activity_id)})
    return render_template('edit_activity.html', activity=activity)


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=False)
