from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

import ATSmodule

app = Flask(__name__)
api = Api(app)

users = MongoClient("mongodb://db:27017").SimilarityDB["Users"]

def UserExist(username):
    if users.find({"Username":username}).count() == 0:
        return False
    else:
        return True

def verifyPw(username, password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "Username":username
    })[0]["Tokens"]
    return tokens

def make_json_response(status, msg=None, **kwargs):
    retJson = {"status": status}
    if msg is not None:
        retJson["msg"] = msg
    retJson.update(kwargs)
    return jsonify(retJson)

class Register(Resource):
    def post(self):
        # get posted data by the user
        postedData = request.get_json()
        username = postedData.get("username")
        password = postedData.get("password") #"123xyz"

        if UserExist(username):
            return make_json_response(301, 'Invalid Username')

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        # Store username and pw into the database
        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Tokens":6
        })

        return make_json_response(200, "You successfully signed up for the API")

class Detect(Resource):
    def post(self):
        # get the posted data
        postedData = request.get_json()

        #Step 2 read the data
        username = postedData.get("username")
        password = postedData.get("password")
        text1 = postedData.get("text1")
        text2 = postedData.get("text2")

        if not UserExist(username):
            return make_json_response(301, "Invalid Username")
        #Step 3 verify the username pw match
        correct_pw = verifyPw(username, password)

        if not correct_pw:
            return make_json_response(302, "Incorrect Password")
        #Step 4 Verify user has enough tokens
        num_tokens = countTokens(username)
        if num_tokens <= 0:
            return make_json_response(303, "You are out of tokens, please refill!")

        #Calculate edit distance between text1, text2
        import spacy
        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2 = nlp(text2)

        ratio = text1.similarity(text2)

        # Take away 1 token from user
        current_tokens = countTokens(username)
        users.update({
            "Username":username
        }, {
            "$set":{
                "Tokens":current_tokens-1
                }
        })

        return make_json_response(200, "Similarity score calculated successfully", ratio=ratio)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData.get("username")
        password = postedData.get("admin_pw")
        refill_amount = postedData.get("refill")

        if not UserExist(username):
            return make_json_response(301, "Invalid Username")

        correct_pw = "abc123"
        if not password == correct_pw:
            return make_json_response(304, "Invalid Admin Password")

        # MAKE THE USER PAY!
        users.update({
            "Username":username
        }, {
            "$set":{
                "Tokens":refill_amount
                }
        })

        return make_json_response(200, "Refilled successfully")


api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')


if __name__=="__main__":
    app.run(host='0.0.0.0')
