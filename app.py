import asyncio
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from api.auth import auth_bp
from api.user import user_bp
from linebotApi.linebotApi import line_bot_bp
from utils.websocket_server import start_websocket_server

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# 註冊藍圖
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(line_bot_bp, url_prefix='/linebot')


def run_flask():
	app.run(debug=False, use_reloader=False)


async def main():
	# 啟動 WebSocket 伺服器
	await asyncio.gather(asyncio.to_thread(run_flask), start_websocket_server())


if __name__ == '__main__':
	asyncio.run(main())
