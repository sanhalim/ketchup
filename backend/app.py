from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy.orm
from cockroachdb.sqlalchemy import run_transaction
from datetime import datetime

app = Flask(__name__, static_url_path="")
api = Api(app)

app.config.from_pyfile('hello.cfg')
db = SQLAlchemy(app)
sessionmaker = sqlalchemy.orm.sessionmaker(db.engine)


class Todo(db.Model):
    #example model from tutorial
    __tablename__ = 'todos'
    id = db.Column('todo_id', db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    text = db.Column(db.String)
    done = db.Column(db.Boolean)
    pub_date = db.Column(db.DateTime)

    def __init__(self, title, text):
        self.title = title
        self.text = text
        self.done = False
        self.pub_date = datetime.utcnow()


class EmotionTranslater(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('response', type=str, required=True,
                                   help='No response provided',
                                   location='json')
        super(EmotionTranslater, self).__init__()

    def get(self, id):
        #make a database call to cockroach db to
        return {}

    def post(self, id):
        args = self.reqparse.parse_args()
        return {}, 201

api.add_resource(EmotionTranslater, '/api/emotion/<int:id>', endpoint='tasks')


if __name__ == '__main__':
    app.run(debug=True)
