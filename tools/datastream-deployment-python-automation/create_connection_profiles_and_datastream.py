#!/usr/bin/python3

# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This script will be used to create datastream from Cloud SQL(MySQL) to Cloud
Storage

Please update all config variables in variables.py file
"""
from getpass import getpass
import json
import sys
import time
import requests
from variables import PROJECT_ID, GCP_LOCATION, source_profile_config, \
    destination_profile_config, stream_config


def create_source_connection_profile(source_config, db_password,
                                     token, project, location):
    """
    This function will create the source connection profile in Google Cloud DataStream
    :param source_config: source config from variables.py
    :param db_password: password of DB user mentioned in variables.py
    :param token: Google Cloud auth token
    :param project: Google Cloud project id mentioned in variables.py
    :param location: Google Cloud resource location, for example us-central1
    :return: True or False
    """
    profile_name = source_config["source_profile_name"]
    profile_id = source_config["source_profile_id"]
    db_hostname = source_config["source_db_hostname"]
    db_port = source_config["source_db_port"]
    db_username = source_config["source_db_username"]

    url = f"https://datastream.googleapis.com/v1/projects/{project}/" \
          f"locations/{location}/connectionProfiles" \
          f"?connectionProfileId={profile_id}"

    payload = json.dumps({
        "displayName": profile_name,
        "mysqlProfile": {
            "hostname": db_hostname,
            "port": db_port,
            "username": db_username,
            "password": db_password
        },
        "staticServiceIpConnectivity": {}
    })
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        print(f"Source connection profile {profile_name} created successfully")
        source_connection_profile_stat = True
    elif response.status_code == 409:
        print(f"Source connection profile {profile_name} already exist")
        source_connection_profile_stat = True
    else:
        print(f"Issue while creating source connection profile: {response.text}")
        source_connection_profile_stat = False
    return source_connection_profile_stat


def create_destination_connection_profile(project, location, destination_config, token):
    """
    This function will create the destination connection profile in Google Cloud DataStream
    :param project: Google Cloud project id mentioned in variables.py
    :param location: Google Cloud resource location, for example us-central1
    :param destination_config: destination config from variables.py
    :param token: Google Cloud auth token
    :return: True or False
    """

    d_profile_name = destination_config["destination_profile_name"]
    d_profile_id = destination_config["destination_profile_id"]
    bucket_name = destination_config["storage_bucket_name"]
    bucket_prefix = destination_config["storage_bucket_prefix"]

    url = f"https://datastream.clients6.google.com/v1alpha1/" \
          f"projects/{project}/locations/{location}" \
          f"/connectionProfiles?connectionProfileId={d_profile_id}"

    payload = json.dumps({
        "displayName": d_profile_name,
        "gcsProfile": {
            "bucketName": bucket_name,
            "rootPath": bucket_prefix
        }
    })
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        print(f"Destination connection profile {d_profile_id} created successfully")
        destination_connection_profile_stat = True
    elif response.status_code == 409:
        print(f"Destination connection profile {d_profile_id} already exist")
        destination_connection_profile_stat = True
    else:
        print(f"Issue while creating destination connection profile: {response.text}")
        destination_connection_profile_stat = False
    return destination_connection_profile_stat


def create_stream(project, location, s_config, token):
    """
    This function will create the stream in Google Cloud DataStream
    :param project: Google Cloud project id mentioned in variables.py
    :param location: Google Cloud resource location, for example us-central1
    :param s_config: stream config from variables.py
    :param token: Google Cloud auth token
    :return: True or False
    """

    stream_id = s_config["stream_id"]
    name = s_config["stream_name"]
    source_connection_id = source_profile_config["source_profile_id"]
    destination_connection_id = destination_profile_config["destination_profile_id"]

    url = f"https://datastream.clients6.google.com/v1alpha1/projects/{project}/" \
          f"locations/{location}/streams?streamId={stream_id}"
    source_connection_path = f"projects/{project}/locations/{location}/" \
                             f"connectionProfiles/{source_connection_id}"
    destination_connection_path = f"projects/{project}/locations/{location}/" \
                                  f"connectionProfiles/{destination_connection_id}"

    payload = json.dumps({
        "displayName": name,
        "sourceConfig": {
            "sourceConnectionProfileName": source_connection_path,
            "mysqlSourceConfig": {
                "allowlist": {
                    "mysqlDatabases": []
                },
                "rejectlist": {
                    "mysqlDatabases": []
                }
            }
        },
        "destinationConfig": {
            "destinationConnectionProfileName": destination_connection_path,
            "gcsDestinationConfig": {
                "path": "",
                "avroFileFormat": {}
            }
        },
        "backfillAll": {
            "mysqlExcludedObjects": {}
        }
    })
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        print(f"Stream {name} created successfully")
        create_stream_stat = True
    elif response.status_code == 409:
        print(f"Stream {name} already exist")
        create_stream_stat = True
    else:
        print(f"Issue while creating stream: {response.text}")
        create_stream_stat = False
    return create_stream_stat


def start_stream(project, location, token, s_config):
    """
    This function will start the stream in Google Cloud DataStream
    :param project: Google Cloud project id mentioned in variables.py
    :param location: Google Cloud resource location, for example us-central1
    :param token: Google Cloud auth token
    :param s_config: stream config from variables.py
    :return: True or False
    """

    stream_id = s_config["stream_id"]
    name = s_config["stream_name"]

    url = f"https://datastream.googleapis.com/v1/" \
          f"projects/{project}/locations/{location}/streams/{stream_id}?" \
          "updateMask=state"

    payload = json.dumps({
        "state": "RUNNING"
    })
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }

    response = requests.request("PATCH", url, headers=headers, data=payload)

    if response.status_code == 200:
        print(f"Stream {name} started successfully")
        start_stream_stat = True
    else:
        print(f"Issue while starting stream: {response.text}")
        start_stream_stat = False
    return start_stream_stat


def main():
    """
    This is the main function
    :return: Print statement if everything works fine else exit with status 1
    """

    auth_token = getpass('Enter auth_token, you can generate auth token by '
                         'running gcloud config set project <project_id> && '
                         'gcloud auth print-access-token: ')

    source_db_password = getpass('Enter Source DB Password: ')

    auth_token = "Bearer " + auth_token

    source_connection_profile_status = create_source_connection_profile(source_profile_config,
                                                                        source_db_password,
                                                                        auth_token,
                                                                        PROJECT_ID, GCP_LOCATION)
    if source_connection_profile_status:
        destination_connection_profile_status = create_destination_connection_profile\
            (PROJECT_ID, GCP_LOCATION, destination_profile_config, auth_token)
        if destination_connection_profile_status:
            create_stream_status = create_stream(PROJECT_ID, GCP_LOCATION,
                                                 stream_config,
                                                 auth_token)
            if create_stream_status:
                time.sleep(60)
                start_stream_status = start_stream(PROJECT_ID, GCP_LOCATION,
                                                   auth_token,
                                                   stream_config)
                if start_stream_status:
                    print("Process Completed!")
                else:
                    sys.exit(1)
        else:
            sys.exit(1)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
