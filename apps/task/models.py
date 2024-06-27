"""
This file defines the database models
"""

from .common import db, Field, auth
from pydal.validators import *

import datetime
### Define your table below

# Get the user's email
def email():
    if auth.current_user:
        return auth.current_user.get('email')
    else:
        print("Email not found in models.py.\n")
        return None

# Get the current time
def time():
    return datetime.datetime.now()

# I'm not sure if this is right, feel free to modify
# Might be more complicated than necessary

# The user can only be managed by one other user 
# The user can manage multiple unique users
db.define_table(
    'managed_users',
    Field('manager_id', 'reference auth_user'),
    Field('user_id', 'reference auth_user', unique=True),
    Field('has_highest_clearance', 'boolean', default=False),
    auth.signature
)

# Task attributes
db.define_table(
    'task',
    Field('title', requires=IS_NOT_EMPTY()),
    Field('description', 'text'),
    Field('deadline', 'datetime'),
    Field('status', default='pending', requires=IS_IN_SET(['pending', 'acknowledged', 'rejected', 'completed', 'failed'])),
    Field('assigned_to', 'reference auth_user'),
    auth.signature
)

# For comments under a specific task
db.define_table(
    'comment',
    Field('task_id', 'reference task'),
    Field('body', requires=IS_NOT_EMPTY()),
    auth.signature
)

db.commit()

