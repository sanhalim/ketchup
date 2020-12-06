from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
import sqlalchemy.orm
from cockroachdb.sqlalchemy import run_transaction
from models import CheckIn, db
from sentiment import get_sentiment
from emotion import get_emotion

app = Flask(__name__, static_url_path="")
api = Api(app)
app.config.from_pyfile('ketchup.cfg')
app.app_context().push()
db.init_app(app)
db.create_all()
sessionmaker = sqlalchemy.orm.sessionmaker(db.engine)

class EmotionTranslater(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('text', type=str, required=True,
                                   help='No response provided',
                                   location='json')
        super(EmotionTranslater, self).__init__()

    # ketchup: checkin text from alexa
    def add_checkin_to_db(self, ketchup):
        def callback(session):
            session.add(ketchup)
        run_transaction(sessionmaker, callback)

    # user_id: user id from alexa
    def checkin_by_user(self, user_id):
        def callback(session):
            return session.query(CheckIn).filter_by(user_id=user_id).order_by(CheckIn.date.desc()).limit(10).all()
        run_transaction(sessionmaker, callback)

    # id: user id from alexa
    def get(self, id):
        # ketchup_bottle: all data from that user
        ketchup_bottle = self.checkin_by_user(id)

        # include analysis parameters:
        #   - average sentiment over 2 week period
        #   - most frequent emotion
        #   - average rate of change of sentiment over 2 week period

        return {"most_freq_emotion": "", "average_sentiment": 0}

    def post(self, id):
        args = self.reqparse.parse_args()
        text = args["text"]
        
        # getting sentiment analysis from google nlp api
        annotations = get_sentiment(text)
        sentiment = annotations.document_sentiment.score

        # getting emotion from deepaffects text api
        emotion = get_emotion(text).text

        ketchup = CheckIn(id, text, sentiment, emotion)
        self.add_checkin_to_db(ketchup)
        return jsonify({"emotion": emotion, "sentiment": sentiment})

api.add_resource(EmotionTranslater, '/api/emotion/<int:id>', endpoint='tasks')


if __name__ == '__main__':
    app.run(debug=True)
