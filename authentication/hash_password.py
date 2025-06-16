from argon2 import PasswordHasher, exceptions

# Configure Argon2 parameters
ph = PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # 64 MB
    parallelism=2,      # Number of threads
)

def hash_password(password):
    """
    Hash a password using Argon2id and return the encoded hash string.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    return ph.hash(password)

def verify_password(stored_hash, provided_password):
    """
    Verify a password against the stored Argon2 hash.
    """
    if not stored_hash or not provided_password:
        raise ValueError("Stored hash and provided password must not be empty.")
    try:
        return ph.verify(stored_hash, provided_password)
    except exceptions.VerifyMismatchError:
        return False
    except exceptions.VerificationError:
        return False