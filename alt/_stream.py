
from time import sleep
from json import loads,dumps
from threading import Thread
from websocket import WebSocketApp
from requests import get

try:
	from alt._lsr_oi import LSR_OI
	from alt._db import DB, FILTROS_COMUNS, FILTROS_INDCTR, SQL_PRICES
except ModuleNotFoundError:
	from _lsr_oi import LSR_OI
	from _db import DB, FILTROS_COMUNS, FILTROS_INDCTR, SQL_PRICES

from collections import deque


LSR_OI_MNGR= LSR_OI()
BANCO_DADOS= DB(False)
TIMEFRAMES = ('15m', '1h', '4h', '1d', '2d')

class Stream:
	def __init__(self, on_open, on_message, exchange):
		self.on_open = on_open
		self.on_message = on_message
	def on_close(self, ws, status_code, msg_code):
		print('[!] Stream fechado:',status_code,'|',msg_code)
	def on_error(self, ws, err):
		if len(str(err)) > 0:
			print('[!] Erro no websocket:',err)
	def __start_ws(self, url_wss):
		while True:
			try:
				wss = WebSocketApp(url_wss, on_close=self.on_close, on_error=self.on_error, 
										on_open=self.on_open, on_message=self.on_message)
				wss.run_forever()
			except KeyboardInterrupt:
				print('\n[!] Cancelado pelo user')
				break
			except Exception as err:
				print('Erro no loop:',err)
				sleep(5)
	def start_wss(self, urls_wss):
		for url_wss in urls_wss:
			Thread(target=self.__start_ws, args=(url_wss,)).start()
			sleep(2)

#####

class Binance(Stream):
	url_rest_api = 'https://fapi.binance.com'
	url_wss_api  = 'wss://fstream.binance.com/stream?streams='
	ticker_24h = True
	####
	price_current = {}
	last_price_15m = {}
	last_price_1h  = {}
	last_price_4h  = {}
	last_price_1d  = {}
	last_price_3d  = {}
	last_trades = {}
	####
	def __init__(self):
		super().__init__(self.on_open, self.on_message, 'binance')
		_pares = self.buscar_pares()
		_split = len(_pares) // 6
		_streams = []
		for i in range(0, len(_pares), _split):
			new_pares = '/'.join(_pares[i:i+_split])
			_streams.append(self.url_wss_api + new_pares)
		self.start_wss(_streams)
		sleep(5)
		Thread(target=self._update_pares, args=()).start()
	def on_open(self, ws):
		print('[!] Websocket aberto')
	def on_message(self, ws, msg):
		msg = loads(msg)
		Thread(target=self.__message, args=(msg,)).start()
	def __message(self, msg):
		if '!ticker@arr' == msg['stream'] and self.ticker_24h:
			self.ticker_24h = False
			Thread(target=self.ticker_manager, args=(msg['data'],)).start()
		elif '@kline_' in msg['stream']:
			kline = msg['data']['k']
			first = float(kline['o'])
			last  = float(kline['c'])
			change= round(((last-first)/first)*100,2)
			###
			symbol= kline['s']
			timeframe = kline['i']
			###
			if timeframe == '15m':
				self.price_current[symbol] = round(last,2)
				self.last_price_15m[symbol] = change
			elif timeframe == '1h':
				self.last_price_1h[symbol] = change
			elif timeframe == '4h':
				self.last_price_4h[symbol] = change
			elif timeframe == '3d':
				self.last_price_3d[symbol] = change
	def ticker_manager(self, lines):
		for line in lines:
			if line['s'] not in self.last_price_15m.keys():
				continue
			symbol = line['s']
			change = round(float(line['P']),2)
			self.last_price_1d[symbol] = change
			self.last_trades[symbol] = int(line['n'])
		self.ticker_24h = True
	def buscar_pares(self):
		url = self.url_rest_api + '/fapi/v1/exchangeInfo'
		content = get(url).json()["symbols"]
		pares_tf= []
		pares_raw = []
		for asset in content:
			if asset["contractType"] == "PERPETUAL" and asset["status"] == "TRADING" and asset["quoteAsset"] == 'USDT':
				pair = asset['pair']
				pares_raw.append((pair))
				###
				self.price_current[pair] = 0
				self.last_price_15m[pair] = 0
				self.last_price_1h[pair] = 0
				self.last_price_4h[pair] = 0
				self.last_price_1d[pair] = 0
				self.last_price_3d[pair] = 0
				self.last_trades[pair] = 0
				###
				pares_tf.append(f'{pair.lower()}@kline_15m')
				pares_tf.append(f'{pair.lower()}@kline_1h')
				pares_tf.append(f'{pair.lower()}@kline_4h')
				pares_tf.append(f'{pair.lower()}@kline_3d')
		pares_tf.append('!ticker@arr')
		## adicionar os pares
		with BANCO_DADOS.conn_thread() as pool:
			BANCO_DADOS.adicionar_pares('binance', pares_raw, pool)
		### thread lsr e oi
		Thread(target=LSR_OI_MNGR.start, args=('binance',)).start()
		return pares_tf
	def _update_pares(self):
		with BANCO_DADOS.conn_thread() as pool:
			pares = [c[0] for c in BANCO_DADOS.query('SELECT par FROM binance', pool, False)]
			while True:
				datas = []
				for pair in pares:
					datas.append((
						self.price_current[pair],
						self.last_trades[pair],
						self.last_price_15m[pair],
						self.last_price_1h[pair],
						self.last_price_4h[pair],
						self.last_price_1d[pair],
						self.last_price_3d[pair],
						pair
					))
				BANCO_DADOS.update_col('binance', SQL_PRICES, datas, pool)
				sleep(10)
	#

