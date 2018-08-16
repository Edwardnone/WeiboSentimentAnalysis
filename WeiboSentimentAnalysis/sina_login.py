import time
import base64
import rsa
import math
import random
import binascii
import requests
import re
from urllib.parse import quote_plus
import matplotlib.pyplot as plt

class Login:

    def __init__(self):
        # 构造 Request headers
        # agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
        self.agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0'
        self.headers = {
            'User-Agent': self.agent
        }
        self.session = requests.session()
        # 访问 初始页面带上 cookie
        self.index_url = "http://weibo.com/login.php"
        self.verify_code_path = './pincode.png'

    def get_pincode_url(self,pcid):
        size = 0
        url = "http://login.sina.com.cn/cgi/pin.php"
        pincode_url = '{}?r={}&s={}&p={}'.format(url, math.floor(random.random() * 100000000), size, pcid)
        return pincode_url

    def get_img(self,url):
        resp = requests.get(url, headers=self.headers, stream=True)
        with open(self.verify_code_path, 'wb') as f:
            for chunk in resp.iter_content(1000):
                f.write(chunk)

    def get_su(self,username):
        """
        对 email 地址和手机号码 先 javascript 中 encodeURIComponent
        对应 Python 3 中的是 urllib.parse.quote_plus
        然后在 base64 加密后decode
        """
        username_quote = quote_plus(username)
        username_base64 = base64.b64encode(username_quote.encode("utf-8"))
        return username_base64.decode("utf-8")

    # 预登陆获得 servertime, nonce, pubkey, rsakv
    def get_server_data(self,su):
        pre_url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su="
        pre_url = pre_url + su + "&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)&_="
        prelogin_url = pre_url + str(int(time.time() * 1000))
        pre_data_res = self.session.get(prelogin_url, headers=self.headers)

        sever_data = eval(pre_data_res.content.decode("utf-8").replace("sinaSSOController.preloginCallBack", ''))

        return sever_data

    # 这一段用户加密密码，需要参考加密文件
    def get_password(self,password, servertime, nonce, pubkey):
        rsaPublickey = int(pubkey, 16)
        key = rsa.PublicKey(rsaPublickey, 65537)  # 创建公钥,
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)  # 拼接明文js加密文件中得到
        message = message.encode("utf-8")
        passwd = rsa.encrypt(message, key)  # 加密
        passwd = binascii.b2a_hex(passwd)  # 将加密信息转换为16进制。
        return passwd

    def login(self,username, password):
        # su 是加密后的用户名
        su = self.get_su(username)
        sever_data = self.get_server_data(su)
        servertime = sever_data["servertime"]
        nonce = sever_data['nonce']
        rsakv = sever_data["rsakv"]
        pubkey = sever_data["pubkey"]
        password_secret = self.get_password(password, servertime, nonce, pubkey)

        postdata = {
            'entry': 'weibo',
            'gateway': '1',
            'from': '',
            'savestate': '7',
            'useticket': '1',
            'pagerefer': "http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl",
            'vsnf': '1',
            'su': su,
            'service': 'miniblog',
            'servertime': servertime,
            'nonce': nonce,
            'pwencode': 'rsa2',
            'rsakv': rsakv,
            'sp': password_secret,
            'sr': '1366*768',
            'encoding': 'UTF-8',
            'prelt': '401',
            'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META'
        }

        need_pin = sever_data['showpin']
        if need_pin == 1:
            # 为手动填写验证码
            print('需要手工输入验证码')
            pcid = sever_data['pcid']
            postdata['pcid'] = pcid
            img_url = self.get_pincode_url(pcid)
            self.get_img(img_url)
            image = plt.imread('./pincode.png')
            plt.imshow(image)
            plt.show()

            verify_code = input('验证码：')
            postdata['door'] = verify_code

        login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
        login_page = self.session.post(login_url, data=postdata, headers=self.headers)
        login_loop = (login_page.content.decode("GBK"))
        pa = r'location\.replace\([\'"](.*?)[\'"]\)'
        loop_url = re.findall(pa, login_loop)[0]
        login_index = self.session.get(loop_url, headers=self.headers)
        uuid = login_index.text
        uuid_pa = r'"uniqueid":"(.*?)"'
        try:
            uuid_res = re.findall(uuid_pa, uuid, re.S)[0]
            web_weibo_url = "http://weibo.com/%s/profile?topnav=1&wvr=6&is_all=1" % uuid_res
            weibo_page = self.session.get(web_weibo_url, headers=self.headers)
            weibo_pa = r'<title>(.*?)</title>'
            user_name = re.findall(weibo_pa, weibo_page.content.decode("utf-8", 'ignore'), re.S)[0]
            print('登陆成功，你的用户名为：' + user_name)
            return True
        except:
            print('登录失败，请确保验证码、用户信息准确')
            return False

    def getSession(self):
        return self.session
    #username = input('微博用户名：')
    #password = input('微博密码：')

