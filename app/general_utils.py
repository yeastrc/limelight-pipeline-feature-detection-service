import uuid
import os


def generate_request_id():
    return str(uuid.uuid4())


def verify_file_exists(file_path):
    """Verify the file at the given path exists, raise exception if not

    Parameters:
        file_path (string): Full path to file we are verifying exists

    Returns:
        NoneType
    """

    if not os.path.exists(file_path):
        raise ValueError('Expected file not found:', file_path)
