from flask import Flask
from flask import request
from flask import redirect # 重定向
from flask import abort # 处理错误
from flask import render_template
from flask import session
from flask import url_for
from flask import flash
import os



# 表单库导入
from flask.ext.wtf import Form
from wtforms import StringField,SubmitField
from wtforms.validators import Required

# 初始化
app=Flask(__name__)
app.config['SECRET_KEY']='hard to guess string'

# bootstrap
from flask.ext.bootstrap import Bootstrap
bootstrap=Bootstrap(app)

# 数据库初始化
from flask.ext.sqlalchemy import SQLAlchemy
basedir=os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI']=\
    'sqlite:///'+os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True
db=SQLAlchemy(app)

# 定义数据模型
class Role(db.Model):
    __tablename__='roles' #数据库使用的表名
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    users=db.relationship('User',backref='role') #关系
    def __repr__(self):
        return '<Role %r>'%self.name

class User(db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(64),unique=True,index=True)
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))#关系
    def __repr__(self):
        return '<User %r>'%self.username
# 定义表单类
class NameForm(Form):
    name=StringField('what is your name?',validators=[Required()])
    submit=SubmitField('Submit')
# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'),500

# 路由
@app.route('/',methods=['GET','POST'])
def index():
    form=NameForm()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.name.data).first()
        if user is None:
            user=User(username=form.name.data)
            db.session.add(user)
            session['known']=False
        else:
            session['known']=True
        session['name']=form.name.data
        form.name.data=''
        return redirect(url_for('index'))
    return render_template('index.html',
    form=form,
    name=session.get('name'),
    known=session.get('known',False))
if __name__=='__main__':
    app.run(debug=True)