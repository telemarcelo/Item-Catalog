#!/bin/sh
from flask import Flask, render_template, flash
from flask import session as login_session
from flask import make_response
from flask import request, redirect, jsonify
from flask import Markup
from sqlalchemy import update
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Item, User, Base
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import random
import string
from pprint import pprint

app = Flask(__name__)
flush = False
engine = create_engine(
    'postgresql:///ItemCatalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
APPLICATION_NAME = "Item Catalog"
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Home page: shows all items and all categories


@app.route('/')
def Home():
    all_items = session.query(Item).all()
    all_cats = session.query(Category).all()
    body = Markup(render_template(
        "Home.html", logged=isLogged(),
        items=all_items, cats=all_cats))
    if not isLogged():
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state
        return render_template(
            "SignedOut.html", body=body, STATE=state, CLIENT_ID=CLIENT_ID)
    else:
        return render_template("SignedIn.html",  body=body, info=login_session)

# Category page: shows all categories and items in a certain category


@app.route('/categories/<string:cat_name>')
def ShowCatItems(cat_name):
    print("step 1")
    cat_id = session.query(Category).filter_by(name=cat_name).one().id
    # selects all items in the category
    cat_items = session.query(Item).filter_by(category_id=cat_id).all()
    all_cats = session.query(Category).all()
    body = Markup(render_template(
        "Category.html", logged=isLogged(), category=cat_name,
        items=cat_items, cats=all_cats))
    if not isLogged():
        state = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template(
            "SignedOut.html", body=body, STATE=state, CLIENT_ID=CLIENT_ID)
    else:
        return render_template("SignedIn.html", body=body, info=login_session)

# NewItem page: provides a form for adding new items
# (GET) and code for adding to DB (POST)


@app.route('/newItem', methods=['POST', 'GET'])
def newItem():
    all_cats = session.query(Category).all()
    if request.method == "POST":
        name = request.form['name']
        desc = request.form['description']
        cat = getCategoryID(request.form['category'])
        user = getUserID(login_session['email'])
        # user = 1
        newItem = Item(
            name=name, description=desc, category_id=cat, user_id=user)
        session.add(newItem)
        session.commit()
        return Home()
    else:
        if isLogged():
            body = Markup(render_template("NewItem.html", cats=all_cats))
            return render_template(
                "SignedIn.html", body=body,  info=login_session)
        return Home()

# ItemDesc page: give the item description
# and option to edit or delete (if logged in)


@app.route('/categories/<string:cat_name>/<string:item_name>')
def ShowItemDesc(cat_name, item_name):
    cat_id = session.query(Category).filter_by(name=cat_name).one().id
    item = session.query(Item).filter_by(
        category_id=cat_id, name=item_name).one()
    isAuthor = False
    if isLogged():
        if item.user_id == getUserID(login_session['email']):
            isAuthor = True
    body = Markup(
        render_template("ItemDesc.html", item=item, isAuthor=isAuthor))
    if not isLogged():
        state = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template(
            "SignedOut.html", body=body, CLIENT_ID=CLIENT_ID, STATE=state)
    else:
        return render_template(
            "SignedIn.html",
            body=body, info=login_session)

# EditItem page: allows the author to change the properties of an existing item


@app.route(
    '/editItem/<string:catName>/<string:itemName>', methods=['POST', 'GET'])
def editItem(catName, itemName):
    all_cats = session.query(Category).all()
    if request.method == "POST":
        print("posted")

        item = session.query(Item).filter(
            Item.name == itemName,
            Item.category_id == getCategoryID(catName),
            Item.user_id == getUserID(login_session['email'])
            ).first()
        item.name = request.form['name']
        item.category_id = getCategoryID(request.form['category'])
        item.description = request.form['description']

        session.add(item)
        session.commit()
        return Home()
    else:
        if isLogged():
            thisItem = session.query(Item).filter(
                Item.name == itemName,
                Item.category_id == getCategoryID(catName),
                Item.user_id == getUserID(login_session['email'])).first()
            body = Markup(
                render_template("EditItem.html", item=thisItem, cats=all_cats))
            return render_template(
                "SignedIn.html", body=body, info=login_session)
        return Home()

# DeleteItem page: allows the author


@app.route(
    '/deleteItem/<string:catName>/<string:itemName>', methods=['POST', 'GET'])
def deleteItem(catName, itemName):
    all_cats = session.query(Category).all()
    if request.method == "POST":
        item = session.query(Item).filter(
            Item.name == itemName,
            Item.category_id == getCategoryID(catName),
            Item.user_id == getUserID(login_session['email'])
            ).first()
        session.delete(item)
        session.commit()
        return Home()
    else:
        if isLogged():
            thisItem = session.query(Item).filter(
                Item.name == itemName,
                Item.category_id == getCategoryID(catName),
                Item.user_id == getUserID(login_session['email'])).first()
            body = Markup(
                render_template(
                    "DeleteItem.html", catName=catName, itemName=itemName))
            return render_template(
                "SignedIn.html", body=body,  info=login_session)
        return Home()

# helper methods


def isLogged():
    return login_session.get('access_token') is not None


def getUserID(userEmail):
    session = DBSession()
    user = session.query(User).filter(User.email == userEmail).one()
    return user.id


def getUserEmail(user_id):
    session = DBSession()
    user = session.query(User).filter(User.id == user_id).one()
    return user.email


def getCategoryID(catName):
    session = DBSession()
    cat = session.query(Category).filter(Category.name == catName).first()
    return cat.id

# json endpoint: item in a category


@app.route('/<string:catName>/<string:itemName>/JSON')
def catItemsJSON(catName, itemName):
    cat_id = getCategoryID(catName)
    cat_items = session.query(Item).filter_by(
        category_id=cat_id, name=itemName).first()
    return jsonify(cat_items=cat_items.serialize)

# login/logout methods
# login to google


@app.route('/gconnect', methods=['POST'])
def gconnect():
    print("gconnect")
    # Validate state token

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return "response"
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object

        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 333)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one
    addUser(login_session)

    output = ''
    output += '<span style="font-size:20 margin:80px">Welcome, '
    output += login_session['username']
    output += '!</span>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 70px; height: 70px;'
    output += ' border-radius: 35px;-webkit-border-radius: '
    output += '35px;-moz-border-radius: 35px;"> '
    # flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect', methods=['POST'])
def gdisconnect():

    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2'
    url += '/revoke?token=%s' % login_session['access_token']
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        print(response)
        return response

# add login information and to session and add user to database if necessary


def addUser(login_session):
    nameInput = login_session['username']
    emailInput = login_session['email']
    pictureInput = login_session['picture']
    userExists = session.query(User).filter(
        User.email == emailInput).scalar() is not None
    if(not userExists):
        newUser = User(email=emailInput, name=emailInput, picture=pictureInput)
        session.add(newUser)
        session.commit()
    users = session.query(User).all()
    return Home()

if __name__ == '__main__':
    app.secret_key = 'FJH9WUWUG0oAyZNAmkpJGsgt'
    # app.debug = True
    app.run(host='0.0.0.0', port=5000)
