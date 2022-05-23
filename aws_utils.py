import io
import boto3
import os
from   dotenv import load_dotenv

load_dotenv()
AWS_ACCESS = os.getenv('AWS_ACCESS')
AWS_SECRET = os.getenv('AWS_SECRET')

BUCKET_PREFIX = "iufi"

resource = boto3.resource(
    's3',
    aws_access_key_id = AWS_ACCESS,
    aws_secret_access_key = AWS_SECRET,
    region_name = 'us-east-1'
)

def get_image(rarity, id):
    img = resource.Object(
        bucket_name = f"{BUCKET_PREFIX}-{rarity}",
        key = f"{id}.jpg"
    )
    img_data = img.get().get('Body').read()
    return io.BytesIO(img_data)