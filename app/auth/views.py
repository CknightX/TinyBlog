from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required
from . import auth
from .. import db
from ..models import User
from ..email import send_email
from .forms import LoginForm,RegisterationForm,ChangePasswdForm

#登录
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


#登出
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

#注册(需要验证邮箱) 
@auth.route('/register',methods=['GET','POST'])
def register():
    form=RegisterationForm()
    if form.validate_on_submit():
        user=User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()#提交才能赋予新用户id值
        #生成验证token
        token=user.generate_confirmation_token()
        send_email(user.email,'Confirm Your Account','auth/email/confirm',user=user,token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)

from flask.ext.login import current_user


#验证链接
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:#已经验证通过的账户
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


#限制未登录的用户功能
@auth.before_app_request #注册一个函数，在每次请求前运行
def before_request():
    #账户已经在登录状态,且没有被验证，且请求的端点不在认证蓝图中
    if current_user.is_authenticated \
        and not current_user.confirmed \
        and request.endpoint[:5]!='auth.' \
        and request.endpoint!='static':
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    #如果是匿名用户，或者用户已经验证
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    #未验证的用户
    return render_template('auth/unconfirmed.html')

#重新发送验证链接
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token=user.generate_confirmation_token()
    send_email(user.email,'Confirm Your Account','auth/email/confirm',user=user,token=token)
    flash('A confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))

#修改密码
@auth.route('/change_passwd',methods=['GET','POST'])
@login_required
def change_passwd():
    form=ChangePasswdForm()
    if form.validate_on_submit():
        if form.old_passwd.data==form.new_passwd.data:
            flash('old passwd is same to new passwd')
        else:
            if current_user.verify_password(form.old_passwd.data):
                #更新表数据
                current_user.password=form.new_passwd.data
                db.session.add(current_user)
                flash('Your password has been updated')
                return redirect(url_for('main.index'))
            else:
                flash('old password is error')
    return render_template('auth/change_passwd.html',form=form)