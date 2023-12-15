# Copyright © 2023 Upvest GmbH <support@upvest.co>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore
from sqlalchemy import create_engine
import requests
import config
import settings


def setup_db():
    """Initiate the database"""
    db_engine = create_engine(settings.DB_CONNECTION_STRING)

    installation_store = SQLAlchemyInstallationStore(
        client_id=settings.SLACK_CLIENT_ID,
        engine=db_engine
    )

    installation_store.create_tables()

    state_store = SQLAlchemyOAuthStateStore(
        expiration_seconds=600,
        engine=db_engine
    )

    state_store.metadata.create_all(state_store.engine)

    return installation_store, state_store


def create_app():
    installation_store, state_store = setup_db()
    oauth_settings = OAuthSettings(
        client_id=settings.SLACK_CLIENT_ID,
        client_secret=settings.SLACK_CLIENT_SECRET,
        scopes=["chat:write", "calls:write", "commands", "users:read",
                "users:read.email", "workflow.steps:execute",
                "chat:write.public"],
        installation_store=installation_store,
        state_store=state_store
    )

    return App(
        signing_secret=settings.SLACK_SIGNING_SECRET,
        oauth_settings=oauth_settings
    )



def handle_action(ack, user, client, say, msg):
    ack()
    return say(channel=user, blocks=msg)


def handle_view(ack, body, client, view, action):
    ack()
    if (action == "open"):
        client.views_open(
            trigger_id=body["trigger_id"],
            view=view
        )
    elif (action == "update"):
        client.views_update(
            trigger_id=body["actions"][0]["action_id"],
            view=view,
            view_id=body["view"]["id"]
        )        


def handle_ticket_creation(body, name, email, subject, description, custom_fields, slack_user, workspace):

    meta = body["view"]["private_metadata"].split()
    group = meta[0]
    channel = meta[1]

    comment = "Link to the user: https://app.slack.com/client/" + str(workspace) + "/" + str(channel) + "\nType: " + body["view"]["external_id"]

    for subtype in list(custom_fields.keys()):
        if(subtype != "chooseSystem"):
            subtypeobject = body["view"]["state"]["values"][subtype]
            subtypeobject = list(subtypeobject.keys())[0]
            if not subtypeobject == "input_subject" and not subtypeobject == "input_description":
                value = body["view"]["state"]["values"][subtype][subtypeobject]["value"]
                if value is None:
                    value = "[no value provided]"
                comment += "\n" + subtypeobject + ": " + value
        else:
            comment += "\n" + "Environment: " + body["view"]["state"]["values"][subtype]["selectedSystem"]["selected_option"]["value"]

    comment += "\nComment: " + description
# make sure to adjust the groups to the escalation domain or other way to ensure that ticket will be routed to the team which owns the queue.
    if group == "TECH":
        escalation_domain = "api_technical_issue"
    elif group == "OPS":
        escalation_domain = "operations"
    elif group == "LEGAL":
        escalation_domain = "compliance"
    else:
        print("Unknown group encounted ", group)

    body = {
        "request": {
            "requester": {
                "name": name,
                "email": email
            },
            "subject": group + ": " + subject,
            "comment": {
                "body": comment
            },
            "custom_fields": [{ "id": config.owning_team_field_id, "value": escalation_domain }]
        }
    }

    domain = config.domain+"/api/v2/requests"
    result = requests.post(domain, json=body).json()
    try:
        id = result["request"]["id"]
        return {"id":id, "channel":channel}
    except Exception as err:
        print("weird error condition:")
        print(err)
        print("result ==", result)
        print("channel ==", channel)
        return {}

    
def handle_subtype_view(ack, body, client, item):
    maintype = body["actions"][0]["action_id"]
    if item["value"] == maintype:
        view = {
            "type": "modal",
            "callback_id": "view_zendesk_ticket_creation_done",
            "external_id": item["text"],
            "private_metadata": str(item["group"])+" "+body["view"]["private_metadata"],
            "title": {"type": "plain_text", "text": config.title},
            "submit": {"type": "plain_text", "text": "Create"},
            "blocks": [
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Create a new request (3/3)*\nAwesome! Now please fill out the last informations."
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": config.logo,
                        #ensure to set your company logo in the config
                        "alt_text": "{your comapany} Logo"
                    }
                },
                {
                    "type": "divider"
                }
            ]
        }
