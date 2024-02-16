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
                  version="1.0",
                  author="masterke",
                  desire_priority=100)
class zaobao(Plugin):
    content = None
    config_data = None
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info(f"[{__class__.__name__}] inited")

    def get_help_text(self, **kwargs):
        help_text = f"获取早报信息"
        return help_text

    def on_handle_context(self, e_context: EventContext):
        # 只处理文本消息
        if e_context['context'].type != ContextType.TEXT:
            return
        self.content = e_context["context"].content.strip()
        
        if self.content == "早报":
            logger.info(f"[{__class__.__name__}] 收到消息: {self.content}")
            # 读取配置文件
            config_path = os.path.join(os.path.dirname(__file__),"config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    self.config_data = json.load(file)
            else:
                logger.error(f"请先配置{config_path}文件")
                return
            
            reply = Reply()
            result = self.zaobao()
            if result != None:
                reply.type = ReplyType.TEXT
                reply.content = result
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                reply.type = ReplyType.ERROR
                reply.content = "获取失败,等待修复⌛️"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS

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
                json_data = response.json()
                if json_data.get('code') == 200 and json_data['data']['news']:
                    data = json_data['data']['news']
                    data = [i.rstrip("；") for i in data]
                    text = "\n====================\n".join(data[:10])
                    text = f"☀️早上好,今天是{json_data['data']['date']}\n\n" + text
                    logger.info(f"主接口获取早报成功:{data}")
                    return text
                else:
                    logger.error(f"主接口返回参数异常:{json_data}")
                    raise ValueError('not found data')
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
                    json_data = response.json()
                    if json_data.get('code') == "200" and json_data["news"]:
                        data = json_data["news"]
                        data = [i.rstrip("；") for i in data]
                        text = "\n====================\n".join(data[:10])
                        text = f"☀️早上好,今天是{json_data['date']}\n\n" + text
                        logger.info(f"备用接口获取早报成功:{data}")
                        return text
                    else:
                        logger.error(f"备用接口返回参数异常:{json_data}")
                else:
                    logger.error(f"备用接口请求失败:{response.status_code}")
            except Exception as e:
                logger.error(f"备用接口抛出异常:{e}")
        
        logger.error(f"所有接口都挂了,无法获取")
        return None
