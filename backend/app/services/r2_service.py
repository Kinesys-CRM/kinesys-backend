import boto3
from botocore.config import Config
from app.core.config import settings

class R2Service:
    def __init__(self):

        # Connection Config
        self.s3_client = boto3.client(
            service_name='s3',
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(signature_version='s3v4')
        )

    def generate_upload_url(self, file_key: str, content_type: str = "image/jpeg"):
        """
        Generates a URL that the Frontend can use to PUT the file.
        Expires in 3600 seconds (1 hour).
        """
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': settings.R2_BUCKET_NAME,
                    'Key': file_key,
                    'ContentType': content_type
                },
                ExpiresIn=300
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def generate_read_url(self, file_key: str):
        """Generates a GET URL for the AI or User to view the file."""
        
        return self.s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': settings.R2_BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600
        )
        