class Okx(Stream):
	url_rest_api = 'https://www.okx.com'
	url_wss_api  = 'wss://ws.okx.com:8443/ws/v5/public'
	ticker_24h = True
	########
	price_current = {}
	last_price_15m = {}
	last_price_1h  = {}
	last_price_4h  = {}
	last_price_1d  = {}
	last_price_2d  = {}
	########
	def __init__(self):
		super().__init__(self.on_open, self.on_message, 'okx')
		self.__pares = self.buscar_pares()
		self.start_wss([self.url_wss_api])
		sleep(5)
		Thread(target=self._update_pares, args=()).start()
	def on_open(self, ws):
		print('[!] Websocket aberto')
		if not self.__pares:
			return
		ws.send(dumps({ "op": "subscribe", "args": self.__pares }))
	def on_message(self, ws, msg):
		msg = loads(msg)
		Thread(target=self.__message, args=(msg,)).start()
	def __message(self, msg):
		channel = msg["arg"]["channel"]
		symbol = msg["arg"]["instId"].replace('-SWAP','')
		####
		if 'data' not in msg.keys():
			return
		####
		data = msg["data"][0]
		if 'candle' in channel:
			timeframe = channel.replace('candle','').lower()
			####
			first = float(data[1])
			last = float(data[4])
			change = round(((last-first)/first)*100,2)
			####
			if timeframe == '15m':
				self.price_current[symbol] = round(last,2)
				self.last_price_15m[symbol] = change
			elif timeframe == '1h':
				self.last_price_1h[symbol] = change
			elif timeframe == '4h':
				self.last_price_4h[symbol] = change
			elif timeframe == '2d':
				self.last_price_2d[symbol] = change
			####
		else:
			first = float(data['open24h'])
			last = float(data['last'])
			####
			change = round(((last-first)/first)*100,2)
			self.last_price_1d[symbol] = change
	def buscar_pares(self):
		url = self.url_rest_api + '/api/v5/public/instruments?instType=SWAP'
		content = get(url).json()["data"]
		pares_raw = []
		pares_list = []
		for asset in content:
			if 'USDT' != asset["settleCcy"] or asset['state'] != 'live':
				continue
			pair = asset["uly"]
			pares_raw.append((pair))
			###
			self.price_current[pair] = 0
			self.last_price_15m[pair] = 0
			self.last_price_1h[pair] = 0
			self.last_price_4h[pair] = 0
			self.last_price_1d[pair] = 0
			self.last_price_2d[pair] = 0
			###
			for tf in TIMEFRAMES:
				if tf[-1] != 'm':
					tf = tf.upper()
				pares_list.append({ "channel": 'candle'+tf, "instId": pair+'-SWAP' })
			pares_list.append({ "channel": 'tickers', "instId": pair+'-SWAP' })
		## adicionar os pares
		with BANCO_DADOS.conn_thread() as pool:
			BANCO_DADOS.adicionar_pares('okx', pares_raw, pool)
		### thread lsr e oi
		Thread(target=LSR_OI_MNGR.start, args=('okx',)).start()
		return pares_list
	def _update_pares(self):
		with BANCO_DADOS.conn_thread() as pool:
			pares = [c[0] for c in BANCO_DADOS.query('SELECT par FROM okx', pool, False)]
			while True:
				datas = []
				for pair in pares:
					datas.append((
						self.price_current[pair],0,
						self.last_price_15m[pair],
						self.last_price_1h[pair],
						self.last_price_4h[pair],
						self.last_price_1d[pair],
						self.last_price_2d[pair],
						pair
					))
				BANCO_DADOS.update_col('okx', SQL_PRICES, datas, pool)
				sleep(10)

