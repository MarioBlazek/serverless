from datetime import datetime
import boto3
from io import BytesIO
from PIL import Image, ImageOps
import os
import uuid
import json

s3 = boto3.client('s3')
size = int(os.environ['THUMBNAIL_SIZE'])
db_table = str(os.environ['DYNAMODB_TABLE'])
dynamodb = boto3.resource('dynamodb', region_name=str(os.environ['REGION_NAME']))


def get_dynamodb_table():
    return dynamodb.Table(db_table)


def s3_thumbnail_generator(event, context):
    print("EVENT:::", event)

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    image_size = event['Records'][0]['s3']['object']['size']

    if not key.endswith("_thumbnail.png"):
        image = get_s3_image(bucket, key)
        thumbnail = image_to_thumbnail(image)
        thumbnail_key = new_filename(key)

        print('Uploading to S3')
        url = upload_to_s3(bucket, thumbnail_key, thumbnail, image_size)
        print('Done')

        return url

    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    return {"statusCode": 200, "body": json.dumps(body)}


def s3_save_thumbnail_url_to_dynamo(url_path, img_size):
    to_int = float(img_size * 0.53) / 1000
    table = get_dynamodb_table()

    response = table.put_item(
        Item={
            'id': str(uuid.uuid4()),
            'url': str(url_path),
            'approxReducedSize': str(to_int) + str(' KB'),
            'createdAt': str(datetime.now()),
            'updatedAt': str(datetime.now())
        }
    )

    print('DYNAMODB_RESPONSE::', response)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response)
    }


def get_s3_image(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    image_content = response['Body'].read()

    file = BytesIO(image_content)
    img = Image.open(file)

    return img


def image_to_thumbnail(image):
    return ImageOps.fit(image, (size, size), Image.ANTIALIAS)


def new_filename(key):
    key_split = key.rsplit('.', 1)
    return key_split[0] + "_thumbnail.png"


def upload_to_s3(bucket, key, image, img_size):
    out_thumbnail = BytesIO()

    image.save(out_thumbnail, 'PNG')
    out_thumbnail.seek(0)

    response = s3.put_object(
        ACL='public-read',
        Body=out_thumbnail,
        Bucket=bucket,
        ContentType='image/png',
        Key=key
    )

    print(response)

    url = '{}/{}/{}'.format(s3.meta.endpoint_url, bucket, key)

    s3_save_thumbnail_url_to_dynamo(url_path=url, img_size=img_size)

    return url


def s3_get_item(event, context):
    table = get_dynamodb_table()

    response = table.get_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )

    item = response['Item']

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(item),
        "isBase64Encoded": False
    }


def s3_delete_item(event, context):
    item_id = event['pathParameters']['id']

    response = {
        "statusCode": 500,
        "body": f"An error occurred while deleting post {item_id}"
    }

    table = get_dynamodb_table()
    dynamodb_response = table.delete_item(
        Key={
            'id': item_id
        }
    )

    all_good_response = {
        "deleted": True,
        "itemDeletedId": item_id
    }

    if dynamodb_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(all_good_response)
        }

    return response


def s3_get_thumbnail_urls(event, context):
    table = get_dynamodb_table()
    response = table.scan()

    data = response['Items']

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(data),
    }
