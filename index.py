
from json import dumps
from alt._db import DB
from alt._lsr_oi import LSR_OI
from alt._stream import Binance, Okx, Bybit, Thread
from flask import Flask, request, render_template, redirect

POOL = None
DATABASE = None
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def pagina_principal():
	if not request.args.get('exchange'):
		return redirect('/?exchange=binance')
	exchange = request.args.get('exchange')
	###
	if exchange == 'binance':
		tf_2d_or_3d = '3D'
	else:
		tf_2d_or_3d = '2D'
	###
	return render_template('index.html', exchange_name=exchange.upper(), tf_2d_or_3d=tf_2d_or_3d)

@app.route('/api')
def pagina_api():
	if not request.args.get('exchange') or not request.args.get('orderby') or not request.args.get('ordem'):
		return dumps({'tops':[], 'alts':[]})
	###
	exchange = request.args.get('exchange')
	orderby  = request.args.get('orderby')
	ordem    = request.args.get('ordem')
	###
	result = DATABASE.dump_exchange(exchange, orderby, ordem, POOL)
	return dumps(result)

@app.route('/calculadora')
def pagina_calculadora():
	return render_template('calculadora.html')

if '__main__' == __name__:
	DATABASE = DB(True)
	POOL = DATABASE.conn_thread()
	###
	Thread(target=Binance, args=()).start()
	Thread(target=Okx, args=()).start()
	Thread(target=Bybit, args=()).start()
	####
	app.run('0.0.0.0', port=5000, debug=False, threaded=False)
















