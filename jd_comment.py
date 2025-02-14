'''
new Env('自动评价');
8 8 2 1 * https://raw.githubusercontent.com/6dylan6/auto_comment/main/jd_comment.py
'''
import copy
import logging
import os
import random
import sys
import time, re
import urllib.parse
import platform
import toml

try:
	import jieba
	import jieba.analyse
	import requests
	from lxml import etree
	import zhon.hanzi

except:
	print('解决依赖问题...稍等')
	os.system('pip3 install lxml &> /dev/null')
	os.system('pip3 install jieba &> /dev/null')
	os.system('pip3 install zhon &> /dev/null')
	os.system('pip3 install requests &> /dev/null')
	os.system('pip3 install urllib3==1.25.11 &> /dev/null')
	import jieba
	import jieba.analyse
	from lxml import etree
	import requests
	import urllib.parse
import jdspider

# constants
ORDINARY_SLEEP_SEC = 10
SUNBW_SLEEP_SEC = 5
REVIEW_SLEEP_SEC = 10
SERVICE_RATING_SLEEP_SEC = 15

_COLORS = {
	'black': 0,
	'red': 1,
	'green': 2,
	'yellow': 3,
	'blue': 4,
	'magenta': 5,
	'cyan': 6,
	'white': 7
}

_RESET_SEQ = '\033[0m'
_COLOR_SEQ = '\033[1;%dm'
_BOLD_SEQ = '\033[1m'
_ITALIC_SEQ = '\033[3m'
_UNDERLINED_SEQ = '\033[4m'

_FORMATTER_COLORS = {
	'DEBUG': _COLORS['blue'],
	'INFO': _COLORS['green'],
	'WARNING': _COLORS['yellow'],
	'ERROR': _COLORS['red'],
	'CRITICAL': _COLORS['red']
}

user_aiUSER_AI_AUTO_COMMENT = False
AUTO_COMMENT_DEEPSEEK_BASE_URL = ""
AUTO_COMMENT_DEEPSEEK_USER_TOKEN = ""


def read_config_from_toml():
	# 读取 jd_config.toml 配置文件
	config_file_path = 'jd_config.toml'

	try:
		config = toml.load(config_file_path)
		# 获取 deepseek 部分的配置
		deepseek_config = config.get('deepseek', {})
		result = False if not deepseek_config.get('USER_AI_AUTO_COMMENT', None) else True
		return {"user_ai": result,
				"deepseek_base_url": deepseek_config.get('AUTO_COMMENT_DEEPSEEK_BASE_URL', None),
				"deepseek_base_token": deepseek_config.get('AUTO_COMMENT_DEEPSEEK_USER_TOKEN', None)}
	except Exception as e:
		print(f"读取jd_config.toml文件时出错: {e}")
		return {}


def read_config_from_env():
	print("从环境变量读取的配置")
	result = False if not os.environ.get("USER_AI_AUTO_COMMENT") else True
	return {"user_ai": result,
			"deepseek_base_url": os.environ["AUTO_COMMENT_DEEPSEEK_BASE_URL"],
			"deepseek_base_token": os.environ["AUTO_COMMENT_DEEPSEEK_USER_TOKEN"]}


def get_deepseek_config():
	# 获取当前操作系统
	current_system = platform.system()
	if current_system == 'Darwin':  # macOS
		return read_config_from_toml()
	elif current_system == 'Linux':  # Linux
		return read_config_from_env()
	else:
		raise Exception("不支持的操作系统: {}".format(current_system))


def format_style_seqs(msg, use_style=True):
	if use_style:
		msg = msg.replace('$RESET', _RESET_SEQ)
		msg = msg.replace('$BOLD', _BOLD_SEQ)
		msg = msg.replace('$ITALIC', _ITALIC_SEQ)
		msg = msg.replace('$UNDERLINED', _UNDERLINED_SEQ)
	else:
		msg = msg.replace('$RESET', '')
		msg = msg.replace('$BOLD', '')
		msg = msg.replace('$ITALIC', '')
		msg = msg.replace('$UNDERLINED', '')


