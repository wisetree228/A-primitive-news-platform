from flask import Flask, render_template, url_for, request, flash, get_flashed_messages, redirect, session, send_file, make_response
from sqlite3 import *
import base64



app=Flask(__name__)

app.secret_key='key123456789'


#массив адресов ссылок (потом я заменил их функцией url_for())
urls=[
    {"name":"Добавить запись", "url":"/add"},
    {"name":"динамический просмотр", "url":"/view/<int:id>"}
]


# ассоциативный массив с данными о входе пользователя и его юзернеймом
data={
    'userLogged':False,
    'userName':'',
}


# вспомогательные функции для работы с базой данных в коде
def selectAllWithCondition(table, cond):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {cond};")
    db.commit()
    list = cur.fetchall()
    db.close()
    return list


def selectOne(table, cond):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {cond};")
    db.commit()
    list = cur.fetchone()
    db.close()
    return list

def selectAll(table):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM {table};")
    db.commit()
    list = cur.fetchall()
    db.close()
    return list

def drop(table, cond):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"DELETE FROM {table} WHERE {cond};")
    db.commit()
    db.close()

def check_id(table, cond):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {cond};")
    db.commit()
    list = cur.fetchall()
    db.close()
    if len(list)>=1:
        return True
    return False



 # обработчик страницы входа
@app.route('/login',  methods=['POST', 'GET'])
def login():
     # вход в существующий аккаунт
    if request.method=='POST':
        if len(request.form['username'])>3 and len(request.form['password'])>5:  # проверка
            username=request.form['username']
            passw=request.form['password']

            if not check_id('user', f"username='{username}'"):  # нет такой записи
                flash('Учётной записи с таким именем нет, проведите регистрацию')
            else:
                user=selectOne('user', f"username='{username}'")
                if user[1]==username and user[2]==passw:#успешная регистрация
                    data['userLogged']=True
                    data['userName']=username
                    return redirect('/')
                else:# неверный пароль
                    flash('Неверный пароль, повторите попытку')

        else:
            flash('юзернейм должен быть длиннее 3 символов, а пароль - длиннее 5!')


    return render_template('log.html')




 # обработчик страницы регистрации

@app.route("/register", methods=['POST', 'GET'])
def register():

    if request.method=='POST':
        if (len(request.form['username'])>3 and len(request.form['password'])>5) and not("'" in request.form['username'] or "'" in request.form['password']):  # проверка на длинну пароля, имени и запрещенного символа
            username=request.form['username']
            passw=request.form['password']

            if check_id('user', f"username='{username}'"):
                flash('Аккаунт с таким именем уже существует! Попробуйте другое')
            else:  # успешная регистрация
                db = connect('database.db')
                cur = db.cursor()
                cur.execute("INSERT INTO user (username, password) VALUES (?, ?);", (username, passw))
                db.commit()
                db.close()
                data['userLogged'] = True
                data['userName'] = username
                return redirect('/')


        else:  # некорректные данные
            flash('юзернейм должен быть длиннее 3 символов, а пароль - длиннее 5, также запрещено использовать одинарную кавычку в данных с целью защиты от sql иньекций')

    return render_template('register.html')





@app.route("/")  # обработчик главной страницы
def index():

    articles=selectAll('article')


    return render_template('index.html', title="news", urls=urls, articles=articles, data=data)

@app.route("/add", methods=['POST', 'GET'])  # обработчик страницы добавления статей
def add():
    if not data['userLogged']:  # проверка входа в аккаунт
        return redirect('/')

    if request.method=='POST':  # добавление

        if len(request.form['header']) > 3 and len(request.form['text'])>10:


            db = connect('database.db')
            cur = db.cursor()
            cur.execute(f"INSERT INTO article (name, text, author) VALUES (?, ?, ?);", (request.form['header'], request.form['text'], data['userName']))
            db.commit()
            db.close()

            flash(f"все ок, статья {request.form['header']} добавлена")
        else:
            flash('ошибка, некорректные данные')


    return render_template('add.html', data=data)


