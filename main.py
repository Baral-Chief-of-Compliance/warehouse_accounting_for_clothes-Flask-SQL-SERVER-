from flask import Flask, request, render_template, session, redirect, url_for
import pyodbc
from config import Config
from hash import check_password
from call_sql_quary import call


app = Flask(__name__)
app.config.from_object(Config)


@app.route('/', methods=['GET'])
def home():
    if 'loggedin' in session:
        if request.method == 'GET':

            return render_template('home.html', title='Главная', login=session['username'])

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():

    msg = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        hash_pass = call('select [pass_hash] '
                         'from [РГР_ВАДИМ].[dbo].[Operator] '
                         'where [login] = ?', [username], commit=False, fetchall=False)

        if check_password(password, hash_pass[0]):
            operator = call('select * '
                            'from [РГР_ВАДИМ].[dbo].[Operator] '
                            'where [login] = ?', [username], commit=False, fetchall=False)
            session['loggedin'] = True
            session['id'] = operator[0]
            session['username'] = operator[1]

            return redirect(url_for('home'))
        else:
            msg = 'Неправильный логин/пароль'

    return render_template('login.html', title='Вход', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)

    return redirect(url_for('login'))

@app.route('/workers', methods=['GET'])
def workers():
    if 'loggedin' in session:
        if request.method == 'GET':

            workers = call('SELECT * '
                           'FROM [РГР_ВАДИМ].[dbo].[РАБОТНИК] '
                           'INNER JOIN[РГР_ВАДИМ].[dbo].[ЦЕХ] '
                           'on [РГР_ВАДИМ].[dbo].[РАБОТНИК].[код_цеха] '
                           '= [РГР_ВАДИМ].[dbo].[ЦЕХ].[код_цеха]',
                           commit=False,
                           fetchall=True
                           )

            return render_template('workers.html', title='Работники', workers=workers)

    return redirect(url_for('login'))


@app.route('/add_worker', methods=['GET', 'POST'])
def add_worker():
    if 'loggedin' in session:
        if request.method == 'GET':

            shops = call('SELECT * FROM [РГР_ВАДИМ].[dbo].[ЦЕХ]',
                         commit=False,
                         fetchall=True
                         )

            return render_template('add_worker.html',
                                   title='Добавить работника',
                                   shops=shops
                                   )

        elif request.method == 'POST':
            shops_id = int(request.form['shop'])
            surname = request.form['surname']
            name = request.form['name']
            patronomic = request.form['patronomic']
            role = request.form['role']
            sale = request.form['sale']
            worker_code = request.form['worker_code']

            print(shops_id, surname, name, patronomic, role, sale)

            call(
                'insert into '
                '[РГР_ВАДИМ].[dbo].[РАБОТНИК] ('
                '[код_работника],'
                '[код_цеха],'
                '[фамилия_р],'
                '[имя_р],'
                '[отчество_р],'
                '[должность],'
                '[скидка_проц])'
                'values (?, ?, ?, ?, ?, ?, ?)',
                [worker_code, shops_id, surname, name, patronomic, role, sale],
                commit=True,
                fetchall=False
            )

            print(shops_id, surname, name, patronomic, role, sale)

        return render_template('worker_is_add.html',
                               title='Рабочий добавлен',
                               surname=surname,
                               name=name,
                               patronomic=patronomic,
                               role=role,
                               sale=sale,
                               worker_code=worker_code
                               )

    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
