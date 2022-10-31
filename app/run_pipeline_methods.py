from . import ms1_lib, ms2_lib, spectr_utils, general_utils, bullseye_utils
from . import __hardklor_config_file__, __hardklor_results_file__, __bullseye_results_file__, __ms1_file__,\
    __ms2_file__, __hardklor_filter_executable_path_env_key__, __bullseye_filter_executable_path_env_key__,\
    __final_dir_env_key__, __clean_working_directory_env_key__
import os
import subprocess
import shutil


def export_spectral_data(request, request_status_dict, workdir):
    """Export spectral data for this request to desk from spectr

    Parameters:
        request (dict): A dict: {'id': request_id, 'data': {data for job}}
        request_status_dict (dict): The dict that stores the status of requests
        workdir (string): Full path to workdir

    Returns:
        NoneType
    """

    spectr_file_id = request['data']['spectr_file_id']
    if spectr_file_id is None or not spectr_file_id:
        raise ValueError("Error running pipeline, could not find spectr_file_id in request.")

    # get all ms1 and ms2 scan numbers
    request_status_dict[request['id']]['end_user_message'] = 'Gathering scan numbers from spectr'
    ms1_scan_numbers = spectr_utils.get_scan_numbers_for_scan_level(spectr_file_id, 1)
    ms2_scan_numbers = spectr_utils.get_scan_numbers_for_scan_level(spectr_file_id, 2)

    # build ms1 file
    request_status_dict[request['id']]['end_user_message'] = 'Creating MS1 file'
    ms1_lib.create_ms1_file(spectr_file_id, ms1_scan_numbers, workdir)

    # build ms2 file
    request_status_dict[request['id']]['end_user_message'] = 'Creating MS2 file'
    ms2_lib.create_ms2_file(spectr_file_id, ms2_scan_numbers, workdir)


def write_hardklor_config_file(request, request_status_dict, workdir):
    """Write the Hardklor config file to disk

    Parameters:
        request (dict): A dict: {'id': request_id, 'data': {data for job}}
        request_status_dict (dict): The dict that stores the status of requests
        workdir (string): Full path to workdir

    Returns:
        NoneType
    """

    request_status_dict[request['id']]['end_user_message'] = 'Writing Hardklor config file'

    hardklor_config_data = request['data']['hardklor_conf']
    if hardklor_config_data is None or not hardklor_config_data:
        raise ValueError("Error running pipeline, could not find hardklor_config_data in request.")

    # ensure line endings are unix type
    hardklor_config_data = hardklor_config_data.replace("\r\n", "\n")
    hardklor_config_data = hardklor_config_data.replace("\r", "\n")

    # ensure it ends with a new line
    if not hardklor_config_data.endswith("\n"):
        hardklor_config_data = hardklor_config_data + "\n"

    endline = __ms1_file__ + "\t" + __hardklor_results_file__ + "\n"

    hardklor_config_data = hardklor_config_data + endline

    config_file = open(os.path.join(workdir, __hardklor_config_file__), 'w')
    config_file.write(hardklor_config_data)
    config_file.close()


def execute_hardklor(request, request_status_dict, workdir):
    """Run Hardklor feature detection on ms1 data

    Parameters:
        request (dict): A dict: {'id': request_id, 'data': {data for job}}
        request_status_dict (dict): The dict that stores the status of requests
        workdir (string): Full path to workdir

    Returns:
        NoneType
    """

    request_status_dict[request['id']]['end_user_message'] = 'Running Hardklor'

    hardklor_filter_executable = os.getenv(__hardklor_filter_executable_path_env_key__)
    if not os.path.exists(hardklor_filter_executable):
        raise ValueError('Could not find Hardklor executable:', hardklor_filter_executable)

    result = subprocess.run(
        [hardklor_filter_executable, __hardklor_config_file__],
        cwd=workdir,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)

    general_utils.verify_file_exists(os.path.join(workdir, __hardklor_results_file__))

    if result.returncode != 0:
        raise ValueError("Non-zero return code from Hardklor. Error message:", result.stderr)