class StyleFormatter(logging.Formatter):
	def __init__(self, fmt=None, datefmt=None, use_style=True):
		logging.Formatter.__init__(self, fmt, datefmt)
		self.use_style = use_style

	def format(self, record):
		rcd = copy.copy(record)
		levelname = rcd.levelname
		if self.use_style and levelname in _FORMATTER_COLORS:
			levelname_with_color = '%s%s%s' % (
				_COLOR_SEQ % (30 + _FORMATTER_COLORS[levelname]),
				levelname, _RESET_SEQ)
			rcd.levelname = levelname_with_color
		return logging.Formatter.format(self, rcd)


# 评价生成
def generation(pname, _class=0, _type=1):
	user_ai = get_deepseek_config().get("user_ai")
	# 配置中需要声明使用AI生成评价
	if user_ai is True:
		return 5, generation_ai(pname, _type)
	items = ['商品名']
	items.clear()
	items.append(pname)
	print('Items: %s', items)
	loop_times = len(items)
	print('Total loop times: %d', loop_times)
	for i, item in enumerate(items):
		print('Loop: %d / %d', i + 1, loop_times)
		print('Current item: %s', item)
		spider = jdspider.JDSpider(item, ck)
		print('Successfully created a JDSpider instance')
		# 增加对增值服务的评价鉴别
		if "赠品" in pname or "非实物" in pname or "京服无忧" in pname or "权益" in pname or "非卖品" in pname or "增值服务" in pname:
			result = [
				"赠品挺好的。",
				"很贴心，能有这样免费赠送的赠品!",
				"正好想着要不要多买一份增值服务，没想到还有这样的赠品。",
				"赠品正合我意。",
				"赠品很好，挺不错的。",
				"本来买了产品以后还有些担心。但是看到赠品以后就放心了。",
				"不论品质如何，至少说明店家对客的态度很好！",
				"我很喜欢这些商品！",
				"我对于商品的附加值很在乎，恰好这些赠品为这件商品提供了这样的的附加值，这令我很满意。"
				"感觉现在的网购环境环境越来越好了，以前网购的时候还没有过么多贴心的赠品和增值服务",
				"第一次用京东，被这种赠品和增值服物的良好态度感动到了。",
				"赠品还行。"
			]
		else:
			result = spider.getData(4, 3)  # 这里可以自己改
		print('Result: %s', result)

	# class 0是评价 1是提取id
	try:
		name = jieba.analyse.textrank(pname, topK=5, allowPOS='n')[0]
		print('Name: %s', name)
	except Exception as e:
		name = "宝贝"
	if _class == 1:
		print('_class is 1. Directly return name')
		return name
	else:
		if _type == 1:
			num = 6
		elif _type == 0:
			num = 4
		num = min(num, len(result))
		# use `.join()` to improve efficiency
		comments = ''.join(random.sample(result, num))
		print('_type: %d', _type)
		print('num: %d', num)
		print('Raw comments: %s', comments)

		return 5, comments.replace("$", name)


