
import pymysql


FILTROS_COMUNS = ('price', 'trades', 'price_15m', 'price_1h', 'price_4h', 'price_1d', 'price_2d')
FILTROS_INDCTR = ('lsr', 'oi_15m', 'oi_1h', 'oi_4h', 'oi_1d', 'oi_2d', 
						'lsr_15m', 'lsr_1h', 'lsr_4h', 'lsr_1d', 'lsr_2d')

SQL_PRICES = 'UPDATE {0} SET price=%s, trades=%s, price_15m=%s, price_1h=%s, price_4h=%s, price_1d=%s, price_2d=%s WHERE par=%s;'
SQL_INDCTR = 'UPDATE {0} SET lsr=%s, oi_15m=%s, oi_1h=%s, oi_4h=%s, oi_1d=%s, oi_2d=%s, lsr_15m=%s, lsr_1h=%s, lsr_4h=%s, lsr_1d=%s, lsr_2d=%s WHERE par=%s;'

DB_NAME = 'analyser'
TBL_NAMES = ('binance','okx','bybit')
DB_USER = 'root'
DB_PASS = ''


class DB:
	def conn_thread(self):
		return pymysql.connect(host='localhost',
                             user=DB_USER,
                             password=DB_PASS,
                             database=DB_NAME,
                             charset='utf8mb4',
                             autocommit=True,
                             cursorclass=pymysql.cursors.Cursor)
	def __init__(self, reset=False):
		if reset:
			self.reset()
	def reset(self):
		pool = self.conn_thread()

		for tbl in TBL_NAMES:
			self.query(f'DROP TABLE IF EXISTS {tbl.lower()};', pool)
			self.query(f'CREATE TABLE {tbl.lower()}(id INT AUTO_INCREMENT PRIMARY KEY, par VARCHAR(30) UNIQUE NOT NULL, price FLOAT DEFAULT 0, lsr FLOAT DEFAULT 0, trades INT DEFAULT 0, price_15m FLOAT DEFAULT 0, oi_15m FLOAT DEFAULT 0, lsr_15m FLOAT DEFAULT 0, price_1h FLOAT DEFAULT 0, oi_1h FLOAT DEFAULT 0, lsr_1h FLOAT DEFAULT 0, price_4h FLOAT DEFAULT 0, oi_4h FLOAT DEFAULT 0, lsr_4h FLOAT DEFAULT 0, price_1d FLOAT DEFAULT 0, oi_1d FLOAT DEFAULT 0, lsr_1d FLOAT DEFAULT 0, price_2d FLOAT DEFAULT 0, oi_2d FLOAT DEFAULT 0, lsr_2d FLOAT DEFAULT 0);', pool)

		pool.close()
	def query(self, text, pool, one=True):
		with pool.cursor() as cursor:
			cursor.execute(text)
			if one:
				data = cursor.fetchone()
			else:
				data = cursor.fetchall()
		return data
	def querymany(self, struct_sql, lista, pool):
		with pool.cursor() as cursor:
			cursor.executemany(struct_sql, lista)
	def adicionar_pares(self, exchange, pares, pool):
		self.querymany(f'INSERT INTO {exchange.lower()}(par) VALUES(%s)', pares, pool)
	def update_col(self, exchange, struct_sql, datas, pool):
		if not datas:
			return
		###
		self.querymany(struct_sql.format(exchange.lower()), datas, pool)
	def dump_exchange(self, exchange, orderby, ordem, pool):
		if exchange.lower() == 'okx':
			top_list = '("BTC-USDT","ETH-USDT")'
		else:
			top_list = '("BTCUSDT","ETHUSDT")'
		filtros = 'par, price, lsr, trades, price_15m, oi_15m, lsr_15m, price_1h, oi_1h, lsr_1h, price_4h, oi_4h, lsr_4h, price_1d, oi_1d, lsr_1d, price_2d, oi_2d, lsr_2d'
		###
		try:
			tops = self.query(f'SELECT {filtros} from {exchange.lower()} WHERE par IN {top_list} ORDER BY {orderby} {ordem}', pool, False)
			alts = self.query(f'SELECT {filtros} from {exchange.lower()} WHERE par NOT IN {top_list} ORDER BY {orderby} {ordem}', pool, False)

			return {'tops':tops, 'alts':alts}
		except:
			return {'tops':[], 'alts':[]}

