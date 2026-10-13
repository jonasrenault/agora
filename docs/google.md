# Google APIs

The application uses Google's APIs to receive notifications when a new mail is received in the user's Gmail inbox.

## Setup

To setup the environment to use Google's APIs, follow the [quickstart guide](https://developers.google.com/workspace/gmail/api/quickstart/python#set-up-environment) to

1. Create a [Google Cloud project](https://developers.google.com/workspace/guides/create-project).
2. [Enable the Gmail API](https://console.cloud.google.com/apis/enableflow;apiid=gmail.googleapis.com) for the project.
3. [Configure the OAuth consent screen](https://developers.google.com/workspace/gmail/api/quickstart/python#configure_the_oauth_consent_screen).
4. [Get credentials for a web application](https://console.developers.google.com/auth/clients) and save the client ID, client secret and project ID in the project's settings as env variables `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `GOOGLE_OAUTH_PROJECT_ID`.

## Cloud Pub/Sub

The Gmail API provides server push notifications by using the [Cloud Pub/Sub API](https://console.cloud.google.com/project/_/cloudpubsub/topicList). [This guide](https://developers.google.com/workspace/gmail/api/guides/push) shows how to setup a topic and subscription in the [Cloud Pub/Sub console](https://console.cloud.google.com/project/_/cloudpubsub/topicList).

1. First create a topic such as `projects/myproject/topics/gmail-push-notifications`.
2. Then create a `push` subscription `projects/myproject/subscriptions/agora-railway-gmail-push-notifications` with a push endpoint pointing to `https://{production_url}/api/v1/google/webhook`.
3. Grant publish rights on the topic to the Gmail service account `gmail-api-push@system.gserviceaccount.com`.
4. Save the topic and subscription names as env variables `GOOGLE_WEBHOOK_TOPIC` and `GOOGLE_WEBHOOK_SUBSCRIPTION`.

## Gmail Watch

On the Gmail and Cloud Pub/Sub APIs have been setup, the [Gmail API](https://developers.google.com/workspace/gmail/api/guides/push#gmail-watch) must send a `watch` request for each client to send notifications to the Cloud Pub/Sub topic. This watch request is sent as a [BackgroundTask](https://fastapi.tiangolo.com/tutorial/background-tasks/) whenever a user logs in with their google account.

!!! warning

    The [Gmail API](https://developers.google.com/workspace/gmail/api/guides/push#renew-mailbox) specifies that a `watch` request must be sent at least once every 7 days or push notifications will stop for the user. This is currently unimplemented and the user must logout / login in the application to trigger a new `watch` request at least once every 7 days.
