from app import app, encoder, helper, mailTrigger
import logging
import flask
from flask import request, jsonify
import json
import time
import base64
import boto3
#import pdfkit
import os
from weasyprint import HTML

import requests
# app = flask.Flask(__name__)
# app.config["DEBUG"] = True

logging.basicConfig(level=logging.DEBUG)

session = boto3.Session(
aws_access_key_id='ASIAVBLO43SBNQ4VI5TV',
aws_secret_access_key='r4v5eJl1ezKJ15l051/EJoUMrsvSwU3U2iKwhZ7J',
aws_session_token='FwoGZXIvYXdzECUaDBoHhBEEIAiIwe9viyK+AXdgr7e+Q6k5v6BMvrqYMvGb0DzJSWJNtzTfnBkWG/EJQqAWbsXUsugQ5y/I4SmKrq/UuMbGxjk4eWF3D3//UAmx+gUQdmyTT7iKR33bhoA96UfqrUHVu83nwF3Vl7YGZ7Wsjy8m7qO3+/Gup350pLBBKLoY0INYOAi7lj/psa7mwUqoYeRKLGFoXx2gLJIeKpS6M5vxZV9FPp/lwQFR4bHE0U4LIcRHhScSruKgYGutMSkR0SjhZ845eAX3jDYooMSO9AUyLWbCoEycvfxFgLFFtZ3fzxwzo7hCBl0AeittSyUaXa7ckPrHKqF0Y/85t2Gxng==',
region_name='us-east-1')

dynamodb = session.resource('dynamodb')

table = dynamodb.Table('Booking')
table2 = dynamodb.Table('Card_detail')
host_URL = "http://project-alb-1382584841.us-east-1.elb.amazonaws.com"
# host_URL = "http://localhost:5001"
def b64decoding(value,requestObj=None):
        return base64.b64decode(value).decode("ascii")

def getDataFromRequest(dataObj,keyValue,requestObj=None):
    if dataObj is not None:
        return base64.b64decode(dataObj.get(keyValue)).decode("ascii")
    else:
        return base64.b64decode(request.args.get(keyValue)).decode("ascii")

@app.route('/booking')
def health_check():
    # mailTrigger.sendEmail("t.karthikk95@gmail.com","Test","Test")
    return "booking"

@app.route('/bookticket' , methods=['POST'])
def book_ticket():
    response_json = {}
    response_json["message"] = "error"
    global host_URL
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
        passenger_count = getDataFromRequest(dataObj=data, keyValue="count")
        ##
        payment_info = data.get("payment_info")
        ######## nested attribute of payment_info#######
        card_number = getDataFromRequest(dataObj=payment_info,keyValue="card_number")
        expiry = getDataFromRequest(dataObj=payment_info,keyValue="expiry")
        cvv = getDataFromRequest(dataObj=payment_info,keyValue="cvv")
        app.logger.debug(cvv)

        validation_response = requests.post(host_URL + "/user", json={"email": data.get("email")}, headers={"token": request.headers['token']})
        # app.logger.debug(validation_response.json())
        validation_response = validation_response.json()
        if validation_response["message"] == "ok":
            response_json["message"] = "ok"
        else:
            return json.dumps(response_json)
        # ##
        # TODO: call payment API
        payment_request_json = {}
        payment_request_json["name"] = name_on_card
        payment_request_json["expiry"] = expiry
        payment_request_json["card_number"] = card_number
        payment_request_json["cvv"] = cvv
        payment_response = requests.post(host_URL+"/payment",json=payment_request_json)
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
        ##
        try:
            fp = open("TicketTemplate.html", "r")
            tableTempl = fp.read()
            fp.close()
            ##
            tableTempl = tableTempl.replace("{FROM_PLACE}", frm)
            tableTempl = tableTempl.replace("{TO_PLACE}", to)
            tableTempl = tableTempl.replace("{DATE}", date )
            tableTempl = tableTempl.replace("{PRICE}", price)
            tableTempl = tableTempl.replace("{COUNT}", passenger_count)
            ##
            app.logger.debug(tableTempl)
            attachmentName = str(tempid)+".pdf"
            # pdfkit.from_string(tableTempl,"./app/"+attachmentName)
            HTML(string=tableTempl).write_pdf('./app/' + attachmentName)
            mailTrigger.sendEmail(email,"Ticket Confirmation","Your Ticket is confirmed and is attached",attachmentName)
            os.remove("./app/"+attachmentName)
        except Exception as e:
            app.logger.debug("File error")
            app.logger.debug(e)

    except Exception as e:
        app.logger.debug("Error")
        app.logger.debug(e)
        response_json["message"] = "error"

    return json.dumps(response_json)

@app.route('/bookticket/carddetails' , methods=['GET'])
def card_details():
    response_json = {}
    response_json["message"] = "error"
    global host_URL
    try:
        app.logger.debug(request)
        # data = request.get_json()
        # app.logger.debug(email)
        email = getDataFromRequest(dataObj=None, keyValue="email", requestObj=request)
        app.logger.debug(email)
        # email = b64decoding(email)
        validation_response = requests.post(host_URL + "/user", json={"email": request.args.get("email")}, headers={"token": request.headers['token']})
        validation_response = validation_response.json()
        if validation_response["message"] == "ok":
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
