"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from pydal.validators import *
from datetime import datetime

@action("index")
@action.uses("index.html", auth, T)
def index():
    user = auth.get_user()
    redirect(URL('dashboard')) if user else redirect(URL('auth/login'))
    return locals()

# Not to be confused with _dashboard
# This is the dashboard with every posts visible to the user
@action("dashboard", method='GET')
@action.uses("index.html", auth.user, T)
def front_page():
    user = auth.get_user()
    cur_user_id = user['id']
    message = ("Hello {first_name}").format(**user) if user else redirect(URL('auth/login'))
    
    cur_manager = get_user_manager(cur_user_id)
    users = get_users_without_self(cur_user_id)
    managed_users = get_managed_users(cur_user_id)
    tasks = db(db.task).select(
        db.task.ALL,
        db.auth_user.first_name,
        db.auth_user.last_name,
        join=db.auth_user.on(db.task.created_by == db.auth_user.id)
    )

    return dict(tasks=tasks, message=message, cur_manager=cur_manager, cur_user_id=cur_user_id, users=users, managed_users=managed_users)

# Helper functions 
def get_users_without_self(user_id):
    users = db(db.auth_user.id != user_id).select().as_list()
    return users
    
def get_user_manager(user_id):
    print("Getting manager")
    managed_user = db(db.managed_users.user_id == user_id).select().first()
    if managed_user:
        manager = db.auth_user(managed_user.manager_id)
        if manager:
            print("Manager is: ", manager)
            return f"{manager.first_name} {manager.last_name}"
    return None

def get_managed_users(manager_id):
    managed_users = db(db.managed_users.manager_id == manager_id).select()
    
    user_info_list = []
    
    for managed_user in managed_users:
        user = db.auth_user(managed_user.user_id)
        if user:
            user_info_list.append({
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}"
            })
    return user_info_list

def convert_to_datetime(task_data):
    if 'deadline' in task_data and task_data['deadline']:
        task_data['deadline'] = datetime.datetime.strptime(task_data['deadline'], '%Y-%m-%dT%H:%M:%S')
    if 'created_on' in task_data and task_data['created_on']:
        task_data['created_on'] = datetime.datetime.strptime(task_data['created_on'], '%Y-%m-%dT%H:%M:%S')
    if 'modified_on' in task_data and task_data['modified_on']:
        task_data['modified_on'] = datetime.datetime.strptime(task_data['modified_on'], '%Y-%m-%dT%H:%M:%S')
           

def print_current_user_info_in_terminal(user_id):
    user = auth.get_user()
    if user:
        user_id = user['id']
        first_name = user['first_name']
        last_name = user['last_name']
        email = user['email']
        print(f"User ID: {user_id}\n")
        print(f"First Name: {first_name}\n")
        print(f"Last Name: {last_name}\n")
        print(f"Email: {email}\n")
    else:
        print("Not logged in.")

# Direct to the task.html page for creating a new task
@action("api/create_task", method=['GET', 'POST'])
@action.uses("task.html", auth.user)
def create_task():
    user = auth.get_user()
    manager = get_user_manager(user['id'])
    data = request.json
    if not data:
        return dict(error="Invalid JSON data (create_task)", manager=manager)
    
    task_id = db.task.validate_and_insert(**data)
    if task_id:
        db.commit()
        return dict(message="Task created", task_id=task_id.id, manager=manager)
    else:
        return dict(error="Validation error (insert)", errors=task_id.errors)

# Retrieve all the users
# Used for the dropdown menu
@action("api/get_users", method='GET')
@action.uses(db, auth.user)
def change_manager(user_id):
    cur_manager = get_user_manager(user_id['id'])
    users = get_users_without_self(user_id['id'])
    return dict(cur_manager=cur_manager, users=users)

# Return current user and manager
@action("api/get_current_user", method="GET")
@action.uses(auth.user)
def get_current_user():
    user = auth.get_user()
    manager = get_user_manager(user["id"])
    user_name = f"{user['first_name']} {user['last_name']}"
    print("username:", user_name)
    return dict(user=user_name, manager=manager)

# Retrieve only tasks, used for loading the initial app
@action("api/get_tasks", method='GET')
@action.uses(db, auth.user)
def get_tasks():
    tasks = db(db.task).select(
        db.task.ALL,
        db.auth_user.first_name,
        db.auth_user.last_name,
        join=db.auth_user.on(db.task.created_by == db.auth_user.id)
    )
    return dict(tasks=tasks)

# Each user can select a manager from the drop down menu 
# Upon click, the manager will be updated in the db
@action("change_manager/<user_id:int>/<manager_id:int>", method='GET')
@action.uses(db, auth.user)
def change_manager(user_id, manager_id):
    record = db(db.managed_users.user_id == user_id).select().first()
    if record:
        db(db.managed_users.user_id == user_id).validate_and_update(manager_id=manager_id)
    else:
        db.managed_users.insert(user_id=user_id, manager_id=manager_id)
    db.commit()

    cur_manager = get_user_manager(user_id)
    print(cur_manager)
    redirect(URL('dashboard'))

    return dict(cur_manager=cur_manager)