# deepseek评价生成
def generation_ai(pname, _class=0, _type=1):
	deepseek_base_url = get_deepseek_config().get("deepseek_base_url")
	deepseek_base_token = get_deepseek_config().get("deepseek_base_token")
	# 当存在 OPENAI_API_BASE_URL 时，使用反向代理
	if deepseek_base_url is None:
		print("请先根据文档配置 deepseek [请求地址]")
		return None
	if deepseek_base_token is None or (isinstance(deepseek_base_token, str) and len(deepseek_base_token) == 0):
		deepseek_base_token = "[userToken value]"
		print("如 deepseek_free_api 已经配置 [DEEP_SEEK_CHAT_AUTHORIZATION] 可以忽略！")
	if _type == 0:
		prompt = f"针对 {pname} 的使用一段时候后的追加评价，请用精简、口语化的风格进行评论"
	else:
		prompt = f"针对 {pname} 的评价，请用简短、口语化的风格进行评论"
	# 设置超时时间（单位：秒）
	timeout = 20  # 20秒超时
	# 错误信息
	SERVER_BUSY_ERROR = "服务器繁忙，请稍后再试"
	try:
		response = requests.post(
			f"{deepseek_base_url}/v1/chat/completions",
			headers={
				"Content-Type": "application/json",
				"Authorization": f"Bearer {deepseek_base_token}",
			},
			json={
				"model": "deepseek",
				"messages": [
					{
						"role": "user",
						"content": prompt
					}
				],
				"stream": False
			},
			timeout=timeout,
		)
		# 检查响应状态
		if response.status_code == 200:
			# 解析响应内容
			response_data = response.json()
			# 检查是否有错误信息
			if 'error' in response_data and SERVER_BUSY_ERROR in response_data['error']:
				raise Exception(SERVER_BUSY_ERROR)  # 抛出自定义异常
			# 提取并打印 content 中的内容
			content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
			if len(content) > 1:
				print("结果是:", content)
				return content
			else:
				print(f"请求结果是：{response_data}")
		else:
			print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
	except requests.exceptions.Timeout:
		# 请求超时处理
		print(f"请求超时，未在 {timeout} 秒内获得响应。")
	except requests.exceptions.RequestException as e:
		# 处理其他请求异常
		print(f"请求发生错误: {e}")
	except Exception as e:
		# 处理自定义的服务器繁忙错误
		print(f"自定义错误: {e}")
	return None


# 查询全部评价
def all_evaluate():
	try:
		N = {}
		url = 'https://club.jd.com/myJdcomments/myJdcomment.action?'
		print('URL: %s', url)
		print('Fetching website data')
		req = requests.get(url, headers=headers)
		print(
			'Successfully accepted the response with status code %d',
			req.status_code)
		if not req.ok:
			print(
				'Status code of the response is %d, not 200', req.status_code)
		req_et = etree.HTML(req.text)
		print('Successfully parsed an XML tree')
		evaluate_data = req_et.xpath('//*[@id="main"]/div[2]/div[1]/div/ul/li')
		loop_times = len(evaluate_data)
		print('Total loop times: %d', loop_times)
		for i, ev in enumerate(evaluate_data):
			print('Loop: %d / %d', i + 1, loop_times)
			na = ev.xpath('a/text()')[0]
			print('na: %s', na)
			# print(ev.xpath('b/text()')[0])
			try:
				num = ev.xpath('b/text()')[0]
				print('num: %s', num)
			except IndexError:
				num = 0
			N[na] = int(num)
		return N
	except Exception as e:
		print(e)


