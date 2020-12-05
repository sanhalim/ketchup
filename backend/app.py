from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal

app = Flask(__name__, static_url_path="")
api = Api(app)

class EmotionTranslater(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('response', type=str, required=True,
                                   help='No response provided',
                                   location='json')
        super(EmotionTranslater, self).__init__()

    def get(self, id):
        return {}

    def post(self, id):
        args = self.reqparse.parse_args()
        return {}, 201

api.add_resource(EmotionTranslater, '/api/emotion/<int:id>', endpoint='tasks')


if __name__ == '__main__':
    app.run(debug=True)
