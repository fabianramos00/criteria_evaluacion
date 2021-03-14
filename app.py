from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from scripts import visibility
from flask import request

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:root1@localhost/criteria'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    return visibility.execute(request.get_json())

if __name__ == '__main__':
    app.run(debug=True)
