from flask import Flask, render_template, url_for, request, flash, get_flashed_messages, redirect, session, send_file, make_response, session
from sqlite3 import *
import base64



app=Flask(__name__)

app.secret_key='key123456789'


#массив адресов ссылок (потом я заменил их функцией url_for())
urls=[
    {"name":"Добавить запись", "url":"/add"},
    {"name":"динамический просмотр", "url":"/view/<int:id>"}
]





# functions for work with database
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



 # login page handler
@app.route('/login',  methods=['POST', 'GET'])
def login():
     # sign in
    if request.method=='POST':
        if len(request.form['username'])>3 and len(request.form['password'])>5:  # check length
            username=request.form['username']
            passw=request.form['password']

            if not check_id('user', f"username='{username}'"):  # does that account exist?
                flash("That account doesn't exist!" )
            else:
                user=selectOne('user', f"username='{username}'")
                if user[1]==username and user[2]==passw:  # ok log in your account
                    session['userLogged']=True
                    session['userName']=username
                    return redirect('/')
                else:# incorrect assword
                    flash('Incorrect password!')

        else:
            flash('The username must be longer than 3 characters, and the password must be longer than 5!')


    return render_template('log.html')




 # registration page handler

@app.route("/register", methods=['POST', 'GET'])
def register():

    if request.method=='POST':
        if (len(request.form['username'])>3 and len(request.form['password'])>5) and not("'" in request.form['username'] or "'" in request.form['password']):  # checking for length and forbidden symbols
            username=request.form['username']
            passw=request.form['password']

            if check_id('user', f"username='{username}'"): #if that account exist
                flash('That account already exists!')
            else:  # успешная регистрация
                db = connect('database.db')
                cur = db.cursor()
                cur.execute("INSERT INTO user (username, password) VALUES (?, ?);", (username, passw))
                db.commit()
                db.close()
                session['userLogged'] = True
                session['userName'] = username
                return redirect('/')


        else:  # incorrect data
            flash("The username must be longer than 3 characters, and the password must be longer than 5, it is also prohibited to use ' to protect against sql injections")

    return render_template('register.html')





@app.route("/")  # main page handler
def index():

    articles=selectAll('article')


    return render_template('index.html', title="news", urls=urls, articles=articles, session=session)

@app.route("/add", methods=['POST', 'GET'])  # handler for adding articles page
def add():
    if not session['userLogged']:  # account login verification
        return redirect('/')

    if request.method=='POST':  # add

        if len(request.form['header']) > 3 and len(request.form['text'])>10: #checking for correct data


            db = connect('database.db')
            cur = db.cursor()
            cur.execute(f"INSERT INTO article (name, text, author) VALUES (?, ?, ?);", (request.form['header'], request.form['text'], session['userName']))
            db.commit()
            db.close()

            flash(f"Article '{request.form['header']}' is added!")
        else:
            flash('Error, incorrect data')


    return render_template('add.html', session=session)


@app.route("/view/<int:id>")  # dynamic page view handler
def detailview(id):
    if not check_id('article', f"id={id}"): # if there is no such article, transfer to the 404 error page
        return redirect('error')



    article=selectOne('article', f"id={id}")
    auth=article[3]
    comments=selectAllWithCondition('comment', f"new_id={id}")
    leng=len(comments)

    return render_template('detailview.html', article=article, session=session, comments=comments, leng=leng, auth=auth)

@app.route("/delete/<int:id>")  # deleting handler
def delete(id):
    if not check_id('article', f"id={id}"): # if there is no such article, transfer to the 404 error page
        return redirect('error')
    auth = selectOne('article', f"id={id}")[3]
    if not session['userLogged']:
        return redirect('/')
    elif session['userName']!=auth:  # You can't delete someone else's article
        return redirect('/')
    else:
        drop('article', f"id={id}")
        drop('comment', f"new_id={id}")
        return redirect("/")

@app.route("/update/<int:id>", methods=['POST', 'GET'])  # article editing handler
def update(id):
    if not check_id('article', f"id={id}"):  # if there is no such article, transfer to the 404 error page
        return redirect('error')
    auth=selectOne('article', f"id={id}")[3]
    if not session['userLogged']:
        return redirect('/')
    elif session['userName']!=auth:   # You can't edit someone else's article
        return redirect('/')
    else:

        #article=selectOne('article', f"author='{session['userName']}'")

        db = connect('database.db')
        cur = db.cursor()
        cur.execute(f"SELECT * FROM article WHERE id={id};")
        db.commit()
        article = cur.fetchone()
        db.close()
        if request.method == 'POST':

            if len(request.form['header']) > 3 and len(request.form['text']) > 10:#checking for correct data

                db = connect('database.db')
                cur = db.cursor()
                cur.execute(f"UPDATE article SET name='{request.form['header']}', text='{request.form['text']}' WHERE id={id};")
                db.commit()
                db.close()

                flash(f"Ok, article '{request.form['header']}' edited!")
            else:
                flash('error, incorrect data')

    return render_template('update.html', article=article, session=session)



@app.route('/logout')  # logout handler
def logout():
    session['userLogged']=False
    session['userName']=''
    return redirect('/')




@app.errorhandler(404)  # invalid URL handler
def pagenotfound(error):
    return render_template('error.html')


