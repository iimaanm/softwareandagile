from flask import Flask
from routes.main import main_bp
from db import init_db
import config

app = Flask(__name__)

app.secret_key = config.SECRET_KEY

app.config['DATABASE'] = config.DATABASE

init_db()

app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)