# 评价晒单
def sunbw(N):
	try:
		Order_data = []
		req_et = []
		loop_times = 2
		print('Fetching website data')
		print('Total loop times: %d', loop_times)
		for i in range(loop_times):
			url = (f'https://club.jd.com/myJdcomments/myJdcomment.action?sort=0&'
				   f'page={i + 1}')
			print('URL: %s', url)
			req = requests.get(url, headers=headers)
			print(
				'Successfully accepted the response with status code %d',
				req.status_code)
			if not req.ok:
				print(
					'Status code of the response is %d, not 200', req.status_code)
			req_et.append(etree.HTML(req.text))
			print('Successfully parsed an XML tree')
		print('Fetching data from XML trees')
		print('Total loop times: %d', loop_times)
		for idx, i in enumerate(req_et):
			print('Loop: %d / %d', idx + 1, loop_times)
			print('Fetching order data in the default XPath')
			elems = i.xpath(
				'//*[@id="main"]/div[2]/div[2]/table/tbody')
			print('Count of fetched order data: %d', len(elems))
			Order_data.extend(elems)
		print(f"当前共有{N['待评价订单']}个评价。")
		print('Commenting on items')
		for i, Order in enumerate(reversed(Order_data)):
			if i + 1 > 10:
				print(f'\n已评价10个订单，跳出')
				break
			try:
				oid = Order.xpath('tr[@class="tr-th"]/td/span[3]/a/text()')[0]
				print('oid: %s', oid)
				oname_data = Order.xpath(
					'tr[@class="tr-bd"]/td[1]/div[1]/div[2]/div/a/text()')
				print('oname_data: %s', oname_data)
				pid_data = Order.xpath(
					'tr[@class="tr-bd"]/td[1]/div[1]/div[2]/div/a/@href')
				print('pid_data: %s', pid_data)
			except IndexError:
				print(f"第{i + 1}个订单未查找到商品，跳过。")
				continue
			loop_times1 = min(len(oname_data), len(pid_data))
			print('Commenting on orders')
			print('Total loop times: %d', loop_times1)
			idx = 0
			for oname, pid in zip(oname_data, pid_data):
				pid = re.findall('(?<=jd.com/)[(0-9)*?]+', pid)
				if len(pid) == 0:
					continue
				pid = pid[0]
				print(f'\n开始第{i + 1}个订单: {oid}')
				print('pid: %s', pid)
				print('oid: %s', oid)
				xing, Str = generation(oname)
				print(f'评价信息：{xing}星  ' + Str)
				# 获取图片
				url1 = (f'https://club.jd.com/discussion/getProductPageImageCommentList'
						f'.action?productId={pid}')
				print('Fetching images using the default URL')
				print('URL: %s', url1)
				req1 = requests.get(url1, headers=headers)
				print(
					'Successfully accepted the response with status code %d',
					req1.status_code)
				if not req1.ok:
					print(
						'Status code of the response is %d, not 200', req1.status_code)
				imgdata = req1.json()
				print('Image data: %s', imgdata)
				if imgdata["imgComments"]["imgCommentCount"] > 10:
					pnum = random.randint(2, int(imgdata["imgComments"]["imgCommentCount"] / 10) + 1)
					print('Count of fetched image comments is 0')
					print('Fetching images using another URL')
					url1 = (f'https://club.jd.com/discussion/getProductPageImage'
							f'CommentList.action?productId={pid}&page={pnum}')
					print('URL: %s', url1)
					time.sleep(1)
					req1 = requests.get(url1, headers=headers)
					print(
						'Successfully accepted the response with status code %d',
						req1.status_code)
					if not req1.ok:
						print(
							'Status code of the response is %d, not 200',
							req1.status_code)
					imgdata2 = req1.json()
					print('Image data: %s', imgdata2)
				try:
					imgurl = random.choice(imgdata["imgComments"]["imgList"])["imageUrl"]
					if ('imgdata2' in dir()):
						imgurl2 = random.choice(imgdata2["imgComments"]["imgList"])["imageUrl"]
					else:
						imgurl2 = ''
				except Exception:
					imgurl = ''
					imgurl2 = ''
				print('Image URL: %s', imgurl)

				print(f'图片：{imgurl + "," + imgurl2}')
				# 提交晒单
				print('Preparing for commenting')
				url2 = "https://club.jd.com/myJdcomments/saveProductComment.action"
				print('URL: %s', url2)
				headers['Referer'] = ('https://club.jd.com/myJdcomments/orderVoucher.action')
				headers['Origin'] = 'https://club.jd.com'
				headers['Content-Type'] = 'application/x-www-form-urlencoded'
				print('New header for this request: %s', headers)
				data = {
					'orderId': oid,
					'productId': pid,
					'score': str(xing),  # 商品几星
					'content': urllib.parse.quote(Str),  # 评价内容
					'imgs': imgurl + ',' + imgurl2,
					'saveStatus': 2,
					'anonymousFlag': 1
				}
				print('Data: %s', data)
				pj2 = requests.post(url2, headers=headers, data=data)
				if pj2.ok:
					print(f'提交成功！')
				print('Sleep time (s): %.1f', ORDINARY_SLEEP_SEC)
				time.sleep(ORDINARY_SLEEP_SEC)
				idx += 1
		N['待评价订单'] -= 1
		return N
	except Exception as e:
		print(e)


