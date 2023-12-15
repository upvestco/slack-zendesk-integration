
# Slack to ZenDesk integration

This project was developed in a collaboration between Leafworks and Upvest.

The purpose of this Slack app is to give your customers a simple and guided way to submit a requests into ZenDesk from Slack.

In comparison to the [official ZenDesk Slack app](https://www.zendesk.com/slack/), the major pros and cons are:

Pros:
1. This app requires limited scopes, that allow it to comply with tighter security restrictions, for example those required in finance companies.
2. This app has dynamic request submission flow, which allows it to guide users to provide the data needed for specific support case types and sub-types.

Cons:
1. The integration is one-way only. Your agents have to navigate back to a shared slack channel or switch to ZenDesk for further communication with user.


## Installation

1. Build a pipeline and/or upload the repository to your hosting server (AWS, Heroku etc.)
2. The procfile, requirements & runtime files are already configured
3. Create a new [Slack app](https://api.slack.com/apps) from an app manifest.
4. Paste the following JSON into the manifest, and insert the URL of your app into the fields wherever you see  `<your-server-url>`. 

```javascript
  {
    "display_information": {
        "name": "<your-app-name>",
        "description": "This app lets you create a Zendesk ticket",
        "background_color": "#0061eb"
    },
    "features": {
        "bot_user": {
            "display_name": "<your-app-name>",
            "always_online": true
        },
        "slash_commands": [
            {
                "command": "/help",
                "url": "<your-server-url>/slack/events",
                "description": "Create a new ticket",
                "should_escape": false
            }
        ]
    },
    "oauth_config": {
        "redirect_urls": [
            "<your-server-url>/slack/oauth_redirect"
        ],
        "scopes": {
            "bot": [
                "calls:write",
                "chat:write",
                "commands",
                "users:read",
                "users:read.email",
                "workflow.steps:execute",
                "chat:write.public"
            ]
        }
    },
    "settings": {
        "event_subscriptions": {
            "request_url": "<your-server-url>/slack/events",
            "bot_events": [
                "workflow_step_execute"
            ]
        },
        "interactivity": {
            "is_enabled": true,
            "request_url": "<your-server-url>/slack/events"
        },
        "org_deploy_enabled": false,
        "socket_mode_enabled": false,
        "token_rotation_enabled": false
    }
}
```

5. Open the **Basic information** Slack page, scroll down and add an app icon.
6. Scroll up and copy the **Client ID**, **Client Secret** and **Signing Secret**
7. Open your host server settings, create new config/environment variables called **SLACK_CLIENT_ID**, **SLACK_CLIENT_SECRET** and **SLACK_SIGNING_SECRET** and paste your copied values accordingly
8. Go back to Slack and open the page **Install app** to add the app to your workspace
9. Open **Manage Distribution** and **Activate Public Distribution**
10. Share the Link defined in **Shareable URL** to allow your customers to add the app to their workspaces.
11. If you wish to specifiy a port number that your host will listen on, add a **PORT** environment variable too.
12. Open the repository file **config.py** and replace the variables **domain** and **logo** (squared & .png) with your own values
13. Run the app on your server
14. 🚀 You can use the app with the command defined in **app.py** in your Slack channels now. Have fun! 🏁
15. 💡 Good to know: When a customer requests a ticket, they will be informed about the ticket number & description via Slack. 💡

## Local Server for testing
1. If you would like to test this app, consider the above configuration first
2. Add the **SECRET**, **TOKEN** & **PORT** variable in your **os**
3. Start the python app locally and ngrok for the localhost port
4. Replace the URL in your manifest above
5. Test this app in your Slack.

## How to run it in Docker locally for development

1. Create a `.env` file. (Copy it from `.env.example` as a template.)
2. Generate or obtain the `TOKEN` and `SECRET` values as described above and fill them in in the `.env` file.
3. Run `make build-dev` to build the Docker image.
4. Run `make run-dev` to run a container with that Docker image.
5. Once logged in inside that container, run `./run.sh`

## How to deploy from your local machine

1. Run `gcloud auth configure-docker` to allow Docker to push to the GCP Container Registry
2. Run `make gcp-deploy` to build a production Docker image, push it to GCP and deploy it as a GCP Cloud Run instance

## GCP Setup Notes

Find [notes about the GCP setup in a separate document](./gcp-setup-notes.md).

## Important note:
To give the bot permissions to write in private channels, you need to invite the bot first.
The oauth method saves installations + states data in a separate folder **data**

## Commercial service and support
This app is provided under an Apache 2.0 license and, as is normal for Open Source software, Upvest does not offer a warranty or support for this code outside our commercial relationships.   If you require commercial support or service for this library please contact leafworks:
- [www.leafworks.de](https://www.leafworks.de)
- [Email: kontakt@leafworks.de](mailto:kontakt@leafworks.de)


![Logo](https://leafworks.de/wp-content/uploads/2020/02/logo_leafworks_schrift_only_blue.png)


## Defining a custom handler

The following is an example of the implementation of a custom handler.  Notice the use of `app.command` decorator.  Fully realised examples are present in `app.py`.

```python
# make sure to define the handler string below
@app.command("/{slack handler string goes here}")
# example of view rendering defined below
def handle(ack, body, client, command): 
    view = {
            "type": "modal",
            "callback_id": "view_zendesk_ticket_creation",
            "private_metadata": str(command["channel_id"]),
            "title": {"type": "plain_text", "text": config.title},
            "blocks": [
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Create a new request (1/3)*\nWe would like to help you as soon as possible\nThat's why we need some more details.\nPlease select an request type first\nto start your request"
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": config.logo,
                        "alt_text": "{your company} Logo"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Request type*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Operations"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Choose"
                        },
                        "value": "escalation_operations",
                        "action_id": "escalation_operations"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Technical"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Choose"
                        },
                        "value": "escalation_technical",
                        "action_id": "escalation_technical"
                    }
                }
            ]
        }
    
    handle_view(ack, body, client, view, "open")
```
