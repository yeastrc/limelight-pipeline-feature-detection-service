"""Methods for writing .ms2 files"""

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

from . import spectr_utils, mass_utils, __spectr_batch_size_env_key__, __ms2_file__
from datetime import datetime
import os


def create_ms2_file(spectr_file_id, ms2_scan_numbers, workdir):
    """Create a MS2 file from a spectr file id for the given scans

    Parameters:
        spectr_file_id (string): A spectr file id
        ms2_scan_numbers (list): Array of scan numbers to include in ms2 file
        workdir (string): Full path to the working directory

    Returns:
        None
    """

    ms2_file_name = __ms2_file__

    scan_count_per_call = os.getenv(__spectr_batch_size_env_key__)
    if scan_count_per_call is None:
        raise ValueError('Missing environmental variable:', __spectr_batch_size_env_key__)

    scan_count_per_call = int(scan_count_per_call)

    scan_sets = [ms2_scan_numbers[i:i + scan_count_per_call] for i in range(0, len(ms2_scan_numbers), scan_count_per_call)]

    ms2_file = initialize_ms2_file(workdir, ms2_file_name)

    try:
        for scan_array in scan_sets:
            scan_data = spectr_utils.get_scan_data_for_scan_numbers(spectr_file_id, scan_array)

            for ms2_scan in scan_data:
                write_scan_to_ms2_file(
                    ms2_file,
                    ms2_scan.scan_number,
                    ms2_scan.precursor_mz,
                    ms2_scan.precursor_charge,
                    ms2_scan.retention_time_seconds,
                    ms2_scan.peak_list_mz,
                    ms2_scan.peak_list_intensity
                )

    finally:
        close_ms2_file(ms2_file)


def write_scan_to_ms2_file(
        ms2_file,
        scan_number,
        precursor_mz,
        charge,
        retention_time_seconds,
        peak_list_mz,
        peak_list_intensity
):
    """Write the supplied scan data to the ms2_file

    Example scan lines:
        S	10	10	636.34
        I   RTime   2.042753
        Z	2	1271.67
        187.4 12.5
        193.1 19.5
        194.3 13.7
        198.3 29.8
        199.1 12.2

    Parameters:
        ms2_file (filehandle): ms2 file we are writing to
        scan_number (int): Scan number of the scan
        precursor_mz (float): Precursor m/z
        charge (int): Charge for this scan
        retention_time_seconds (float): Retention time in seconds
        peak_list_mz (list): array of m/z values from scan
        peak_list_intensity (list): array of intensities corresponding to m/z array

    Returns:
        NoneType
    """

    neutral_mass = mass_utils.get_neutral_mass_from_mz_and_charge(precursor_mz, charge)

    ms2_file.write("S\t" + str(scan_number) + "\t" + str(scan_number) + "\t" + str(precursor_mz) + "\n")
    ms2_file.write("I\tRTime\t" + str(retention_time_seconds / 60) + "\n")  # write retention time in minutes
    ms2_file.write("Z\t" + str(charge) + "\t" + str(neutral_mass) + "\n")

    for mz, intensity in zip(peak_list_mz, peak_list_intensity):
        ms2_file.write(str(mz) + " " + str(intensity) + "\n")


def close_ms2_file(ms2_file):
    """Close the filehandle associated with this ms2 file

    Returns:
        NoneType
    """
    ms2_file.close()


def initialize_ms2_file(path_to_directory, filename):
    """Create a file at path_to_directory, filename and write header (H) lines
    to it.

    Returns:
        io.TextIOWrapper: File handle to the created file for subsequent writes of scan data
    """
    ms2_file = open(os.path.join(path_to_directory, filename), 'w')

    write_header_to_ms2_file(ms2_file, 'CreationDate', datetime.now().strftime("%Y%m%d"))
    write_header_to_ms2_file(ms2_file, 'Extractor', 'Limelight Spectr to MS2')
    write_header_to_ms2_file(ms2_file, 'Comments', 'See: https://github.com/yeastrc/limelight-pipeline-feature-detection-service')

    return ms2_file


def write_header_to_ms2_file(ms2_file, header_key, header_value):
    """Append the supplied key/value pair as a header to the supplied file
    handle

    Example header lines:

        H	CreationDate	20200323
        H	Extractor	Limelight Spectr to MS2
        H	ExtractorVersion	1.0
        H	Comments	MakeMS2 written by Michael J. MacCoss, 2004
        H	ExtractorOptions	MS2/MS1

    Returns:
        NoneType
    """
    ms2_file.write("H\t" + header_key + "\t" + header_value + "\n")
