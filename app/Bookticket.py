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
aws_access_key_id='ASIAVBLO43SBLOC2JGF4',
aws_secret_access_key='jy++YitQr+3fTUSupaZHymnDvlDBrbT2nx2IMv/3',
aws_session_token='FwoGZXIvYXdzEML//////////wEaDGYV4sUpTrfSytMF5yK+AYLVaEQYnL+fZB9k1qbGT/CZNaE81fxQk9Sg/tEu7ga57h/mDewoY/Qr4TGpOCeVA692GGf1B817YaMwUcP0flDH1ITAu3bv1Kis/5hgPZVPQe5iwJ9LypW2UGhrQrxUcJYA6WEKREDdcbF5tm1+BowBxNdsFnIrMexmtAt+zSHWhS4tXRmjjqr0pmywAdiL0U877UG+a/k8I7h/h14fZotwke7QJC+1MAQd6+hkUVCtQJtH/YBquL0ORlSwLX4ojc/48wUyLf4Ne4J0fCBjXtTN3WqVlo/7V/7nRKRn7NxO8jenk9VO5ZPAxB0EdDXHr8zE1w==',
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

@app.route('/booking')
def health_check():
    return "booking"

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

        if encoder.check_validity_token(request.headers['token'],email):
            response_json["message"] = "ok"
        else:
            return json.dumps(response_json)
        ##
        # TODO: call payment API
        payment_request_json = {}
        payment_request_json["name"] = name_on_card
        payment_request_json["expiry"] = expiry
        payment_request_json["card_number"] = card_number
        payment_request_json["cvv"] = cvv
        payment_response = requests.post("http://project-alb-1382584841.us-east-1.elb.amazonaws.com/payment",json=payment_request_json)
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

@app.route('/bookticket/carddetails' , methods=['GET'])
def card_details():
    response_json = {}
    response_json["message"] = "error"
    try:
        app.logger.debug(request)
        # data = request.get_json()
        # app.logger.debug(email)
        email = getDataFromRequest(dataObj=None, keyValue="email", requestObj=request)
        app.logger.debug(email)
        # email = b64decoding(email)
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
