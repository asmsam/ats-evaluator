from flask import Flask, jsonify, request, render_template, send_file, make_response
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import fitz  # PyMuPDf to install but fitz to import
import nltk
from dotenv import load_dotenv
import os
import openai

import ATSmodule as ats

# Load API Key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Flask(__name__, template_folder='templates')
api = Api(app)
nltk.download("punkt")

users = MongoClient("mongodb://db:27017").atsDB["Users"]

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

class Index(Resource):
    def get(self):
        return make_response(render_template('index.html', score=None, suggestions=None))

    def post(self):
        return make_response(render_template('index.html', score=None, suggestions=None))
        
class Download(Resource):
    def get(self):
        return send_file("ATS_suggestions.txt", as_attachment=True)

class Register(Resource):
    def post(self):
        # get posted data by the user
        username = request.form.get("username")
        password = request.form.get("password") #"123xyz"

        if UserExist(username):
            return render_template('index.html', score=None, suggestions="Invalid Username: Username already exists")
        if len(password) < 6:
            return render_template('index.html', score=None, suggestions="Invalid Password: Password must be at least 6 characters long")
        if not isinstance(password, str):
            return render_template('index.html', score=None, suggestions="Invalid Password: Password must be a string")
        if not password.isascii():
            return render_template('index.html', score=None, suggestions="Invalid Password: Password must be ASCII characters only")
        if not username.isascii():
            return render_template('index.html', score=None, suggestions="Invalid Username: Username must be ASCII characters only")

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        if not hashed_pw:
            return render_template('index.html', score=None, suggestions="Error: Password hashing failed")

        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })

        return render_template('index.html', score=None, suggestions="You successfully signed up for the API")

class CalcScore(Resource):
    def get(self):
        return render_template('index.html', score=None, suggestions=None)
    
    def post(self):
        # get the posted data from form
        username = request.form.get("username")
        password = request.form.get("password")
        job_desc = request.form.get("job_desc")
        resume_text = None

        if not UserExist(username):
            return render_template('index.html', score=None, suggestions="Invalid Username")
        if not verifyPw(username, password):
            return render_template('index.html', score=None, suggestions="Incorrect Password")
        if countTokens(username) <= 0:
            return render_template('index.html', score=None, suggestions="You are out of tokens, please refill!")

        # Deduct a token
        current_tokens = countTokens(username)
        users.update({"Username": username}, {"$set": {"Tokens": current_tokens - 1}})

        if "resume" in request.files:
            resume_file = request.files["resume"]
            if resume_file.filename.endswith(".pdf"):
                resume_text = ats.extract_text_from_pdf(resume_file)
            else:
                resume_text = resume_file.read().decode("utf-8")
        else:
            resume_text = request.form.get("resume")

        ats_score, suggestions = ats.analyze_resume(job_desc, resume_text)
        return render_template('index.html', score=ats_score, suggestions=suggestions)

class Refill(Resource):
    def post(self):
        username = request.form.get("username")
        password = request.form.get("admin_password")
        refill_amount = request.form.get("refill")

        if not UserExist(username):
            return render_template('index.html', score=None, suggestions="Invalid Username")

        correct_pw = "abc123"
        if not password == correct_pw:
            return render_template('index.html', score=None, suggestions="Invalid Admin Password")

        # MAKE THE USER PAY!
        users.update({
            "Username": username
        }, {
            "$set": {
            "Tokens": refill_amount
            }
        })

        return render_template('index.html', score=None, suggestions="Refilled successfully")


api.add_resource(Register, '/register')
api.add_resource(CalcScore, '/score')
api.add_resource(Refill, '/refill')
api.add_resource(Download, '/download')
api.add_resource(Index, '/')

if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000)
