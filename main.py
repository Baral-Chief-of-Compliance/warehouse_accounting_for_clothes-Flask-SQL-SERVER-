from flask import Flask, request, render_template, session, redirect, url_for
import pyodbc
from config import Config
from hash import check_password
from dotenv import load_dotenv
from flask_mysqldb import MySQL
import MySQLdb.cursors


load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)


def call(quarry, *args, commit, fetchall):

    cur = mysql.connection.cursor()

    cur.execute(quarry, *args)

    if commit:
        cur.close()

        mysql.connection.commit()

        result_of_procedure = None

    else:

        if fetchall:
            result_of_procedure = cur.fetchall()
            cur.close()
        else:
            result_of_procedure = cur.fetchone()
            cur.close()

    return result_of_procedure


@app.route('/', methods=['GET'])
def home():
    if 'loggedin' in session:
        if request.method == 'GET':

            return render_template('home.html',
                                   title='Главная',
                                   login=session['username'])

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():

    msg = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        hash_pass = call('select pass_hash '
                         'from Operator '
                         'where login = %s', [username], commit=False, fetchall=False)

        print(hash_pass)

        if check_password(password, hash_pass[0]):
            operator = call('select * '
                            'from Operator '
                            'where login = %s', [username], commit=False, fetchall=False)
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
                           'FROM РАБОТНИК '
                           'INNER JOIN ЦЕХ '
                           'on РАБОТНИК.код_цеха '
                           '= ЦЕХ.код_цеха',
                           commit=False,
                           fetchall=True
                           )

            return render_template('workers.html',
                                   title='Работники',
                                   workers=workers,
                                   login=session['username'])

    return redirect(url_for('login'))


@app.route('/add_worker', methods=['GET', 'POST'])
def add_worker():
    if 'loggedin' in session:
        if request.method == 'GET':

            shops = call('SELECT * FROM ЦЕХ',
                         commit=False,
                         fetchall=True
                         )

            return render_template('add_worker.html',
                                   title='Добавить работника',
                                   shops=shops,
                                   login=session['username']
                                   )

        elif request.method == 'POST':
            shops_id = int(request.form['shop'])
            surname = request.form['surname']
            name = request.form['name']
            patronomic = request.form['patronomic']
            role = request.form['role']
            sale = request.form['sale']
            worker_code = call('select max(РАБОТНИК.код_работника) from РАБОТНИК', commit=False, fetchall=False)
            print(worker_code[0]+1)

            print(shops_id, surname, name, patronomic, role, sale)

            call(
                'insert into '
                'РАБОТНИК ('
                'РАБОТНИК.код_работника,'
                'РАБОТНИК.код_цеха,'
                'РАБОТНИК.фамилия_р,'
                'РАБОТНИК.имя_р,'
                'РАБОТНИК.отчество_р,'
                'РАБОТНИК.должность,'
                'РАБОТНИК.скидка_проц)'
                'values (%s, %s, %s, %s, %s, %s, %s)',
                [worker_code[0]+1, shops_id, surname, name, patronomic, role, sale],
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
                               worker_code=worker_code[0]+1,
                               login=session['username']
                               )

    return redirect(url_for('login'))


@app.route('/issuance_information', methods=['GET'])
def issuance_information():
    if 'loggedin' in session:
        if request.method == 'GET':
            inf = call('select СПЕЦОДЕЖДА.вид, СПЕЦОДЕЖДА.срок_носки_дни, СПЕЦОДЕЖДА.стоимость, КОМПЛЕКТ.код_одежды, СКЛАД.дата_получения, РАБОТНИК.код_работника, РАБОТНИК.фамилия_р, РАБОТНИК.имя_р, РАБОТНИК.отчество_р, РАБОТНИК.должность from СПЕЦОДЕЖДА inner join КОМПЛЕКТ on СПЕЦОДЕЖДА.код_одежды = КОМПЛЕКТ.код_одежды inner join СКЛАД on КОМПЛЕКТ.код_получения = СКЛАД.код_получения inner join РАБОТНИК on  СКЛАД.код_работника = РАБОТНИК.код_работника order by СКЛАД.дата_получения desc',
                commit=False,
                fetchall=True
            )

            return render_template('issuance_information.html',
                                   title='Информация о выдаче',
                                   inf=inf,
                                   login=session['username']
                                   )

    return redirect(url_for('login'))


@app.route('/add_extradition', methods=['GET', 'POST'])
def add_extradition():
    if 'loggedin' in session:
        if request.method == 'GET':

            workers = call('SELECT * '
                           'FROM РАБОТНИК '
                           'INNER JOIN ЦЕХ '
                           'on РАБОТНИК.код_цеха '
                           '= ЦЕХ.код_цеха',
                           commit=False,
                           fetchall=True
                           )

            clothes = call('select * from СПЕЦОДЕЖДА',
                           commit=False,
                           fetchall=True
                           )

            return render_template('add_extradition.html',
                                   title='Организовать выдачу',
                                   workers=workers,
                                   clothes=clothes,
                                   login=session['username']
                                   )

        elif request.method == 'POST':
            worker_id = request.form['worker']
            clothes_id = request.form.getlist('clothe')
            date = request.form['date']

            code = call('select count(*) from склад', commit=False, fetchall=False)
            code_count = int(code[0])+1

            if len(str(code_count)) == 1:
                code_count = f'0{code_count}'

            code_receiving = f'{code_count}-{str(date)[2]}{str(date)[3]}'
            print(worker_id, clothes_id, date, code_receiving)

            call('insert into'
                 ' СКЛАД ('
                 'код_получения,'
                 'код_работника,'
                 'дата_получения)'
                 'values (%s, %s, %s)',
                 [code_receiving, worker_id, date],
                 commit=True,
                 fetchall=False
                 )

            for cl in clothes_id:
                call('insert into'
                     ' КОМПЛЕКТ ('
                     'код_получения,'
                     'код_одежды)'
                     'values (%s, %s)',
                     [code_receiving, int(cl)],
                     commit=True,
                     fetchall=False
                     )

            return render_template('inf_about_add.html',
                                   title='Информация была добавлена',
                                   code_receiving=code_receiving,
                                   date=date,
                                   login=session['username']
                                   )

    return redirect(url_for('login'))


@app.route('/workshops', methods=['GET', 'POST'])
def workshops():
    if 'loggedin' in session:
        if request.method == 'GET':

            map_worksops = []

            workshops = call('SELECT код_цеха, название '
                 'FROM ЦЕХ',
                 commit=False,
                 fetchall=True)

            for w in workshops:
                humans = call('select count(РАБОТНИК.код_цеха) from '
                              'РАБОТНИК where '
                              'РАБОТНИК.код_цеха = %s',
                              [w[0]], commit=False, fetchall=False)

                map_worksops.append({
                    'id': w[0],
                    'name': w[1],
                    'humans': humans[0]
                })

            return render_template('workshops.html', title='Цехи',
                                   workshops=map_worksops,
                                   login=session['username'])


    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
