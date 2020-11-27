# visionquest
A serendipitous wrong-number machine learning computer vision scavenger hunt game


## wut
I bought a number with twilio many moons ago and used it as a simple txt message forwarder for sketchy craigslist purchases.  I noticed I started getting random messages saying "START" or whatever, and I wanted to learn how to twilio API, so I set up a little bit of a scavenger hunt for those who accidentally typo'd their way into my phone number honeypot...


## dependencies
Vision Quest is designed to be deployed to cloud services.  Twilio will charge for a phone number and text messages, but it's quite small; Google Cloud is used for the service infrastructure and, while it requires a billing-enabled account, should remain well-within the free tier of services.  Unless you become suddenly popular I suppose...

Twilio services:
* Programmable Messaging

Google Cloud services:
* Cloud Functions
* Cloud Firestore
* Cloud Storage
* Cloud Vision


## how do
### make db
Create a firestore DB and call it something clever like "vision-quest".

### make storage
Create a cloud storage bucket and call it something clever like "vision-quest". If that's taken, add a number after it or something.

### deploy cloud function
Use gcloud SDK to deploy the function:
```
gcloud functions deploy vision_quest_sms_in \
       --runtime python37 \
       --trigger-http \
       --allow-unauthenticated
```

### fight IAM for a while
the appspot service account needs to have perms to write to cloud storage, write to db, and make calls to vision... 'owner' will work but there's probably a better set of roles.  you can find the service account name with gcloud SDK:
```gcloud iam service-accounts list |grep appspot | awk '{print $(NF-1)}'```


### point twilio at gcloud function
first find the trigger URL of your function. in gcloud sdk:
```gcloud functions describe vision_quest_sms_in |grep httpsTrigger -A1 |grep https:// |awk '{print $NF}'```

then log into twilio -> phone numbers -> active numbers -> your number -> scroll down to messaging, set to 
* "Configure with": "Webhooks, TwiML Bins, Functions, Studio or Proxy"
* "A message comes in": "Webhook", URL of trigger found earlier

save it then text that number and see what happens!

## it doesnt work
:(

check google cloud logging -- it'll usually throw a traceback that'll give you a hint as to where the problem may lie. 

