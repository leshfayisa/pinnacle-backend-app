import os
import hashlib

def hash_password_with_salt(password):
    """
    Hash a password with a random salt and return the salt+hash as a hex string.
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # Generate a random 16-byte salt
    salt = os.urandom(16)  # 16 bytes = 32 hex characters

    # Create a new sha256 hash object
    sha256 = hashlib.sha256()

    # Update the hash object with the salt and password
    sha256.update(salt + password.encode('utf-8'))

    # Get the hexadecimal digest of the hash
    hashed_password = sha256.hexdigest()

    # Concatenate salt + hash (both in hex) for storage
    return salt.hex() + hashed_password  # Ensure salt is stored as hex



def verify_password(stored_password, provided_password):
    """
    Verify a stored password against a provided password.
    """
    if not stored_password or not provided_password:
        raise ValueError("Stored password and provided password must not be empty.")

    try:
        # Ensure stored_password is at least 96 characters (32 hex salt + 64 hex hash)
        if len(stored_password) != 96:
            raise ValueError("Invalid stored password format. Expected 96 characters.")

        salt_hex = stored_password[:32]  # First 32 characters should be the salt
        stored_hash = stored_password[32:]  # Remaining should be the hash

        # Convert hex salt back to bytes
        salt = bytes.fromhex(salt_hex)

    except ValueError as e:
        raise ValueError("Invalid stored password format. Ensure it's stored correctly.") from e

    # Create a new sha256 hash object
    sha256 = hashlib.sha256()

    # Update the hash object with the extracted salt and the provided password
    sha256.update(salt + provided_password.encode('utf-8'))

    # Get the hexadecimal digest of the hash
    provided_hash = sha256.hexdigest()


    # Compare the stored hash with the hash of the provided password
    return stored_hash == provided_hash
