from app import app, encoder, helper
import logging
import flask
from flask import request, jsonify
from datetime import datetime
import json
import time
import base64
import boto3
from boto3.dynamodb.conditions import Key, Attr
from random import randint

# app = flask.Flask(__name__)
# app.config["DEBUG"] = True

logging.basicConfig(level=logging.DEBUG)

session = boto3.Session(
aws_access_key_id='ASIAVBLO43SBMEXMSHED',
aws_secret_access_key='N8ZF10DW5tsqqdOj4m3Cw/bi4+CJGmE5ZJpb1/p6',
aws_session_token='FwoGZXIvYXdzELH//////////wEaDJ4EyeiUyGnrZfQA0yK+Abz2EORAR4U5FYplppdRmDoR2kCEtOYt9wRRVIMEE4Z/36v8YPfBnnaT1g7F3K7hJ5wu7w1grEbzwlXMyXS4iU3HBIIHBkp/WElAOL5wLHt5Vd4ejlpSVzYMaGK/Mv7MVpk7PGgvL8KNJSfZrzHvjr+9uhYZip5auPrYLKSgHms9CL7h/7fBgwQCvRSac6IWtYtpO6fDg4E/Lxj9IeTrMT622pFJAv7TEyfOYtPQMA0Py9lg+tIKbd/9TOUvSzAoju308wUyLb5SUOdN1TUpHpBLxljqhOlFQfYGV8tzWMsJ0ZfleHats+HrO540BSRsmbE4Cg==',
region_name='us-east-1')

dynamodb = session.resource('dynamodb')

table = dynamodb.Table('Booking')
table2 = dynamodb.Table('Card_detail')

def b64decoding(value,requestObj=None):
        return base64.b64decode(value).decode("ascii")

def getDataFromRequest(dataObj,keyValue,requestObj=None):
    if dataObj is not None:
        return base64.b64decode(dataObj.get(keyValue)).decode("ascii")
    else:
        return base64.b64decode(request.args.get(keyValue)).decode("ascii")

@app.route('/bookticket' , methods=['POST'])
def book_ticket():
    response_json = {}
    response_json["message"] = "error"
    global temp_booking_id
    try:
        app.logger.debug(request)
        data = request.get_json()

        # app.logger.debug("Printing")
        app.logger.debug(data)
        email = getDataFromRequest(dataObj=data,keyValue="email")
        date = getDataFromRequest(dataObj=data,keyValue="date")
        price = getDataFromRequest(dataObj=data,keyValue="price")
        frm = getDataFromRequest(dataObj=data,keyValue="from")
        to = getDataFromRequest(dataObj=data,keyValue="to")
        name_on_card = getDataFromRequest(dataObj=data,keyValue="name")
        ##
        payment_info = data.get("payment_info")
        ######## nested attribute of payment_info#######
        card_number = getDataFromRequest(dataObj=payment_info,keyValue="card_number")
        app.logger.debug(card_number)
        card_number = helper.encryptValue(card_number)
        app.logger.debug(card_number)
        expiry = getDataFromRequest(dataObj=payment_info,keyValue="expiry")
        expiry = helper.encryptValue(expiry)
        app.logger.debug(expiry)
        cvv = getDataFromRequest(dataObj=payment_info,keyValue="cvv")
        app.logger.debug(cvv)

        if encoder.check_validity_token(request.headers['token'],email):
            response_json["message"] = "ok"
        else:
            return json.dumps(response_json)
        ##
        # TODO: call payment API
        ##
        tempid = int(time.time()*1000.0)
        table.put_item(
            Item={
                'ID' : tempid, 
                'email' : email,
                'date' : date,
                'price' : price,
                'from': frm,
                'to': to,
            }
        )

        app.logger.debug(name_on_card)
        app.logger.debug(card_number)
        app.logger.debug(expiry)

        table2.put_item(
            Item={
                'Email' : email,
                'Name' : name_on_card,
                'Card' : card_number,
                'Expiry' : expiry,
            }
        )

    except Exception as e:
        app.logger.debug("Error")
        app.logger.debug(e)
        response_json["message"] = "error"
    
    return json.dumps(response_json)

@app.route('/bookticket/carddetails/<email>' , methods=['GET'])
def card_details(email):
    response_json = {}
    response_json["message"] = "error"
    try:
        app.logger.debug(request)
        # data = request.get_json()
        app.logger.debug(email)
        email = b64decoding(email)
        if encoder.check_validity_token(request.headers['token'],email):
            response_json["message"] = "ok"
        else:
            return json.dumps(response_json)

        response = table2.get_item( Key={
                'Email': email
            })

        if 'Item' in response:
            item = response['Item']
            response_json["card_number"] = helper.decryptValue(item['Card'].value)
            response_json["expiry"] = helper.decryptValue(item['Expiry'].value)
            response_json["name"] = item['Name']

    except Exception as e:
        app.logger.debug(e)
        response_json["message"] = "error"
            
    return jsonify(response_json)
