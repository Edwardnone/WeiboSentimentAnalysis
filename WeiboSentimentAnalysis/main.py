from sina_login import Login
from spider import CollectData
from analysis import SemanticAnalysis

if __name__=="__main__":

    username = input('微博用户名：')
    password = input('微博密码：')
    login=Login()
    if login.login(username,password):
        #登录成功，开始爬虫数据
        session=login.getSession()#得到登录信息的Session
        keyword = '华泰'
        startTime = '2018-08-13'
        interval = '40'
        excelPath = 'data/weibo.xlsx'
        cd=CollectData(keyword,startTime,excelPath,session,interval)
        cd.start()
        #爬虫数据结束，开始语义分析
        sa=SemanticAnalysis(startTime,keyword,excelPath)
        sa.snowanalysis()#进行语义分析
        sa.getWordCloud()#得到词云图
        print("完成")