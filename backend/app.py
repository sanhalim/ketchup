from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy.orm
from cockroachdb.sqlalchemy import run_transaction
from datetime import datetime

app = Flask(__name__, static_url_path="")
api = Api(app)

app.config.from_pyfile('ketchup.cfg')
db = SQLAlchemy(app)
sessionmaker = sqlalchemy.orm.sessionmaker(db.engine)

class CheckIn(db.Model):
    #example model from tutorial
    __tablename__ = 'daily_checkin'
    id = db.Column('checkin_id', db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    text = db.Column(db.String)
    sentiment = db.Column(db.Float)
    emotion = db.Column(db.String)
    date = db.Column(db.DateTime)

    def __init__(self, user_id, text, sentiment, emotion="None"):
        self.user_id = user_id
        self.text = text
        self.sentiment = sentiment
        self.emotion = emotion
        self.date = datetime.utcnow()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    children = db.relationship("CheckIn")

    def __init__(self, name):
        self.name = name

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
