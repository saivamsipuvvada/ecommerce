from flask import Flask,render_template,request,redirect,url_for,session,flash
import mysql.connector
from cmail import sendmail
from otp import genotp
from itemkey import genid
import stripe
stripe.api_key='sk_test_51NEwbpSGV8I6se9KORwedExAXFwLOMKImSP2IUR2kBUvA8lAhHEUXbPEuTKjPweb1V4Db1ij200j8PEx3Nsv5F2o00UtOfttxi'
import os
app=Flask(__name__)
mydb=mysql.connector.connect(
    host='localhost',
    user='root',
    password='sai1',
    db='ecommerce')
app.secret_key = 'sdsrvwsdcsdsrweefwed'
@app.route('/reg',methods=['GET','POST'])

def reg():
    if request.method=='POST':
        username=request.form['username']
        mobile=request.form['mobile']
        email=request.form['email']
        address=request.form['address']
        password=request.form['password']
        otp=genotp()
        sendmail(to=email,subject="Thanks for registration",body=f'otp is:{otp}')
        return render_template('verification.html',username=username,mobile=mobile,email=email,address=address,password=password,otp=otp)
    return render_template('register.html')
@app.route('/otp/<username>/<mobile>/<email>/<address>/<password>/<otp>',methods=['GET','POST'])
def otp(username,mobile,email,address,password,otp):
    if request.method=='POST':
        uotp=request.form['uotp']
        if otp==uotp:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into registration values(%s,%s,%s,%s,%s)',[username,mobile,email,address,password])
            mydb.commit()
            cursor.close()
            #flash('details registered')
            return redirect(url_for('login'))
    return render_template('verification.html',username=username,mobile=mobile,email=email,address=address,password=password,otp=otp)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from registration where username=%s && password=%s',[username,password])
        data=cursor.fetchone()[0]
        print(data)
        cursor.close()
        if data==1:
            session['username']=username
            if not session.get(session['username']):
                session[session['username']]={}
            return redirect(url_for('home'))
        else:
            return 'Invalid Username and password'
    return render_template('login.html')
@app.route('/',methods=['GET','POST'])
def home():
    return render_template('base.html')
@app.route('/logout')
def logout():
    if session.get('username'):
        session.pop('username')
    return redirect(url_for('login'))
@app.route('/additems',methods=['GET','POST'])
def additems():
    if session.get('admin'):
        if request.method=='POST':
            name=request.form['name']
            description=request.form['description']
            quantity=request.form['quantity']
            price=request.form['price']
            file_data=request.files['file']
            #filedata is an image
            filename=file_data.filename.split('.')
            if filename[-1]!='jpg':
                flash('please upload jpg files only')
                return render_template('additems.html')
            enum=request.form['enum']
            path=os.path.dirname(os.path.abspath(__file__))
            print(path)
            static_path=os.path.join(path,'static')
            itemid=genid()
            filename=itemid+'.jpg'
            #last .jpg included and itemid will be the filename for the img saved in static folder
            file_data.save(os.path.join(static_path,filename))
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into additems values(%s,%s,%s,%s,%s,%s)',[itemid,name,description,quantity,enum,price])
            mydb.commit()
            cursor.close()
            flash('item added succesfully')
            return render_template('additems.html')
        return render_template('additems.html')
    return redirect(url_for('adminlogin'))
@app.route('/adminreg',methods=['GET','POST'])
def adminreg():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from adminreg where username=%s',[username])
        count=cursor.fetchone()[0]
        if count!=1:
            cursor.execute('insert into adminreg values(%s,%s,%s)',[username,password,email])
            mydb.commit()
            cursor.close()
            return redirect(url_for('adminlogin'))
        else:
            return "only one admin is allowed to operate this application" 
    return render_template('admin_register.html')
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from adminreg where username=%s && password=%s',[username,password])
        data=cursor.fetchone()[0]
        print(data)
        if data == 1:
            session['admin']=username
            return redirect(url_for('admindashboard'))
        else:
            return 'Invalid Username or Password'
   
        cursor.close()
    return render_template('admin_login.html') 
@app.route('/admindashboard')
def admindashboard():
    if session.get('admin'):
        return render_template('admindashboard.html')
    else:
        return redirect(url_for('adminlogin'))
@app.route('/adminlogout')
def adminlogout():
    if session.get('admin'):
        session.pop('admin')
    return redirect(url_for('adminlogin'))
