# vision quest twilio sms game
# text +1 604 245 8241 to play!
# it's a scavenger hunt/riddle thing using google vision to
# analyze photos to verify if you succeed or not.
# deploy to gcloud with:
# gcloud functions deploy vision_quest_sms_in \
#       --runtime python37 \
#       --trigger-http \
#       --allow-unauthenticated
#
# Other services needed:
# * A firestore database, named something clever like "vision-quest"
# * A Cloud Storage bucket, the name of which you should set in the
#     bucketName variable in the save_image() function below
# * Your cloud function service account with appropriate permissions
#     and the appropriate APIs enabled
#
# TODO:
# * share sent pictures somewhere
#   * webpage? slack/discord channel? other?
# * build on the quest
#   * proper reward to finishers
#   * more quests? 
#   * better riddles?
#   * diff type of detection (OCR etc)?

from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import firestore
from google.cloud import storage
from google.cloud import vision
import requests
import time
from questData import questData
from questData import goodJob
from questData import badJob
from random import choice

db = firestore.Client()
db_ref = db.collection('vision-quest')
storage_client = storage.Client()


def save_image(phoneNum, level, image):
    bucketName = "insert_bucket_name_here"
    now = int(time.time())
    filename = "level_" + str(level) + "_" + str(phoneNum) + str(now) + ".png"
    filepath = '{}/{}'.format('/tmp', filename)
    with open(filepath, 'wb') as f:
        f.write(requests.get(image).content)

    bucket = storage_client.get_bucket(bucketName)
    blob = bucket.blob(filename)
    blob.upload_from_filename(filepath)
    blob.make_public()
    imagePath = "gs://" + bucketName + "/" + filename
    return imagePath

def add_record(phoneNum,data):
    try:
        db_ref.document(phoneNum).set(data)
        return
    except Exception as e:
        return f"An error occurred: {e}"


def search_records(phoneNum):
    id = phoneNum
    try:
        data = db_ref.document(phoneNum).get()
        return data.to_dict()
    except Exception as e:
        return None


def update_record(phoneNum,data):
    try:
        db_ref.document(phoneNum).update(data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An errorrororoor: {e}"


def vision_query(image):
    ''' call out to google cloud vision and ask it
        to annotate the provided image '''
    client = vision.ImageAnnotatorClient()
    response = client.label_detection({
        'source': {'image_uri': image },
        })
    return response


def vision_quest_sms_in(request):
    """ incoming data should be a twilio sms blob.

    check db to see if we have a record for this phoneNum
        no: create record, send intro text and 1st quest
        yes: did they send a picture?
            no: chide them and remind them of the quest
            yes: save picture to gcs, id image
                is image = answer to quest?
                    no: ask them to try again, hint
                    yes: update db +1 level, grats user, send next quest txt
    """

    # create twilio text response object
    resp = MessagingResponse()

    # things printed to stdout will show up in google cloud logging
    #print(str(request.values))

    # strip the + and call it an int
    phoneNum = request.values['From'][1:]

    # have we seen this user before?
    userData = search_records(phoneNum)
    #print(phoneNum + ": " + str(userData))

    if userData is None:
        # user not found
        level = 0
        data = {"level": level}
        add_record(phoneNum, data)

        # respond to new user with first quest
        message = "Oh, hey, you found me!"
        message += "\n"
        message += questData[0]['query']
        resp.message(message)
        return str(resp)


    # otherwise, they exist, so let's continue their quest
    level = userData['level']

    # did they send us an image?
    if int(request.values['NumMedia']) != 0:
        # save image
        image = save_image(phoneNum, level, request.values['MediaUrl0'])

        # call cloud vision to analyze the image
        visionResponse = vision_query(image)
        #print(visionResponse.label_annotations)
        visionAnswers = []
        for label in visionResponse.label_annotations:
            visionAnswers.append(label.description.lower())

        # is the answer to the quest contained in the list of labels?
        if questData[level]['answer'] in visionAnswers:
            update_record(phoneNum, {"level": userData['level'] + 1})
            message = choice(goodJob)
            message += "\n"
            # so far only 5 quests, so send win message
            if userData['level'] + 1 >= 5:
                message += "You successfully saw through all my tricks and riddles! Congratulations, a winner is you :) :) :)"
                resp.message(message)
                return str(resp)

            message += questData[level + 1]['query']
            resp.message(message)
        else:
            # computer says no, they did not send a correct answer with their image
            message = choice(badJob)
            message += "\n"
            # maybe they can't figure out the riddle -- tell them what i want
            message += "Here's a hint, I'm looking for " + questData[level]['answer'] + "."
            resp.message(message)

        return str(resp)

    # if they didnt send us a picture, let's chide them
    elif int(request.values['NumMedia']) == 0:
        resp.message("What? I asked for a picture, not... this.  Try again.")
        return str(resp)
