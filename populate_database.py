#!/bin/sh
from flask import Flask, render_template, flash
from flask import session as login_session

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Item, User, Base 

engine = create_engine('sqlite:///ItemCatalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#add sample categories to the database
sampleCats = {"Sleep", "Eat", "Move", "Breathe", "Play", "Think", "Feel"}
for cat in sampleCats:
    newCat = Category(name=cat)
    session.add(newCat)

#add sample user
sampleUser = User(email="jd@gmali.com", name="Joe Doe", picture="XXY")
session.add(sampleUser)

cat_id = session.query(Category).first().id
user_id = session.query(User).first().id
sampleItem = Item(name="Bananas", user_id=user_id, category_id=cat_id, description="Best food ever!")
session.add(sampleItem)

session.commit()