@app.route('/status')
def status():
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from additems')
        data=cursor.fetchall()
        return render_template('status.html',data=data)
    else:
        return redirect(url_for('adminlogin'))
@app.route('/update/<itemid>',methods=['GET','POST'])
def update(itemid):
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from additems where itemid=%s',[itemid])
        data=cursor.fetchone()
        cursor.close()
        print(data)
        if request.method=='POST':
            name=request.form['name']
            description=request.form['description']
            quantity=request.form['quantity']
            category=request.form['category']
            price=request.form['price']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update additems set name=%s,description=%s,quantity=%s,category=%s,price=%s \
            where itemid=%s',[name,description,quantity,category,price,itemid])
            mydb.commit()
            flash('item updated successfully')
            return redirect(url_for('status'))
        return render_template('updateproducts.html',data=data)
    else:
        return redirect(url_for('adminlogin'))
@app.route('/delete/<itemid>')
def delete(itemid):
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from additems where itemid=%s',[itemid])
        mydb.commit()
        path=os.path.dirname(os.path.abspath(__file__))
        static_path=os.path.join(path,'static')
        os.remove(os.path.join(static_path,itemid+'.jpg'))
        flash('items deleted sucessfully')
        return redirect(url_for('status'))
    else:
        return redirect(url_for('adminlogin'))
@app.route('/category/<category>',methods=['GET','POST'])
def category(category):
    if session.get('username'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from additems where category=%s',[category])
        data=cursor.fetchall()
        cursor.close()
        return render_template('items.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/item/<itemid>',methods=['GET','POST'])
def detail(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select *   from additems where itemid=%s',[itemid])
    items=cursor.fetchone()
    cursor.close()
    return render_template('detailedview.html',items=items)
@app.route('/cart/<itemid>/<name>/<int:price>',methods=["POST"])
def cart(itemid,name,price):
    if session.get('username'):
        quantity=int(request.form['quantity'])
        if itemid not in session.get(session.get('username')):
            session[session.get('username')][itemid]=[name,quantity,price]
            session.modified=True
            flash(f'{name} added to cart')
            return redirect(url_for('cartview'))
        else:
            session[session.get('username')][itemid][1]+=quantity
            flash(f'Quantity increases to +{quantity}')
            return redirect(url_for('cartview'))
    else:
        return redirect(url_for('login'))
@app.route('/viewcart')
def cartview():
    if session.get('username'):
        items=session.get(session.get('username')) if session.get(session.get('username')) else 'empty'   
        print(items)     
        return render_template('cartview.html',items=items)
    else:
        return redirect(url_for('login'))
@app.route('/cartpop/<itemid>')
def cartpop(itemid):
    if session.get('username'):
        session[session.get('username')].pop(itemid)
        session.modified=True
        flash('item removed')
        return redirect(url_for('cartview'))
    else:
        return redirect(url_for('login'))
@app.route('/pay/<itemid>/<name>/<int:price>',methods=['POST'])
def pay(itemid,price,name):
    if session.get('username'):
        q=int(request.form['quantity'])
        username=session.get('user')
        total=price*q
        checkout_session=stripe.checkout.Session.create(
            success_url=url_for('success',itemid=itemid,name=name,q=q,total=total,_external=True),
            line_items=[
                {
                    'price_data': {
                        'product_data': {
                            'name': name,
                        },
                        'unit_amount': price*100,
                        'currency': 'inr',
                    },
                    'quantity': q,
                },
                ],
            mode="payment",)
        return redirect(checkout_session.url)
    else:
        return redirect(url_for('login'))
@app.route('/success/<itemid>/<name>/<q>/<total>')
def success(itemid,name,q,total):
    if session.get('username'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,itemname,q,total,username)values(%s,%s,%s,%s,%s)',[itemid,name,q,total,session.get('username')])
        mydb.commit()
        cursor.close()
        return redirect(url_for('orderplaced'))
    else:
        return redirect(url_for('login'))
@app.route('/orderplaced')
def orderplaced():
    return render_template('orderplaced.html')
@app.route('/orders')
def orders():
    if session.get('username'):
        username=session.get('username')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from orders where username=%s',[username])
        data=cursor.fetchall()
        cursor.close()
        return render_template('orderdisplay.html',data=data)
    else:
        return redirect(url_for('login'))        



app.run(debug=True,use_reloader=True)