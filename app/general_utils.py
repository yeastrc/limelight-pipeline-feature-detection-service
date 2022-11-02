"""General utility methods for the app"""

#   Copyright 2022 Michael Riffle
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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
