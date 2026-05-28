from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid

def get_user_by_email(db: Session, email: str):
    """"
    Finds a user in the database by their email address. Returns the user record if found, or None if not found.

    """

    query = text("SELECT * from users where email = :email")
    result = db.execute(query, {"email": email}).fetchone()
    return result._mapped.first() if result else None

def get_user_by_id(db:Session, user_id:str):
    """"
    Finds a user in the database by their unique ID. Returns the user record if found, or None if not found.
    """

    query = text("SELECT * from users where id = :user_id")
    result = db.execute(query, {"user_id": user_id}).fetchone()
    return result._mapped.first() if result else None

def create_user(db: Session, full_name: str, email: str, hashed_password:str, role:str):
    """
    Insert a new user into the database with the provided full name, email, hashed password, and role.
    The user ID is generated as a UUID string. Returns the created user record.
    """
    user_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO users (id, full_name, email, hashed_password, role)
        VALUES (:id, :full_name, :email, :hashed_password, :role)
        RETURNING *
    """)
    db.execute(query, {
        "id": user_id,
        "full_name": full_name,
        "email": email,
        "hashed_password": hashed_password,
        "role": role
    })
    db.commit()
    return user_id

def get_all_managers(db:Session):
    """
    Return All users with the role of "manager" from the database. Returns a list of user records.
    """
    query = text("SELECT * FROM users WHERE role = 'manager'")
    result = db.execute(query)
    return result.mappings().all()
    

def get_all_employees(db:Session):
    """
    Return All users with the role of "employee" from the database. Returns a list of user records.
    """
    query = text("SELECT * FROM users WHERE role = 'employee'")
    result = db.execute(query)
    return result.mappings().all()

def delete_user(db: Session, user_id: str):
    """
    Deletes a user from the database based on their unique ID. Returns True if the user was successfully deleted, or False if the user was not found.
    """
    query = text("DELETE FROM users WHERE id = :user_id")
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
        fields.append("hashed_password = :hashed_password")
        params["hashed_password"] = hashed_password
    if role is not None:
        fields.append("role = :role")
        params["role"] = role
    
    if not fields:
        return get_user_by_id(db, user_id)  # No updates, return current user
    
    query = text(f"UPDATE users SET {', '.join(fields)} WHERE id = :user_id RETURNING *")
    result = db.execute(query, params).fetchone()
    db.commit()
    
    return result._mapped.first() if result else None
