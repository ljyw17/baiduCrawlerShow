#encoding=utf-8
import http.cookiejar
import urllib
from bs4 import BeautifulSoup
import re
from django.db import connection
import os,django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SearchByBaiduSearch.settings")
django.setup()

def saveInfoBySearch(url, keyword, page, POS):
    "存储十条搜索结果至数据库，并将状态、当前页数和数据库查询位置更新后返回"

    try:
        cursor = connection.cursor()
        select_sql = "select * from search_results where keyword='"+str(keyword)+"'" #关键词记录
        cursor.execute(select_sql)
        result_num = len(cursor.fetchall()) #关键词记录条数
        if result_num >= POS + 10:  # 新更新数大于等于10，才返回True
            return (True, url, page)
    except:
        return (False, "", 0)

    regex = re.compile('\d{4}年(0?[1-9]|[1][012])月(0?[1-9]|[12][0-9]|3[01])日')  # 查日期的正则
    headers = {"Accept": "text/html, application/xhtml+xml, image/jxr, */*",
               "Accept - Encoding": "gzip, deflate, br",
               "Accept - Language": "zh - CN",
               "Connection": "Keep - Alive",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
               "referer": "baidu.com"} #头信息
    cjar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cjar))
    headall = []

    for key, value in headers.items(): #头信息转为list
        item = (key, value)
        headall.append(item)

    try:
        opener.addheaders = headall
        urllib.request.install_opener(opener)
        data = urllib.request.urlopen(url, timeout=5).read().decode('utf-8') #页面内容
        soup = BeautifulSoup(data, 'html.parser')

        if page < 6: #在6以内的页面和6之后的页面 的 下一页链接获取方式不同
            next_page = "http://www.baidu.com" + data.split("10</span></a><a href=\"")[1].split("\" class=\"n")[0]
        else:
            next_page = "http://www.baidu.com" + data.split(str(page+4) + "</span></a><a href=\"")[1].split("\" class=\"n")[0]
        page += 1 #页码数加一

        for result_table in soup.find_all('h3', class_='t'): #找特定标签的值
            a_click = result_table.find("a")
            title = a_click.get_text().replace("\'","").replace("\"","") #标题
            link = str(a_click).split("href=\"")[1].split("\" target")[0].replace("\'","").replace("\"","") #链接
            description = data[data.find(link):data.find(link)+4000] #简介

            if "百度快照" in description: #存在简介内容
                try:
                    date = re.search(regex, description).group(0) #求日期
                except:
                    date = "" #报错则日期为空

                description = ''.join(re.sub("[A-Za-z0-9</>\!.\{__\'}&@ ?#=|\":%-\[\]\,\。年月日]", "", description).split()) #简介内容进行筛选
                end_site = description.find("百度快照")
                description = description[:end_site][:90].replace("\'","").replace("\"","") #以“百度快照”结尾

            else:
                description = "" #没有简介内容，则简介和日期为空
                date = ""

            cursor = connection.cursor()
            select_sql = "select keyword, title, date_time, description from search_results where keyword='" + str(keyword) + "'"  # 关键词记录
            cursor.execute(select_sql)
            results = cursor.fetchall() #关键词记录

            if(str(keyword), str(title), str(date), str(description)) not in results: #如果数据库中没有，才存进去
                insert_sql = "insert into search_results(keyword, title, link, date_time, description)values('" + str(keyword) + "', '" + str(title) + "', '" + str(link) + "', '" + str(date) + "', '" + str(description) + "')" #存进数据库
                cursor.execute(insert_sql) #写入数据库

    except: #报错则返回False
        return (False, "", 0)

    return saveInfoBySearch(next_page, keyword, page, POS) #递归进行处理下一页

if __name__=="__main__":

    #测试
    keyword = "github"
    url = "http://www.baidu.com/s?wd=" + urllib.parse.quote(keyword)
    print(saveInfoBySearch(url, keyword, 0, 81))