def check_user_image(username):  # helper function for checking the presence of a profile picture
    conn = connect('database.db')
    cursor = conn.cursor()

    
    cursor.execute(f"SELECT * FROM user WHERE username = '{username}' AND image IS NOT NULL")
    result = cursor.fetchall()

    conn.close()

    if len(result)==0:
        return False
    return True




@app.route('/profile', methods=['POST', 'GET'])  # profile page handler
def profile():
    if not session['userLogged']:
        return redirect(url_for('login'))
    articles=selectAllWithCondition('article', f"author='{session['userName']}'")
    leng=len(articles)
    if request.method=='POST':
        db = connect('database.db')
        cur = db.cursor()

        
        image_file = request.files['image']

        
        if image_file:
            # Converting a profile picture to a BLOB
            image_data = image_file.read()

            # Save image to database
            cur.execute("UPDATE user SET image = ? WHERE username = ?", (image_data, session['userName']))
            db.commit()

        db.close()


    if check_user_image(session['userName']):
        user = selectOne('user', f"username='{session['userName']}'")
        db = connect('database.db')
        cur = db.cursor()
        cur.execute("SELECT image FROM user WHERE username = ?", (session['userName'],))
        image_data = cur.fetchone()[0]
        db.close()

        # Decoding and converting image data to base64
        img_data_base64 = base64.b64encode(image_data).decode('utf-8')
        return render_template('profile.html', session=session, articles=articles, leng=leng, img=img_data_base64)
    else:
        return render_template('profile.html', session=session, articles=articles, leng=leng, img=None)

@app.route('/addcomment/<int:id>', methods=['POST', 'GET']) # adding a comment to an article
def add_comment(id):
    if not session['userLogged']:
        return redirect(url_for('login'))
    if not check_id('article', f"id={id}"):
        return redirect('error')
    if request.method=='POST':
        text=request.form['text']
        if len(text)<5 or len(text)>5000 or "'" in text:
            flash("The comment must be more than 5 and no more than 5000 characters! It is forbidden to use ' in order to protect against sql injections!")
        else:
            db = connect('database.db')
            cur = db.cursor()
            cur.execute(f"INSERT INTO comment (new_id, author, text) VALUES (?, ?, ?);", (id, session['userName'], text))
            db.commit()
            db.close()
            flash("comment is added!!")






    return render_template('addcomment.html', session=session, id=id)


@app.route('/deletecom/<int:id>') # deleting a comment
def delcom(id):
    if not check_id('comment', f"id={id}"):  # if there is no such comment, transfer to the 404 error page
        return redirect('error')
    auth = selectOne('comment', f"id={id}")[2]
    if not session['userLogged']:
        return redirect('/')
    elif session['userName'] != auth:  # You can't delete someone else's comment
        art_id=selectOne('comment', f"id={id}")[1]
        return redirect(url_for('detailview', id=art_id))
    else:
        art_id = selectOne('comment', f"id={id}")[1]
        drop('comment', f"id={id}")
        return redirect(url_for('detailview', id=art_id))



@app.route('/updatecom/<int:id>', methods=['GET', 'POST']) # editing a comment
def updcom(id):
    text = selectOne('comment', f"id={id}")[3]
    if not check_id('comment', f"id={id}"):  # if there is no such comment, transfer to the 404 error page
        return redirect('error')
    auth = selectOne('comment', f"id={id}")[2]
    if not session['userLogged']:
        return redirect('/')
    elif session['userName'] != auth:  # You can't edit someone else's comment
        art_id = selectOne('comment', f"id={id}")[1]
        return redirect(url_for('detailview', id=art_id))

    else:
        if request.method=='POST':

            if len(text) < 5 or len(text) > 5000 or "'" in text:#checking for correct data!
                flash("The comment must be more than 5 and no more than 5000 characters! It is forbidden to use ' in order to protect against sql injections!")
            else:
                db = connect('database.db')
                cur = db.cursor()
                cur.execute(f"UPDATE comment SET text='{request.form['text']}' WHERE id={id};")
                db.commit()
                db.close()
                flash("the comment is edited!")


    art_id=selectOne('comment', f"id={id}")[1]
    return render_template('upcom.html', text=text, session=session, id=art_id)


@app.route('/uploadimg/<username>') # download profile photo
def uploadimg(username):

    image_data = selectOne('user', f"username='{username}'")[3]
    if image_data:
        response = make_response(image_data)
        response.headers['Content-Type'] = 'image/jpeg'
        response.headers['Content-Disposition'] = 'attachment; filename=image.jpg'
        return response
    else:
        flash('This user does not have a profile picture')
        return redirect(url_for('otherprof', username=username))



@app.route('/otherprof/<username>') # someone else's profile page
def otherprof(username):
    if session['userName']==username:
        return redirect(url_for('profile'))
    if not check_id('user', f"username='{username}'"): #if that user doesn't exist
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


        img_data_base64 = base64.b64encode(image_data).decode('utf-8')
        return render_template('oprofile.html', session=session, articles=articles, leng=leng, img=img_data_base64, username=username)
    else:
        return render_template('oprofile.html', session=session, articles=articles, leng=leng, img=None, username=username)






if __name__=="__main__":
    app.run(debug=True)
