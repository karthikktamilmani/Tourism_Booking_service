from app import app, encoder, helper
import logging
import flask
from flask import request, jsonify
import json
import time
import base64
import boto3
import requests
# app = flask.Flask(__name__)
# app.config["DEBUG"] = True

logging.basicConfig(level=logging.DEBUG)

session = boto3.Session(
aws_access_key_id='ASIAVBLO43SBP7CW4HXJ',
aws_secret_access_key='fOowJ3EbLbn5UHnGiixyYD4fSp+RhVgQgjhQt9w1',
aws_session_token='FwoGZXIvYXdzELP//////////wEaDHAciCLtI3ILlKrQayK+AVAevU8CTHnA/R1jo2xyF/Sk2btRKRGJ5hW7YHuFn5/XyPQn45HwEZkMhrauclZRJze/wgaBWa8kguKFyorU5+Y9fN3JrOBAidQ7esx4HGxlFx+aoctxF5O7GF3TETT93qhiLkeManyM4IZqX0bSIZg+xGvv7oU1TyXf9PtVZbZrcoxxe5Caf5rGOVoIixqpSKW6ILpMYr4FuGkPufJGNGTvBLYPC8yqIxlHDn4MYVS2bH4OjUfbaB7aSSz/vUAoo6b18wUyLWW0KjeqtGd8XkjqDkDNGRfgbxqTHMZpnmrsrIY+8maEWHBQZRTnYukSRqOhrw==',
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
        expiry = getDataFromRequest(dataObj=payment_info,keyValue="expiry")
        cvv = getDataFromRequest(dataObj=payment_info,keyValue="cvv")
        app.logger.debug(cvv)

        # if encoder.check_validity_token(request.headers['token'],email):
        #     response_json["message"] = "ok"
        # else:
        #     return json.dumps(response_json)
        ##
        # TODO: call payment API
        payment_request_json = {}
        payment_request_json["name"] = name_on_card
        payment_request_json["expiry"] = expiry
        payment_request_json["card_number"] = card_number
        payment_request_json["cvv"] = cvv
        payment_response = requests.post("http://localhost:5002/payment",json=payment_request_json)
        app.logger.debug(payment_response)
        ##
        card_number = helper.encryptValue(card_number)
        expiry = helper.encryptValue(expiry)
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