@app.route("/view/<int:id>")  # обработчик динамического просмотра страницы
def detailview(id):
    if not check_id('article', f"id={id}"): # если нет такой статьи, перенос на страницу ошибки 404
        return redirect('error')



    article=selectOne('article', f"id={id}")
    auth=article[3]
    comments=selectAllWithCondition('comment', f"new_id={id}")
    leng=len(comments)

    return render_template('detailview.html', article=article, data=data, comments=comments, leng=leng, auth=auth)

@app.route("/delete/<int:id>")  # обработчик удаления
def delete(id):
    if not check_id('article', f"id={id}"): # если нет такой статьи, перенос на страницу ошибки 404
        return redirect('error')
    auth = selectOne('article', f"id={id}")[3]
    if not data['userLogged']:
        return redirect('/')
    elif data['userName']!=auth:  # нельзя удалять чужую статью
        return redirect('/')
    else:
        drop('article', f"id={id}")
        return redirect("/")

@app.route("/update/<int:id>", methods=['POST', 'GET'])  # обработчик редактирования статей
def update(id):
    if not check_id('article', f"id={id}"):  # если нет такой статьи, перенос на страницу ошибки 404
        return redirect('error')
    auth=selectOne('article', f"id={id}")[3]
    if not data['userLogged']:
        return redirect('/')
    elif data['userName']!=auth:   # нельзя редактировать чужую статью
        return redirect('/')
    else:

        article=selectOne('article', f"author='{data['userName']}'")

        db = connect('database.db')
        cur = db.cursor()
        cur.execute(f"SELECT * FROM article WHERE id={id};")
        db.commit()
        article = cur.fetchone()
        db.close()
        if request.method == 'POST':

            if len(request.form['header']) > 3 and len(request.form['text']) > 10:

                db = connect('database.db')
                cur = db.cursor()
                cur.execute(f"UPDATE article SET name='{request.form['header']}', text='{request.form['text']}' WHERE id={id};")
                db.commit()
                db.close()

                flash(f"все ок, статья '{request.form['header']}' обновлена")
            else:
                flash('ошибка, некорректные данные')

    return render_template('update.html', article=article, data=data)



@app.route('/logout')  # обработчик выхода из аккаунта
def logout():
    data['userLogged']=False
    data['userName']=''
    return redirect('/')




@app.errorhandler(404)  # обработчик неверного URL 
def pagenotfound(error):
    return render_template('error.html')


def check_user_image(username):  # вспомогательная функция для проверки наличия картинки профиля
    conn = connect('database.db')
    cursor = conn.cursor()

    
    cursor.execute(f"SELECT * FROM user WHERE username = '{username}' AND image IS NOT NULL")
    result = cursor.fetchall()

    conn.close()

    if len(result)==0:
        return False
    else:
        return True




@app.route('/profile', methods=['POST', 'GET'])  # обработчик страницы профиля
def profile():
    if not data['userLogged']:
        return redirect(url_for('login'))
    articles=selectAllWithCondition('article', f"author='{data['userName']}'")
    leng=len(articles)
    if request.method=='POST':
        db = connect('database.db')
        cur = db.cursor()

        
        image_file = request.files['image']

        
        if image_file:
            # Преобразование картинки профиля в BLOB
            image_data = image_file.read()

            # Сохранить изображение в базе данных
            cur.execute("UPDATE user SET image = ? WHERE username = ?", (image_data, data['userName']))
            db.commit()

        db.close()


    if check_user_image(data['userName']):
        user = selectOne('user', f"username='{data['userName']}'")
        db = connect('database.db')
        cur = db.cursor()
        cur.execute("SELECT image FROM user WHERE username = ?", (data['userName'],))
        image_data = cur.fetchone()[0]
        db.close()

        # Декодирование и преобразование данных изображения в base64
        img_data_base64 = base64.b64encode(image_data).decode('utf-8')
        return render_template('profile.html', data=data, articles=articles, leng=leng, img=img_data_base64)
    else:
        return render_template('profile.html', data=data, articles=articles, leng=leng, img=None)