# 追评
def review(N):
	try:
		req_et = []
		Order_data = []
		loop_times = 2
		print('Fetching website data')
		print('Total loop times: %d', loop_times)
		for i in range(loop_times):
			print('Loop: %d / %d', i + 1, loop_times)
			url = (f"https://club.jd.com/myJdcomments/myJdcomment.action?sort=3"
				   f"&page={i + 1}")
			print('URL: %s', url)
			req = requests.get(url, headers=headers)
			print(
				'Successfully accepted the response with status code %d',
				req.status_code)
			if not req.ok:
				print(
					'Status code of the response is %d, not 200', req.status_code)
			req_et.append(etree.HTML(req.text))
			print('Successfully parsed an XML tree')
		print('Fetching data from XML trees')
		print('Total loop times: %d', loop_times)
		for idx, i in enumerate(req_et):
			print('Loop: %d / %d', idx + 1, loop_times)
			print('Fetching order data in the default XPath')
			elems = i.xpath(
				'//*[@id="main"]/div[2]/div[2]/table/tr[@class="tr-bd"]')
			print('Count of fetched order data: %d', len(elems))
			Order_data.extend(elems)
		print(f"当前共有{N['待追评']}个需要追评。")
		print('Commenting on items')
		for i, Order in enumerate(reversed(Order_data)):
			if i + 1 > 10:
				print(f'\n已评价10个订单，跳出')
				break
			oname = Order.xpath('td[1]/div/div[2]/div/a/text()')[0]
			_id = Order.xpath('td[3]/div/a/@href')[0]
			print('_id: %s', _id)
			url1 = ("https://club.jd.com/afterComments/"
					"saveAfterCommentAndShowOrder.action")
			print('URL: %s', url1)
			pid, oid = _id.replace(
				'http://club.jd.com/afterComments/productPublish.action?sku=',
				"").split('&orderId=')
			print('pid: %s', pid)
			print('oid: %s', oid)
			print(f'\n开始第{i + 1}个订单: {oid}')
			_, context = generation(oname, _type=0)
			print(f'追评内容：{context}')
			data1 = {
				'orderId': oid,
				'productId': pid,
				'content': urllib.parse.quote(context),
				'anonymousFlag': 1,
				'score': 5
			}
			print('Data: %s', data1)
			req_url1 = requests.post(url1, headers=headers, data=data1)
			if req_url1.ok:
				print(f'提交成功！')
			print('Sleep time (s): %.1f', REVIEW_SLEEP_SEC)
			time.sleep(REVIEW_SLEEP_SEC)
			N['待追评'] -= 1
		return N
	except Exception as e:
		print(e)


# 服务评价
def Service_rating(N):
	try:
		Order_data = []
		req_et = []
		loop_times = 2
		print('Fetching website data')
		print('Total loop times: %d', loop_times)
		for i in range(loop_times):
			print('Loop: %d / %d', i + 1, loop_times)
			url = (f"https://club.jd.com/myJdcomments/myJdcomment.action?sort=4"
				   f"&page={i + 1}")
			print('URL: %s', url)
			req = requests.get(url, headers=headers)
			print(
				'Successfully accepted the response with status code %d',
				req.status_code)
			if not req.ok:
				print(
					'Status code of the response is %d, not 200', req.status_code)
			req_et.append(etree.HTML(req.text))
			print('Successfully parsed an XML tree')
		print('Fetching data from XML trees')
		print('Total loop times: %d', loop_times)
		for idx, i in enumerate(req_et):
			print('Loop: %d / %d', idx + 1, loop_times)
			print('Fetching order data in the default XPath')
			elems = i.xpath(
				'//*[@id="main"]/div[2]/div[2]/table/tbody/tr[@class="tr-th"]')
			print('Count of fetched order data: %d', len(elems))
			Order_data.extend(elems)
		print(f"当前共有{N['服务评价']}个需要服务评价。")
		print('Commenting on items')
		for i, Order in enumerate(reversed(Order_data)):
			if i + 1 > 10:
				print(f'\n已评价10个订单，跳出')
				break
			# oname = Order.xpath('td[1]/div[1]/div[2]/div/a/text()')[0]
			oid = Order.xpath('td[1]/span[3]/a/text()')[0]
			print(f'\n开始第{i + 1}个订单: {oid}')
			print('oid: %s', oid)
			url1 = (f'https://club.jd.com/myJdcomments/insertRestSurvey.action'
					f'?voteid=145&ruleid={oid}')
			print('URL: %s', url1)
			data1 = {
				'oid': oid,
				'gid': '32',
				'sid': '186194',
				'stid': '0',
				'tags': '',
				'ro591': f'591A{random.randint(4, 5)}',  # 商品符合度
				'ro592': f'592A{random.randint(4, 5)}',  # 店家服务态度
				'ro593': f'593A{random.randint(4, 5)}',  # 快递配送速度
				'ro899': f'899A{random.randint(4, 5)}',  # 快递员服务
				'ro900': f'900A{random.randint(4, 5)}'  # 快递员服务
			}
			print('Data: %s', data1)
			pj1 = requests.post(url1, headers=headers, data=data1)
			if pj1.ok:
				print(f'提交成功！')
			print('Sleep time (s): %.1f', SERVICE_RATING_SLEEP_SEC)
			time.sleep(SERVICE_RATING_SLEEP_SEC)
			N['服务评价'] -= 1
		return N
	except Exception as e:
		print(e)