class Bybit(Stream):
	url_rest_api = 'https://api.bybit.com'
	url_wss_api  = 'wss://stream.bybit.com/realtime_public'
	ticker_24h = True
	########
	queue_list_bybit = {}
	lasts_prices_24h = {}
	dict_tframe= {'15':'15m', '60':'1h', '240':'4h', 'D':'1d'}
	def __init__(self):
		super().__init__(self.on_open, self.on_message, 'bybit')
		self.__pares = self.buscar_pares()
		self.start_wss([self.url_wss_api])
		sleep(5)
		Thread(target=self._update_pares, args=()).start()
	def on_open(self, ws):
		print('[!] Websocket aberto')
		if not self.__pares:
			return
		ws.send(dumps({ "op": "subscribe", "args": self.__pares }))
	def on_message(self, ws, msg):
		msg = loads(msg)
		Thread(target=self.__message, args=(msg,)).start()
	def __message(self, msg):
		try:
			timeframe,par = msg['topic'].split('.')[1:]
			timeframe = self.dict_tframe[timeframe]
			data = msg['data'][0]
			###
			first = float(data['open'])
			last  = float(data['close'])
			change= round(((last-first)/first)*100,2)
			###
			if timeframe == '1d' and int(data['end']) % 172800 == 0:
				self.lasts_prices_24h[par].append(last)
			###
			prices_48h = self.lasts_prices_24h[par]
			if len(prices_48h) == 2:
				change_48h = round(((prices_48h[1]-prices_48h[0])/prices_48h[0])*100,2)
			else:
				change_48h = 0
			###
			self.queue_list_bybit[par]['price_'+timeframe] = change
			self.queue_list_bybit[par]['price_2d'] = change_48h
			###
			if timeframe == '15m':
				self.queue_list_bybit[par]['price'] = round(last,2)
		except KeyError:
			#print(msg)
			pass
	def buscar_pares(self):
		url = self.url_rest_api + '/v2/public/symbols'
		content = get(url).json()["result"]
		pares_raw = []
		pares_list = []
		for asset in content:
			if 'USDT' != asset["quote_currency"]:
				continue
			par = asset["name"]
			pares_raw.append((par,))
			self.queue_list_bybit[par] = {}
			self.lasts_prices_24h[par] = deque(maxlen=2)
			###
			pares_list.append("candle.15."+par) # 15m
			pares_list.append("candle.60."+par) # 1H
			pares_list.append("candle.240."+par) # 4H
			pares_list.append("candle.D."+par) # 1d
		## adicionar os pares
		with BANCO_DADOS.conn_thread() as pool:
			BANCO_DADOS.adicionar_pares('bybit', pares_raw, pool)
		### thread lsr e oi
		Thread(target=LSR_OI_MNGR.start, args=('bybit',)).start()
		return pares_list
	def _update_pares(self):
		with BANCO_DADOS.conn_thread() as pool:
			while True:
				datas = []
				for par in list(self.queue_list_bybit.keys()):
					data = []
					for key in FILTROS_COMUNS:
						try:
							val = self.queue_list_bybit[par][key]
						except KeyError:
							val = 0
						data.append(val)
					datas.append(tuple(data+[par]))
				BANCO_DADOS.update_col('bybit', SQL_PRICES, datas, pool)
				sleep(10)

