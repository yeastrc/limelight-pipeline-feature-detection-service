"""Helper methods for Bullseye"""

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


def convert_bullseye_config_to_dict(bullseye_config):
    """Read the lines of a "bullseye config" file that contains all the parameters needed to
    run Bullseye. Each line is in the form of <bullseye CLI param>=<value>, e.g., p=5  All lines
    not in this format will be ignored.

    Parameters:
        bullseye_config (string): Contents of a bullseye config file, new lines included

    Returns:
        dict: keys are CLI params, values are values for those params
    """

    if bullseye_config is None or len(bullseye_config) < 1:
        return {}

    if "\n" in bullseye_config:
        bullseye_config = bullseye_config.replace("\r", "")
    else:
        bullseye_config = bullseye_config.replace("\r", "\n")

    lines = bullseye_config.split("\n")

    ret_dict = {}
    for line in lines:
        line = line.strip()
        if not line.startswith("#"):
            fields = line.split("=")
            if len(fields) == 2:
                key = fields[0].strip()
                value = fields[1].strip()

                ret_dict[key] = value

    return ret_dict
