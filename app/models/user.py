from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid

def get_user_by_email(db: Session, email: str):
    """"
    Finds a user in the database by their email address. Returns the user record if found, or None if not found.

    """

    query = text("SELECT * FROM users WHERE email = :email")
    return db.execute(query, {"email": email}).mappings().fetchone()

def get_user_by_id(db: Session, user_id: str):
    """"
    Finds a user in the database by their unique ID. Returns the user record if found, or None if not found.
    """

    query = text("SELECT * FROM users WHERE user_id = :user_id")
    return db.execute(query, {"user_id": user_id}).mappings().fetchone()

def create_user(db: Session, full_name: str, email: str, hashed_password: str, role: str):
    """
    Insert a new user into the database with the provided full name, email, hashed password, and role.
    The user ID is generated as a UUID string. Returns the created user record.
    """
    user_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO users (user_id, full_name, email, password_hash, role)
        VALUES (:user_id, :full_name, :email, :password_hash, :role)
    """)
    db.execute(query, {
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "password_hash": hashed_password,
        "role": role
    })
    db.commit()
    return get_user_by_id(db, user_id)

def get_all_managers(db: Session):
    """
    Return All users with the role of "manager" from the database. Returns a list of user records.
    """
    query = text("SELECT * FROM users WHERE role = 'manager'")
    return db.execute(query).mappings().all()

def get_all_employees(db: Session):
    """
    Return All users with the role of "employee" from the database. Returns a list of user records.
    """
    query = text("SELECT * FROM users WHERE role = 'employee'")
    return db.execute(query).mappings().all()

def delete_user(db: Session, user_id: str):
    """
    Deletes a user from the database based on their unique ID. Returns True if the user was successfully deleted, or False if the user was not found.
    """
    query = text("DELETE FROM users WHERE user_id = :user_id")
    result = db.execute(query, {"user_id": user_id})
    db.commit()
    return result.rowcount > 0

def update_user(db: Session, user_id: str, full_name: str = None, email: str = None, hashed_password: str = None, role: str = None):
    """
    Updates a user's information in the database based on their unique ID. Only the provided fields will be updated. Returns the updated user record if successful, or None if the user was not found.
    """
    fields = []
    params = {"user_id": user_id}

    if full_name is not None:
        fields.append("full_name = :full_name")
        params["full_name"] = full_name
    if email is not None:
        fields.append("email = :email")
        params["email"] = email
    if hashed_password is not None:
        fields.append("password_hash = :password_hash")
        params["password_hash"] = hashed_password
    if role is not None:
        fields.append("role = :role")
        params["role"] = role

    if not fields:
        return get_user_by_id(db, user_id)

    query = text(f"UPDATE users SET {', '.join(fields)} WHERE user_id = :user_id")
    db.execute(query, params)
    db.commit()

    return get_user_by_id(db, user_id)


def get_all_clients(db: Session):
    """
    Returns all active clients.
    Used when creating a draft (writer must pick a client).
    """
    query = text("""
        SELECT client_id, client_name, timezone
        FROM   clients
        WHERE  active_status = 1
        ORDER BY client_name ASC
    """)
    result = db.execute(query)
    return result.mappings().all()