# Updates a task
@action('api/save_task/<task_id:int>', method=['PUT'])
@action('api/save_task', method=['POST'])
@action.uses(db, auth.user)
def save_task(task_id=None):
    data = request.json
    if not data:
        return dict(error="Invalid JSON data (save_task)")

    convert_to_datetime(data)
    if task_id:
        task = db.task(task_id)
        if task:
            task.update_record(**data)
            db.commit()
            return dict(message="Task updated", task=task.as_dict())
        else:
            return dict(error="Task not found")

@action("api/search_users", method='GET')
@action.uses(db, auth.user)
def search_users():
    query = request.params.get('query', '')
    if not query:
        users = db(db.auth_user.id).select().as_list()
    else:
        # Perform case-insensitive search for the query
        search_query = f"%{query.lower()}%"
        # Query users that match the search query (first_name or last_name)
        users = db(
            (db.auth_user.first_name.ilike(search_query)) |
            (db.auth_user.last_name.ilike(search_query))
        ).select(db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name).as_list()
        
    return dict(users=users)

@action("api/get_comments/<task_id:int>", method="GET")
@action.uses(db, auth.user)
def get_comments(task_id):
    comments = db(db.comment.task_id==task_id).select(db.task.ALL)
    return dict(comments=comments)

@action("api/add_comment", method=['GET', 'POST'])
@action.uses(db, auth.user)
def add_comment():
    data = request.json
    if not data:
        return dict(error="Invalid JSON data (add_comment)")
    
    cmt_id = db.comment.validate_and_insert(**data)
    if cmt_id:
        db.commit()
        return dict(message="Comment created")
    else:
        return dict(error="Validation error (add_comment)", errors=cmt_id.errors)

@action('api/delete/<task_id:int>', method='DELETE')
@action.uses(db, auth.user)
def delete(task_id):
    user = auth.get_user()
    user_id = user['id']
    task = db(db.task.id == task_id).select().first()
    if not task:
        return dict(error="Failed to delete task, not found in database.")
    if task.created_by == user_id:
        db(db.task.id == task_id).delete()
        db.commit()
        message = "deleted" + str(task_id)
        return dict(message=message)
    if db((db.managed_users.user_id == task.created_by) & (db.managed_users.manager_id == user_id)).count() > 0:
        db(db.task.id == task_id).delete()
        db.commit()
        message = "deleted" + str(task_id)
        return dict(message=message)
    return dict(error="Task found but not deleted.")

# For example:
# api/filter_task?by=status=pending,created_by_self,assigned_to_self,created_by_user=1,assigned_to_user=2
# Where x,y,z could be the following:

# date created (task.created_on)
# deadline (task.deadline)
# status (task.status)
# created by self (user=get.auth_user, db(task.created_by == user['id'])
# assigned to self (user=get.auth_user, db(task.assigned_to == user['id'])
# created by a specific user (maybe use the dropdown menu with the get_user_without_self function)
# assigned to a specific user (maybe use the dropdown menu with the get_user_without_self function)
# created by any managed user
# assigned to any managed user

# @action('api/filter_task', method='GET')
# @action.uses(db, auth.user)
# def filter_task_by_self_or_specific_user():
    # api/filter_task?by=x,y,z
    # filters = request.query.get('by')

    # or api/filter_task with JSON -> filters = request.json.get('status')


@action('api/filter_task', method='GET')
@action.uses(db, auth.user)
def filter_tasks():
    created_by_self = request.params.get("created_by_self", False)
    assigned_to_self = request.params.get("assigned_to_self", False)
    created_by_user = request.params.get("created_by_user", None)
    assigned_to_user = request.params.get("assigned_to_user", None)
    created_by_managed = request.params.get("created_by_managed", None)
    assigned_to_managed = request.params.get("assigned_to_managed", None)

    
    query = db.task.id > 0
    
    if created_by_self.lower() == "true":
        query &= (db.task.created_by == auth.get_user()['id'])
    if assigned_to_self.lower() == "true":
        query &= (db.task.assigned_to == auth.get_user()['id'])
    if created_by_user:
        query &= (db.task.created_by == created_by_user)
    if assigned_to_user:
        query &= (db.task.assigned_to == assigned_to_user)
    if created_by_managed:
        managed_users = get_managed_users(auth.get_user['id'])
        if managed_user_ids:
            query &= (db.task.created_by.belongs(managed_user_ids))
    if assigned_to_managed:
        managed_user_ids = get_managed_users(auth.get_user['id'])
        if managed_user_ids:
            query &= (db.task.assigned_to.belongs(managed_user_ids))

    tasks = db(query).select(
        db.task.ALL,
        db.auth_user.first_name,
        db.auth_user.last_name,
        join=db.auth_user.on(db.task.created_by == db.auth_user.id)
    )
    return dict(tasks=tasks)
    

