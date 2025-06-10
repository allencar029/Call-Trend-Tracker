from flask_app import app
from flask_app.controllers import call_summary

if __name__ == "__main__": #This code runs your server
    app.run(debug=True, port=5002) #you can define what port you want to run on here 