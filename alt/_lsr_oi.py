

from time import sleep
from requests import get

try:
	from alt._db import DB, FILTROS_INDCTR, SQL_INDCTR
except ModuleNotFoundError:
	from _db import DB, FILTROS_INDCTR, SQL_INDCTR

_database = DB(False)

class LSR_OI:
	url_exchange = {'binance':'https://fapi.binance.com','okx':'https://www.okx.com',
					'ftx':'https://fapi.coinglass.com/api/futures/longShortRate?timeType=3&symbol=',
					'bybit':'https://api.bybit.com'}
	def diff_change(self, arr):
		if len(arr) < 2:
			return 0
		first = float(arr[-2])
		last = float(arr[-1])
		return round(((last-first)/first)*100,2)
	def binance(self, par):
		url_oi = self.url_exchange['binance'] + '/futures/data/openInterestHist'
		url_lsr= self.url_exchange['binance'] + '/futures/data/globalLongShortAccountRatio'
		###
		try:
			content_oi  = get(url_oi, params={'symbol':par, 'period':'15m', 'limit':500}).json()
			if type(content_oi) != list:
				raise ValueError
		except:
			content_oi  = []
		try:
			content_lsr = get(url_lsr, params={'symbol':par, 'period':'15m', 'limit':500}).json()
			if type(content_lsr) != list:
				raise ValueError
		except:
			content_lsr = []
		# OI
		oi_m_15 = [c['sumOpenInterest'] for c in content_oi[-2:]]
		oi_hora_1 = []
		oi_hora_4 = []
		oi_hora_24 = []
		oi_hora_48 = []
		for c in content_oi:
			if c['timestamp'] % 3600000 == 0:
				oi_hora_1.append(c['sumOpenInterest'])
			if c['timestamp'] % 14400000 == 0:
				oi_hora_4.append(c['sumOpenInterest'])
			if c['timestamp'] % 86400000 == 0:
				oi_hora_24.append(c['sumOpenInterest'])
			if c['timestamp'] % 172800000 == 0:
				oi_hora_48.append(c['sumOpenInterest'])
		# LSR
		lsr_m_15 = [c['longShortRatio'] for c in content_lsr[-2:]]
		lsr_hora_1 = []
		lsr_hora_4 = []
		lsr_hora_24 = []
		lsr_hora_48 = []
		for c in content_lsr:
			if c['timestamp'] % 3600000 == 0:
				lsr_hora_1.append(c['longShortRatio'])
			if c['timestamp'] % 14400000 == 0:
				lsr_hora_4.append(c['longShortRatio'])
			if c['timestamp'] % 86400000 == 0:
				lsr_hora_24.append(c['longShortRatio'])
			if c['timestamp'] % 172800000 == 0:
				lsr_hora_48.append(c['longShortRatio'])
		###
		data = {}
		# -> LSR
		data['lsr_15m'] = self.diff_change(lsr_m_15)
		data['lsr_1h']  = self.diff_change(lsr_hora_1)
		data['lsr_4h']  = self.diff_change(lsr_hora_4)
		data['lsr_1d']  = self.diff_change(lsr_hora_24)
		data['lsr_2d']  = self.diff_change(lsr_hora_48)
		# -> Open Interest
		data['oi_15m'] = self.diff_change(oi_m_15)
		data['oi_1h']  = self.diff_change(oi_hora_1)
		data['oi_4h']  = self.diff_change(oi_hora_4)
		data['oi_1d']  = self.diff_change(oi_hora_24)
		data['oi_2d']  = self.diff_change(oi_hora_48)
		try: data['lsr'] = round(float(lsr_m_15[-1]),4)
		except: data['lsr'] = 0
		###
		sleep(1.5)
		###
		return par,data
	def okx(self, par):
		url_oi = self.url_exchange['okx'] + '/api/v5/rubik/stat/contracts/open-interest-volume'
		url_lsr= self.url_exchange['okx'] + '/api/v5/rubik/stat/contracts/long-short-account-ratio'
		###
		try:
			content_oi  = get(url_oi, params={'ccy':par.split('-')[0], 'period':'5m'}).json()["data"]
			if type(content_oi) != list:
				raise ValueError
		except:
			content_oi  = []
		try:
			content_lsr = get(url_lsr, params={'ccy':par.split('-')[0], 'period':'5m'}).json()["data"]
			if type(content_lsr) != list:
				raise ValueError
		except:
			content_lsr = []
		## -> Open Interest
		oi_m_15 = []
		oi_hora_1 = []
		oi_hora_4 = []
		oi_hora_24 = []
		oi_hora_48 = []
		for c in content_oi:
			if int(c[0]) % 900000 == 0:
				oi_m_15.append(c[1])
			if int(c[0]) % 3600000 == 0:
				oi_hora_1.append(c[1])
			if int(c[0]) % 14400000 == 0:
				oi_hora_4.append(c[1])
			if int(c[0]) % 86400000 == 0:
				oi_hora_24.append(c[1])
			'''if int(c[0]) % 172800000 == 0:
				oi_hora_48.append(c[1])'''
		## -> Long Short Ratio
		lsr_m_15 = []
		lsr_hora_1 = []
		lsr_hora_4 = []
		lsr_hora_24 = []
		lsr_hora_48 = []
		for c in content_lsr:
			if int(c[0]) % 900000 == 0:
				lsr_m_15.append(c[1])
			if int(c[0]) % 3600000 == 0:
				lsr_hora_1.append(c[1])
			if int(c[0]) % 14400000 == 0:
				lsr_hora_4.append(c[1])
			if int(c[0]) % 86400000 == 0:
				lsr_hora_24.append(c[1])
		### 48h REST
		try:
			content_oi  = get(url_oi, params={'ccy':par.split('-')[0], 'period':'1H'}).json()["data"]
			if type(content_oi) != list:
				raise ValueError
		except:
			content_oi  = []
		try:
			content_lsr = get(url_lsr, params={'ccy':par.split('-')[0], 'period':'1H'}).json()["data"]
			if type(content_lsr) != list:
				raise ValueError
		except:
			content_lsr = []
		#
		for c in content_oi:
			if int(c[0]) % 172800000 == 0:
				oi_hora_48.append(c[1])
		for c in content_lsr:
			if int(c[0]) % 172800000 == 0:
				lsr_hora_48.append(c[1])
		###
		data = {}
		# -> LSR
		data['lsr_15m'] = self.diff_change(lsr_m_15)
		data['lsr_1h']  = self.diff_change(lsr_hora_1)
		data['lsr_4h']  = self.diff_change(lsr_hora_4)
		data['lsr_1d']  = self.diff_change(lsr_hora_24)
		data['lsr_2d']  = self.diff_change(lsr_hora_48)
		# -> Open Interest
		data['oi_15m'] = self.diff_change(oi_m_15)
		data['oi_1h']  = self.diff_change(oi_hora_1)
		data['oi_4h']  = self.diff_change(oi_hora_4)
		data['oi_1d']  = self.diff_change(oi_hora_24)
		data['oi_2d']  = self.diff_change(oi_hora_48)
		#
		try: data['lsr'] = round(float(lsr_m_15[-1]),4)
		except: data['lsr'] = 0
		#### RATE LIMIT
		sleep(2)
		return par,data
	def bybit(self, par):
		url_oi = self.url_exchange['bybit'] + '/v2/public/open-interest'
		url_lsr= self.url_exchange['bybit'] + '/v2/public/account-ratio'
		###
		try:
			content_oi  = get(url_oi, params={'symbol':par.upper(), 'period':'15min', 'limit':200}).json()["result"]
			if type(content_oi) != list:
				raise ValueError
		except:
			content_oi  = []
		try:
			content_lsr = get(url_lsr, params={'symbol':par.upper(), 'period':'15min', 'limit':200}).json()["result"]
			if type(content_lsr) != list:
				raise ValueError
		except:
			content_lsr = []
		## -> Open Interest
		oi_m_15 = []
		oi_hora_1 = []
		oi_hora_4 = []
		oi_hora_24 = []
		oi_hora_48 = []
		for c in content_oi:
			if int(c['timestamp']) % 900 == 0:
				oi_m_15.append(c['open_interest'])
			if int(c['timestamp']) % 3600 == 0:
				oi_hora_1.append(c['open_interest'])
			if int(c['timestamp']) % 14400 == 0:
				oi_hora_4.append(c['open_interest'])
			if int(c['timestamp']) % 86400 == 0:
				oi_hora_24.append(c['open_interest'])
		## -> LSR
		lsr_m_15 = []
		lsr_hora_1 = []
		lsr_hora_4 = []
		lsr_hora_24 = []
		lsr_hora_48 = []
		for c in content_lsr:
			ls_ratio = round((float(c["buy_ratio"])/float(c["sell_ratio"])),2)
			if int(c['timestamp']) % 900 == 0:
				lsr_m_15.append(ls_ratio)
			if int(c['timestamp']) % 3600 == 0:
				lsr_hora_1.append(ls_ratio)
			if int(c['timestamp']) % 14400 == 0:
				lsr_hora_4.append(ls_ratio)
			if int(c['timestamp']) % 86400 == 0:
				lsr_hora_24.append(ls_ratio)
			ls_ratio = None
		### 48h REST
		try:
			content_oi  = get(url_oi, params={'symbol':par.upper(), 'period':'1d', 'limit':6}).json()["result"]
			if type(content_oi) != list:
				raise ValueError
		except:
			content_oi  = []
		try:
			content_lsr = get(url_lsr, params={'symbol':par.upper(), 'period':'1d', 'limit':6}).json()["result"]
			if type(content_lsr) != list:
				raise ValueError
		except:
			content_lsr = []
		#
		for c in content_oi:
			if int(c['timestamp']) % 172800 == 0:
				oi_hora_48.append(c['open_interest'])
		for c in content_lsr:
			ls_ratio = round((float(c["buy_ratio"])/float(c["sell_ratio"])),2)
			if int(c['timestamp']) % 172800 == 0:
				lsr_hora_48.append(ls_ratio)
		###
		data = {}
		# -> LSR
		data['lsr_15m'] = self.diff_change(lsr_m_15)
		data['lsr_1h']  = self.diff_change(lsr_hora_1)
		data['lsr_4h']  = self.diff_change(lsr_hora_4)
		data['lsr_1d']  = self.diff_change(lsr_hora_24)
		data['lsr_2d']  = self.diff_change(lsr_hora_48)
		# -> Open Interest
		data['oi_15m'] = self.diff_change(oi_m_15)
		data['oi_1h']  = self.diff_change(oi_hora_1)
		data['oi_4h']  = self.diff_change(oi_hora_4)
		data['oi_1d']  = self.diff_change(oi_hora_24)
		data['oi_2d']  = self.diff_change(oi_hora_48)
		###
		try: data['lsr'] = round(float(lsr_m_15[-1]),4)
		except: data['lsr'] = 0
		##
		sleep(2)
		return par,data
	def ftx(self, par):
		_url = self.url_exchange['ftx'] + par
		try:
			content = get(_url).json()['data'][0]['list']
			if type(content) != list:
				raise ValueError
		except:
			content = []
		lsr = 0
		for data in content:
			if data['exchangeName'] == 'FTX':
				lsr = round(data['longRate'] / data['shortRate'],4)
				break
		data = {'lsr':lsr}
		sleep(2)
		return par,data
	def start(self, exchange):
		print('[THREAD] LSR e OI =>',exchange)
		###
		pool = _database.conn_thread()
		if exchange == 'binance':
			pares = [c[0] for c in _database.query('SELECT par FROM binance', pool, False)]
			while True:
				datas = []
				for par in pares:
					_,_data = self.binance(par)
					data = []
					for key in FILTROS_INDCTR:
						data.append(_data[key])
					datas.append(tuple(data+[par]))
				_database.update_col('binance', SQL_INDCTR, datas, pool)
				sleep(10)
		elif exchange == 'okx':
			pares = [c[0] for c in _database.query('SELECT par FROM okx', pool, False)]
			while True:
				datas = []
				for par in pares:
					_,_data = self.okx(par)
					data = []
					for key in FILTROS_INDCTR:
						data.append(_data[key])
					datas.append(tuple(data+[par]))
				_database.update_col('okx', SQL_INDCTR, datas, pool)
				sleep(10)
		elif exchange == 'bybit':
			pares = [c[0] for c in _database.query('SELECT par FROM bybit', pool, False)]
			while True:
				datas = []
				for par in pares:
					_,_data = self.bybit(par)
					data = []
					for key in FILTROS_INDCTR:
						data.append(_data[key])
					datas.append(tuple(data+[par]))
				_database.update_col('bybit', SQL_INDCTR, datas, pool)
				sleep(10)

