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

logging.getLogger().setLevel(logging.INFO)


def main(event, context):

    print("""This Function was triggered by messageId {} published at {} to {}
    """.format(context.event_id, context.timestamp, context.resource["name"]))

    try:
        alert = json.loads(base64.b64decode(result['data']).decode('utf-8'))
    except Exception as e:
        logging.exception(e)
        logging.error("Event: %s", pformat(event))
        logging.error("Event.data: %s", pformat(base64.b64decode(event['data']).decode('utf-8')))
