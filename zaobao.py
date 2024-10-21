from datetime import datetime
import requests
import plugins
from plugins import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger

BASE_URL_ALAPI = "https://v2.alapi.cn/api/"
BASE_URL_XIAROU = "http://api.suxun.site/api/"


@plugins.register(name="zaobao",
                  desc="获取早报",
                  version="1.1",
                  author="masterke",
                  desire_priority=100)
class zaobao(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info(f"[{__class__.__name__}] inited")



    def on_handle_context(self, e_context: EventContext):
        self.context = e_context['context']
        self.e_context = e_context
        self.channel = e_context['channel']
        self.message = e_context["context"].content
        # 只处理文本消息
        if self.context.type != ContextType.TEXT:
            return
        elif self.message != "早报":
            return
        # =======================读取配置文件==========================
        logger.info(f"[{__class__.__name__}] 收到消息: {self.message}")
        config_path = os.path.join(os.path.dirname(__file__),"config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                self.config_data = json.load(file)
        else:
            logger.error(f"请先配置{config_path}文件")
            return
        # =======================插件处理流程==========================
        result, result_type = self.zaobao()
        reply = Reply()
        if result != None:
            reply.type = result_type
            reply.content = result
            self.e_context["reply"] = reply
            self.e_context.action = EventAction.BREAK_PASS
        else:
            reply.type = ReplyType.ERROR
            reply.content = "获取失败,等待修复⌛️"
            self.e_context["reply"] = reply
            self.e_context.action = EventAction.BREAK_PASS
    # =======================函数定义部分==========================
    def zaobao(self):
        try:
            #主接口
            url = BASE_URL_ALAPI + "zaobao"
            payload = f"token={self.config_data['alapi_token']}&format=json"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            response = requests.post(url=url,
                                     data=payload,
                                     headers=headers,
                                     timeout=2)
            if response.status_code == 200:
                rjson = response.json()
                
                if response.status_code !=200 or rjson.get('code') != 200 or rjson['data']['news'] == None:
                    logger.error(f"主接口返回异常:{rjson}")
                    raise requests.ConnectionError
                else:
                    data = rjson['data']['news']
                    data = [i.rstrip("；") for i in data]
                    text = "\n====================\n".join(data[:10])
                    formatted_date = datetime.strptime(rjson['data']['date'], "%Y-%m-%d").strftime("%Y年%m月%d日")
                    text = f"☀️早上好，今天是{formatted_date}\n\n" + text
                    logger.info(f"主接口获取早报成功:{data}")
                    return text, ReplyType.TEXT
            else:
                logger.error(f"主接口请求失败:{response.status_code}")
                raise requests.ConnectionError
        except Exception as e:
            logger.error(f"主接口抛出异常:{e}")
            try:
                #备用接口
                url = BASE_URL_XIAROU + "sixs"
                payload = f"type=json"
                headers = {'Content-Type': "application/x-www-form-urlencoded"}
                response = requests.post(url=url,
                                         data=payload,
                                         headers=headers,
                                         timeout=2)
                if response.status_code == 200:
                    rjson = response.json()
                    if response.status_code !=200 or rjson.get('code') != "200" or rjson['news'] == None:
                        logger.error(f"备用接口返回异常:{rjson}")
                        return None, ReplyType.ERROR
                    else:
                        data = rjson["news"]
                        data = [i.rstrip("；") for i in data]
                        text = "\n====================\n".join(data[:10])
                        text = f"☀️早上好，今天是{rjson['date']}\n\n" + text
                        logger.info(f"备用接口获取早报成功:{data}")
                        return text, ReplyType.TEXT
                else:
                    logger.error(f"备用接口请求失败:{response.status_code}")
            except Exception as e:
                logger.error(f"备用接口抛出异常:{e}")
        
        logger.error(f"所有接口都挂了,无法获取")
        return None, ReplyType.ERROR

    def get_help_text(self, **kwargs):
        help_text = f"发送【早报】获取早报信息"
        return help_text