#below is example of implementation of the view structure that is defined in config.py
        if maintype == "type_api_request_issue":
            view["blocks"].append(
            {
                "type": "input",
                "block_id": "chooseSystem",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select system",
                        "emoji": True
                    },
                    "options": [{
                        "text": {
                            "type": "plain_text",
                            "text": "Production",
                            "emoji": True
                        },
                        "value": "Production"
                        },
                        {
                        "text": {
                            "type": "plain_text",
                            "text": "Sandbox",
                            "emoji": True
                        },
                        "value": "Sandbox"
                    }],
                    "action_id": "selectedSystem"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Choose the affected system*"
                }
            })

        for sub in item["sub"]:
            optional = True if maintype == "type_api_request_issue" and sub == "Request ID" else False
            star = "*" if optional == False else ""
            view["blocks"].append(
            {
                "type": "input",
                "optional": optional,
                "block_id": "txt_"+sub,
                "element": {
                    "type": "plain_text_input",
                    "action_id": sub,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Type your answer here"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": sub + star
                }
            })

        view["blocks"].append(
            {
                "type": "input",
                "block_id": "txt_subject",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input_subject",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter the subject of your request"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Subject*"
                }
            }
        )
        # custom description value example
        value_description = "If the Request ID is not available, please provide\nClient ID:\nApproximate time (UTC):\nEndpoint:\nResponse status code:"
        holder_description = "Add the notes to describe your request here"

        if maintype == "type_api_request_issue":
            view["blocks"].append(
            {
                "type": "input",
                "block_id": "txt_description",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "input_description",
                    "initial_value": value_description
                },
                "label": {
                    "type": "plain_text",
                    "text": "Description*"
                }
            })
        else:
            view["blocks"].append(
            {
                "type": "input",
                "block_id": "txt_description",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "input_description",
                    "placeholder": {
                            "type": "plain_text",
                            "text": holder_description
                        }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Description*"
                }
            })
        
        handle_view(ack, body, client, view, "update")

        

    
@app.action("escalation_technical")
def handle(ack, body, client):
    view = {
            "type": "modal",
            "private_metadata": body["view"]["private_metadata"],
            "title": {"type": "plain_text", "text": config.title},
            "blocks": [
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Create a new request (2/3)*\nAlright! Now please choose your topic"
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": config.logo,
                        "alt_text": "Upvest Logo"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Topic*"
                    }
                }
            ]
        }
    
    for type in config.technical:
        view["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": type["text"]
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "Choose"
                },
                "value": type["value"],
                "action_id": type["value"]
            }
        })

    handle_view(ack, body, client, view, "update")

    
@app.action("escalation_operations")
def handle(ack, body, client):
    view = {
            "type": "modal",
            "private_metadata": body["view"]["private_metadata"],
            "title": {"type": "plain_text", "text": config.title},
            "blocks": [
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Create a new request (2/3)*\nAlright! Now please choose your topic"
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": config.logo,
                        "alt_text": "Upvest Logo"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Topic*"
                    }
                }
            ]
        }
    
    for type in config.operation:
        view["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": type["text"]
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "Choose"
                },
                "value": type["value"], 
                "action_id": type["value"]
            }
        })

    handle_view(ack, body, client, view, "update")


for item in config.technical:
    @app.action(item["value"])
    def handle(ack, body, client):
        for item in config.technical:
            handle_subtype_view(ack, body, client, item)


for item in config.operation:
    @app.action(item["value"])
    def handle(ack, body, client):
        for item in config.operation:
            handle_subtype_view(ack, body, client, item)


@app.view("view_zendesk_ticket_creation_done")
def handle(ack,  body,  client,  view,  say,  message):
    slack_user = body["user"]["id"]
    user = client.users_info(user=slack_user)['user']['profile']
    workspace = body["user"]["team_id"]
    name = body["user"]["name"]
    email = user["email"]
    subject = str(view["state"]["values"]["txt_subject"]["input_subject"]["value"])
    description = str(view["state"]["values"]["txt_description"]["input_description"]["value"])
    custom_fields = body["view"]["state"]["values"]

    ticket = handle_ticket_creation(body, name, email, subject, description, custom_fields, slack_user, workspace)

    if(ticket["id"]):
        id = ticket["id"]
        domain = config.domain + "/hc/requests"
        txt = f"<@{slack_user}> Your request was successfully created.\nTicket ID: #{id}.\nTopic: {subject}\nYou can check your ticket(s) status <{domain}|here>."
    else:
        txt = "An error occurred during the creation process."

    msg = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": txt,
                }
            }
        ]
    
    #Send direct message
    handle_action(ack, slack_user, client, say, msg)

    #Send to initial Channel
    handle_action(ack, ticket["channel"], client, say, msg)


    
if __name__ == "__main__":
    app.start(port=settings.PORT)