@app.route('/addcomment/<int:id>', methods=['POST', 'GET']) # добавление комментария к статье
def add_comment(id):
    if not data['userLogged']:
        return redirect(url_for('login'))
    if not check_id('article', f"id={id}"):
        return redirect('error')
    if request.method=='POST':
        text=request.form['text']
        if len(text)<5 or len(text)>5000 or "'" in text:
            flash('комментарий должен быть больше 5 и не больше 5000 символов! запрещено использовать одинарную кавычку в целях защиты от sql иньекций!')
        else:
            db = connect('database.db')
            cur = db.cursor()
            cur.execute(f"INSERT INTO comment (new_id, author, text) VALUES (?, ?, ?);", (id, data['userName'], text))
            db.commit()
            db.close()
            flash("комментарий добавлен!")






    return render_template('addcomment.html', data=data, id=id)


@app.route('/deletecom/<int:id>') # удаление комментария
def delcom(id):
    if not check_id('comment', f"id={id}"):  # если нет такого комментария, перенос на страницу ошибки 404
        return redirect('error')
    auth = selectOne('comment', f"id={id}")[2]
    if not data['userLogged']:
        return redirect('/')
    elif data['userName'] != auth:  # нельзя удалять чужой комментарий
        art_id=selectOne('comment', f"id={id}")[1]
        return redirect(url_for('detailview', id=art_id))
    else:
        art_id = selectOne('comment', f"id={id}")[1]
        drop('comment', f"id={id}")
        return redirect(url_for('detailview', id=art_id))



@app.route('/updatecom/<int:id>', methods=['GET', 'POST']) # редактирования комментария
def updcom(id):
    text = selectOne('comment', f"id={id}")[3]
    if not check_id('comment', f"id={id}"):  # если нет такого комментария, перенос на страницу ошибки 404
        return redirect('error')
    auth = selectOne('comment', f"id={id}")[2]
    if not data['userLogged']:
        return redirect('/')
    elif data['userName'] != auth:  # нельзя редактировать чужой комментарий
        art_id = selectOne('comment', f"id={id}")[1]
        return redirect(url_for('detailview', id=art_id))

    else:
        if request.method=='POST':

            if len(text) < 5 or len(text) > 5000 or "'" in text:
                flash('комментарий должен быть больше 5 и не больше 5000 символов! запрещено использовать одинарную кавычку в целях защиты от sql иньекций!')
            else:
                db = connect('database.db')
                cur = db.cursor()
                cur.execute(f"UPDATE comment SET text='{request.form['text']}' WHERE id={id};")
                db.commit()
                db.close()
                flash("комментарий обновлён!")


    art_id=selectOne('comment', f"id={id}")[1]
    return render_template('upcom.html', text=text, data=data, id=art_id)


@app.route('/uploadimg/<username>') # скачивание фото профиля
def uploadimg(username):

    image_data = selectOne('user', f"username='{username}'")[3]
    if image_data:
        response = make_response(image_data)
        response.headers['Content-Type'] = 'image/jpeg'
        response.headers['Content-Disposition'] = 'attachment; filename=image.jpg'
        return response
    else:
        flash('у данного пользователя нет картинки профиля')
        return redirect(url_for('otherprof', username=username))



@app.route('/otherprof/<username>')
def otherprof(username):
    if data['userName']==username:
        return redirect(url_for('profile'))
    if not check_id('user', f"username='{username}'"):
        return redirect('error')
    articles = selectAllWithCondition('article', f"author='{username}'")
    leng = len(articles)

    if check_user_image(username):
        user = selectOne('user', f"username='{username}'")
        db = connect('database.db')
        cur = db.cursor()
        cur.execute("SELECT image FROM user WHERE username = ?", (username,))
        image_data = cur.fetchone()[0]
        db.close()

        # Декодирование и преобразование данных изображения в base64
        img_data_base64 = base64.b64encode(image_data).decode('utf-8')
        return render_template('oprofile.html', data=data, articles=articles, leng=leng, img=img_data_base64, username=username)
    else:
        return render_template('oprofile.html', data=data, articles=articles, leng=leng, img=None, username=username)

if __name__=="__main__":
    app.run(debug=True)
