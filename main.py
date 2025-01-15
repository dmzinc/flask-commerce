from flask import Flask, request, jsonify
import json
from user.user import User

app = Flask(__name__)

with open('data/users.json', 'r') as file:
        users = json.load(file)
        users['users'] = [User(**user) for user in users['users']]

@app.route("/")
def home():
    return {'reply': 'Hello World'}

@app.route('/users', methods=['GET'])
def get_user_by_id():
    id = request.args.get('id', default = 1, type = int)
    result = [user.to_dict() for user in users['users'] if int(user.id) == id]
    return jsonify(result)

@app.route("/users", methods=['GET'])
def get_users():
    return jsonify([user.to_dict() for user in users['users']])

@app.route("/users", methods=['POST'])
def store_user():
    data = User(**request.get_json())
    users['users'] += [data]
    to_write = [user.to_dict() for user in users['users']]
    with open('data/users.json', 'w') as file:
         json.dump({'users': to_write}, file)

    return str(data), 201


if __name__ == '__main__':
    app.run(debug=True)
