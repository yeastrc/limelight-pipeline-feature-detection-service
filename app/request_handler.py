"""Handle processing of the request queue"""

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

import os
import time
import traceback
from . import __request_check_delay__, __workdir_env_key__, run_pipeline_methods


def process_request_queue(request_queue, request_status_dict):
    """Serially process all requests in the request queue

    Parameters:
        request_queue (list): The request queue, a list of dicts: {'id': request_id, 'data': xml_request}
        request_status_dict (dict): The dict that stores the status of requests

    Returns:
        None
    """

    while True:
        while len(request_queue) > 0:
            request = request_queue.pop(0)

            process_request(request, request_status_dict)

        time.sleep(__request_check_delay__)


def process_request(request, request_status_dict):
    """Process the given request. Should not ever raise an exception. Will update the
    request status dict appropriately.

    Parameters:
        request (dict): A dict: {'id': request_id, 'data': {data for job}}
        request_status_dict (dict): The dict that stores the status of requests

    Returns:
        None
    """

    print('Processing request:')
    print('\trequest', request)
    print('\trequest_status_dict', request_status_dict)

    workdir = None

    try:

        workdir = get_workdir(request)

        request_status_dict[request['id']]['status'] = 'processing'
        request_status_dict[request['id']]['end_user_message'] = 'Initiating feature detection pipeline run...'

        run_pipeline_methods.export_spectral_data(request, request_status_dict, workdir)
        run_pipeline_methods.write_hardklor_config_file(request, request_status_dict, workdir)
        run_pipeline_methods.execute_hardklor(request, request_status_dict, workdir)
        run_pipeline_methods.execute_bullseye(request, request_status_dict, workdir)
        run_pipeline_methods.move_data_to_final_destination(request, request_status_dict, workdir)

        request_status_dict[request['id']]['status'] = 'success'
        request_status_dict[request['id']]['message'] = 'Pipeline complete'

        run_pipeline_methods.clean_workdir(workdir, success=True)

    except Exception as e:
        request_status_dict[request['id']]['status'] = 'error'
        request_status_dict[request['id']]['message'] = str(e)

        # print stack trace
        traceback.print_exc()

        run_pipeline_methods.clean_workdir(workdir, success=False)


def get_workdir(request):
    """Create and return the path to the work directory

    Parameters:
        request (dict): A dict: {'id': request_id, 'data': xml_request}

    Returns:
        string
    """

    if os.getenv(__workdir_env_key__) is None:
        raise ValueError('No environmental variable defined:', __workdir_env_key__)

    if not os.path.exists(os.getenv(__workdir_env_key__)):
        raise ValueError('Directory does not exist: ', os.getenv(__workdir_env_key__))

    if not os.path.isdir(os.getenv(__workdir_env_key__)):
        raise ValueError('Work directory is a file, not a directory:', os.getenv(__workdir_env_key__))

    workdir = os.path.join(os.getenv(__workdir_env_key__), request['id'])
    if os.path.exists(workdir):
        raise ValueError('Work directory already exists:', workdir)

    os.mkdir(workdir)
    if not os.path.exists(workdir):
        raise ValueError('Failed to create work directory:', workdir)

    return workdir