def execute_bullseye(request, request_status_dict, workdir):
    """Run Bullseye persistent feature detection

    Parameters:
        request (dict): A dict: {'id': request_id, 'data': {data for job}}
        request_status_dict (dict): The dict that stores the status of requests
        workdir (string): Full path to workdir

    Returns:
        NoneType
    """

    request_status_dict[request['id']]['end_user_message'] = 'Running Bullseye'

    bullseye_filter_executable = os.getenv(__bullseye_filter_executable_path_env_key__)
    if not os.path.exists(bullseye_filter_executable):
        raise ValueError('Could not find Bullseye executable:', bullseye_filter_executable)

    bullseye_config_data = request['data']['bullseye_conf']
    if bullseye_config_data is None or not bullseye_config_data:
        raise ValueError("No bullseye config data.")

    bullseye_config_dict = bullseye_utils.convert_bullseye_config_to_dict(bullseye_config_data)

    # the array to build for the executable passed to subprocess.run
    execute_array = [bullseye_filter_executable]

    # add any user CLI params
    for key, value in bullseye_config_dict.items():
        execute_array.append(['-' + key], [value])

    # add rest of required CLI params
    execute_array.append(
        [
            __bullseye_results_file__,
            __hardklor_results_file__,
            __ms2_file__,
            'matches.ms2',
            'nomatches.ms2'
        ]
    )

    # run bullseye
    result = subprocess.run(
        execute_array,
        cwd=workdir,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)

    general_utils.verify_file_exists(os.path.join(workdir, __bullseye_results_file__))

    if result.returncode != 0:
        raise ValueError("Non-zero return code from Bullseye. Error message:", result.stderr)


def move_data_to_final_destination(request, request_status_dict, workdir):
    """Run Bullseye persistent feature detection

    Parameters:
        request (dict): A dict: {'id': request_id, 'data': {data for job}}
        request_status_dict (dict): The dict that stores the status of requests
        workdir (string): Full path to workdir

    Returns:
        NoneType
    """

    request_status_dict[request['id']]['end_user_message'] = 'Copying data to final location'

    project_id = request['data']['project_id']
    if project_id is None or not project_id:
        raise ValueError("No project id found.")

    if not os.path.exists(workdir):
        raise ValueError('Working directory does not exist:', workdir)

    if not os.path.exists(os.path.join(workdir, __hardklor_results_file__)):
        raise ValueError('Attempting to move hardklor results that don\'t not exist:',
                         os.path.join(workdir, __hardklor_results_file__))

    if not os.path.exists(os.path.join(workdir, __bullseye_results_file__)):
        raise ValueError('Attempting to move bullseye results that don\'t not exist:',
                         os.path.join(workdir, __bullseye_results_file__))

    if os.getenv(__final_dir_env_key__) is None:
        raise ValueError('Final destination dir env var not defined:', __final_dir_env_key__)

    final_destination_dir = os.getenv(__final_dir_env_key__)
    if not os.path.exists(final_destination_dir):
        raise ValueError('Final destination dir does not exist:', final_destination_dir)

    # place the resulting data in the final_destination_dir/project_id/
    final_destination_dir = os.path.join(final_destination_dir, str(project_id))
    if not os.path.exists(final_destination_dir):
        os.mkdir(final_destination_dir)

    # move the result files to the final location
    shutil.move(
        os.path.join(workdir, __hardklor_results_file__),
        os.path.join(final_destination_dir, __hardklor_results_file__)
    )

    shutil.move(
        os.path.join(workdir, __hardklor_config_file__),
        os.path.join(final_destination_dir, __hardklor_config_file__)
    )

    shutil.move(
        os.path.join(workdir, __bullseye_results_file__),
        os.path.join(final_destination_dir, __bullseye_results_file__)
    )

    general_utils.verify_file_exists(os.path.join(workdir, os.path.join(final_destination_dir, __hardklor_results_file__)))
    general_utils.verify_file_exists(os.path.join(workdir, os.path.join(final_destination_dir, __hardklor_config_file__)))
    general_utils.verify_file_exists(os.path.join(workdir, os.path.join(final_destination_dir, __bullseye_results_file__)))


def clean_workdir(workdir, success):
    """Remove the supplied directory and all files within. Swallows all exceptions but prints out
    error message

    Parameters:
        workdir (string): Full path to the desired directory
        success (bool): Whether the request was completed successfully

    Returns:
        NoneType
    """

    if get_should_clean_workdir(success):
        if workdir is not None and os.path.exists(workdir):
            try:
                shutil.rmtree(workdir)
            except OSError as e:
                print('Error cleaning workdir: ', workdir)


def get_should_clean_workdir(success):
    """Determine whether the working directory should be deleted. Uses the environmental
    variable to determine behavior. If that variable is set to 'no', never delete. If
    set to 'yes', always delete. If set to 'on success', only delete on success. Defaults
    to 'yes' if that variable is not set.

    Parameters:
        success (bool): Whether the request was completed successfully

    Returns:
        bool
    """

    workdir_deletion_config_string = os.getenv(__clean_working_directory_env_key__)

    if workdir_deletion_config_string is None:
        workdir_deletion_config_string = 'yes'

    if workdir_deletion_config_string == 'no':
        return False

    if workdir_deletion_config_string == 'yes':
        return True

    if workdir_deletion_config_string == 'on success':
        return success

    raise ValueError('Got unknown value for env var:', __clean_working_directory_env_key__)
