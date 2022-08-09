import json
import boto3
import os
# from PIL import Image, ImageDraw, ExifTags, ImageColor, ImageFont

def start_model(project_arn, model_arn, version_name, min_inference_units):
    client = boto3.client('rekognition')

    try:
        # Start the model
        print('Starting model: ' + model_arn)
        response = client.start_project_version(ProjectVersionArn=model_arn, MinInferenceUnits=min_inference_units)
        # Wait for the model to be in the running state
        project_version_running_waiter = client.get_waiter('project_version_running')
        project_version_running_waiter.wait(ProjectArn=project_arn, VersionNames=[version_name])

        # Get the running status
        describe_response = client.describe_project_versions(ProjectArn=project_arn,
                                                             VersionNames=[version_name])
        for model in describe_response['ProjectVersionDescriptions']:
            print("Status: " + model['Status'])
            print("Message: " + model['StatusMessage'])
    except Exception as e:
        print(e)

    print('Done...')

def show_custom_labels(model,bucket,photo, min_confidence):
    client=boto3.client('rekognition')

    #Call DetectCustomLabels
    response = client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
        MinConfidence=min_confidence,
        ProjectVersionArn=model)

    # For object detection use case, uncomment below code to display image.
    # display_image(bucket,photo,response)

    return response['CustomLabels'], len(response['CustomLabels'])

def stop_model(model_arn):

    client=boto3.client('rekognition')

    print('Stopping model:' + model_arn)

    #Stop the model
    try:
        response=client.stop_project_version(ProjectVersionArn=model_arn)
        status=response['Status']
        print ('Status: ' + status)
    except Exception as e:
        print(e)

    print('Done...')

def lambda_handler(event, context):
    project_arn = os.environ['project_arn']
    model_arn =os.environ['model_arn']
    try:
        s3_records = event['Records']
        print(s3_records)
        # Start Model
        min_inference_units=1
        version_name= os.environ['version_name']
        start_model(project_arn, model_arn, version_name, min_inference_units)
        responses = []

        # Analyze Image
        min_confidence = 95
        for record in s3_records:
            bucket = record['s3']['bucket']['name']
            photo = record['s3']['object']['key']
            response, label_count = show_custom_labels(model_arn, bucket, photo, min_confidence)
            responses.append({
                'Key': photo,
                'Response': response,
                'Label_Count': label_count
            })
            print("Custom labels detected: " + str(label_count))

        output = {
            "statusCode": 200,
            "body": json.dumps({
                "response": responses
            }),
        }

        print(f"Predictions: {output}")
        return output
    except Exception as e:
        raise e

    finally:
        # Stop Model
        stop_model(model_arn)
