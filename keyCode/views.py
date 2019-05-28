#encoding=utf-8
from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
import hashlib, urllib, time
from .models import *
from django.shortcuts import redirect
from .searchKeyword import saveInfoBySearch

# Create your views here.
POS = 0 #在数据库中查询内容的位置
PAGE = 0 #页数
URL = "" #存储更新的url

#views
def logging(request):
    "注册成功后立即的登陆"
    if request.method == "POST":  # 登陆用户名密码验证

        username = request.POST.get('form-username') #获取前端输入的账户和密码
        password = request.POST.get('form-password')

        cursor = connection.cursor() #打开数据库
        select_sql = "select count(*) from user_table where username='" + str(username) + "'" #在数据库中查询用户名是否存在
        cursor.execute(select_sql)
        result_num = cursor.fetchone() #获取select_sql的结果

        if result_num[0] == 0:  # 验证用户名是否存在与数据库中
            return render(request, "loggingAfterFail.html") #如果数据库中没有该用户名的记录，则返回登陆失败页面
        else: #用户名存在
            select_sql = "select password from user_table where username='" + str(username) + "'" #验证密码正确与否
            cursor.execute(select_sql)
            real_password = cursor.fetchone()[0]

            if real_password != str(hashlib.md5(password.encode("utf8")).hexdigest()): #如果密码不正确
                insert_sql = "insert into login_log(username, date_time, status)values('" + str(username) + "', '" + str(int(time.time())) + "', 'failure" + "')" #登陆失败的记录
                try:
                    cursor.execute(insert_sql)  # 写入数据库
                except:
                    raise Exception("数据库写入出错")
                return render(request, "loggingAfterFail.html") #返回登陆错误页面
            else: #密码正确
                insert_sql = "insert into login_log(username, date_time, status)values('" + str(username) + "', '" + str(int(time.time())) + "', 'success" + "')" #登陆成功的记录
                try:
                    cursor.execute(insert_sql)  # 写入数据库
                except:
                    raise Exception("数据库写入出错")
                return redirect(search) #登陆成功，定向到搜索函数

    else: #GET请求，直接进到注册成功提示登陆页面
        return render(request, "loggingAfterRegister.html")

def index(request):
    "首页和登陆"
    if request.method == "POST": #登陆用户名密码验证

        username = request.POST.get('form-username')
        password = request.POST.get('form-password')

        cursor = connection.cursor()
        select_sql = "select count(*) from user_table where username='" + str(username) + "'" #查询用户名是否记录
        cursor.execute(select_sql)
        result_num = cursor.fetchone()

        if result_num[0] == 0: #如果没有记录该用户名
            return render(request, "loggingAfterFail.html") #提示登陆出错
        else: #有该用户名的记录
            select_sql = "select password from user_table where username='" + str(username) + "'" #查询该用户名的密码
            cursor.execute(select_sql)
            real_password = cursor.fetchone()[0] #正确的密码

            if real_password != str(hashlib.md5(password.encode("utf8")).hexdigest()): #如密码不正确
                insert_sql = "insert into login_log(username, date_time, status)values('" + str(username) + "', '" + str(int(time.time())) + "', 'failure" + "')" #记录登陆失败日志
                try:
                    cursor.execute(insert_sql)  #写入数据库
                except:
                    raise Exception("数据库写入出错")
                return render(request, "loggingAfterFail.html") #返回登陆失败页面
            else: #如果密码正确
                insert_sql = "insert into login_log(username, date_time, status)values('" + str(username) + "', '" + str(int(time.time())) + "', 'success" + "')" #记录登陆成功的日志
                try:
                    cursor.execute(insert_sql)  # 写入数据库
                except:
                    raise Exception("数据库写入出错")
                return redirect(search) #登陆成功，定向到搜索函数

    else: #GET请求，返回首页
        return render(request, "index.html")

def register(request):
    "注册"
    if request.method == "POST": #POST请求，进行注册

        username = request.POST.get('form-username') #先获取前端的用户名和密码
        password = request.POST.get('form-password')

        cursor = connection.cursor()
        select_sql = "select count(*) from user_table where username='"+str(username)+"'" #验证该用户名是否已经注册
        cursor.execute(select_sql)
        result_num = cursor.fetchone()

        if result_num[0] == 0 and len(username)!=0 and len(password)!=0: #该用户名和密码合法
            insert_sql = "insert into user_table(username, password)values('" + str(username) + "', '" + str(hashlib.md5(password.encode("utf8")).hexdigest()) + "')" #用户名和密码插入数据库
            try:
                cursor.execute(insert_sql) #写入数据库
            except:
                raise Exception("数据库写入出错")
            return redirect(logging) #注册成功,定向到登陆函数
        else: #用户名或密码不合法
            return render(request, "registerAfterFail.html") #返回注册失败页面

    else: #GET请求，返回注册页面
        return render(request, "register.html")

def search(request):
    "搜索"
    global POS, PAGE, URL
    status = True #存储内容至数据库的状态信息

    if request.method == "POST" and 'nextpage' not in request.POST: #第一次进入内容展示页面
        url = "http://www.baidu.com/s?wd=" + urllib.parse.quote(request.POST.get('keyword')) #对关键词构建出百度搜索的url
        POS = 0  # 第一次进入,数据库检索位置归零
        status, URL, PAGE = saveInfoBySearch(url, request.POST.get('keyword'), 1, POS) #调用检索存储方法

        if status == True: #如果检索存储成功
            cursor = connection.cursor()
            select_sql = "select * from search_results where keyword='" + str(request.POST.get('keyword')) + "' order by id asc limit " + str(POS) + ",10" #检索开头的十条
            cursor.execute(select_sql)
            results = cursor.fetchall()
            POS += 10 #位置加十
            return render(request, "content.html", {"tuple":results}) #返回内容页面
        else: #检索存储失败
            return render(request, "searchAfterError.html") #会到错误提示页

    if request.method == "POST" and 'nextpage' in request.POST: #点击下一页后
        cursor = connection.cursor()
        select_sql = "select * from search_results where keyword='" + str(request.POST.get('keyword')) + "' order by id asc limit " + str(POS) + "," + str(POS+10) #在数据库中重新检索下十条
        cursor.execute(select_sql)
        results = cursor.fetchall()

        if len(results) < 10: #如果不够十条了
            status, URL, PAGE = saveInfoBySearch(URL, request.POST.get('keyword'), PAGE, POS)  # 调用检索存储方法

        if status == True: #如果检索存储成功
            cursor = connection.cursor()
            select_sql = "select * from search_results where keyword='" + str(request.POST.get('keyword')) + "' order by id asc limit " + str(POS) + "," + str(POS+10) #检索下一页的十条
            cursor.execute(select_sql)
            results = cursor.fetchall()
            POS += 10 #位置加十
            return render(request, "content.html", {"tuple":results}) #返回内容页面
        else: #检索存储失败
            return render(request, "searchAfterError.html") #到错误提示页

    else: #GET请求，返回搜索首页
        return render(request, "search.html")