# Item Catalog App

## Purpose:
This app is used for cataloguing items within preset categories.  Users can view all items but can only edit their own items.  Only users that are logged in can create new items.

## Prerequisites
* Python 2 	
* Vagrant 
* SQLAlchemy
* Flask

## Replicating results:

To set up database simply type:

		$ python database_setup.py
		$ python populate_database.py
		$ python app.py

In addition to setting up User, Category, and  Item tables, these commands populate the database with seven categories, one user, and one item created by that user.

To view the app simply open a browser and go to "localhost:5000".  There you can sign in with gmail and operate the lists in the intuitive manner outlined in the project rubric.

## JSON

JSON objects can be found for any item at /category_name/item_name/JSON.  For example, /Breathe/Bananas/JSON returns the full JSON description of the Bananas item in the Breathe category.


Authors

Marcelo Antunes