def No():
	print('-' * 20)
	N = all_evaluate()
	s = '----'.join(['{} {}'.format(i, N[i]) for i in N])
	print(s)
	print('-' * 20)
	return N


def main():
	N = No()
	print('N value after executing No(): %s', N)
	if not N:
		print('CK错误，请确认是否电脑版CK！')
		return
	if N['待评价订单'] != 0:
		print("1.开始评价晒单")
		N = sunbw(N)
		print('N value after executing sunbw(): %s', N)
		N = No()
		print('N value after executing No(): %s', N)
	if N['待追评'] != 0:
		print("2.开始追评！")
		N = review(N)
		print('N value after executing review(): %s', N)
		N = No()
		print('N value after executing No(): %s', N)
	if N['服务评价'] != 0:
		print('3.开始服务评价')
		N = Service_rating(N)
		print('N value after executing Service_rating(): %s', N)
		N = No()
		print('N value after executing No(): %s', N)
	print("该账号运行完成！")


def get_ck():
	cks = []
	jd_cooke = ""
	if "PC_COOKIE" in os.environ:
		jd_cooke = os.environ["PC_COOKIE"]
	else:
		# 获取当前脚本所在目录
		current_directory = os.path.dirname(__file__)
		# 构建配置文件路径
		config_file_path = os.path.join(current_directory, 'jd_config.toml')
		# 检查配置文件是否存在
		if os.path.exists(config_file_path):
			# 读取配置文件
			with open(config_file_path, 'r') as file:
				config_data = toml.load(file)
				# 获取 cookie 下的 PC_COOKIE 变量
				jd_cooke = config_data.get('cookie', {}).get('PC_COOKIE')
		else:
			print(f"Error: The file '{config_file_path}' was not found.")
	if len(jd_cooke) > 200:
		if '&' in jd_cooke:
			cks = jd_cooke.split('&')
		else:
			cks.append(jd_cooke)
	else:
		print("CK错误，请确认是否电脑版CK！")
		sys.exit(1)
	print("已获取环境变量 CK")
	return cks


if __name__ == '__main__':
	cks = get_ck()
	try:
		i = 1
		for ck in cks:
			headers = {
				'cookie': ck.encode("utf-8"),
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36',
				'Connection': 'keep-alive',
				'Cache-Control': 'max-age=0',
				'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
				'sec-ch-ua-mobile': '?0',
				'sec-ch-ua-platform': '"Windows"',
				'DNT': '1',
				'Upgrade-Insecure-Requests': '1',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
				'Sec-Fetch-Site': 'same-site',
				'Sec-Fetch-Mode': 'navigate',
				'Sec-Fetch-User': '?1',
				'Sec-Fetch-Dest': 'document',
				'Referer': 'https://order.jd.com/',
				'Accept-Encoding': 'gzip, deflate, br',
				'Accept-Language': 'zh-CN,zh;q=0.9',
			}
			print('Builtin HTTP request header: %s', headers)
			print('Starting main processes')
			print('\n开始第 ' + str(i) + ' 个账号评价...\n')
			main()
			i += 1
	# NOTE: It needs 3,000 times to raise this exception. Do you really want to
	# do like this?
	except RecursionError:
		print("多次出现未完成情况，程序自动退出")
