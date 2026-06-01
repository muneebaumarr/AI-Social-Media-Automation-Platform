from app.services.auth_service import hash_password, verify_password

h = hash_password("test123")
print("Hash:", h)
print("Match:", verify_password("test123", h))
print("Wrong:", verify_password("wrong", h))
