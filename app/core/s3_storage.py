import boto3 

from app.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET_NAME
)

class S3Storage:
    """
    Wraps all s3 interactions (upload, presigned down URL, delete)
    for storing pre-user resume files. One shared instance is created 
    at the bottom of this module and reused accross the app -- the
    underlying boto3 client is safe to resuse and expensive to recreate
    on every call.    
    """

    def __init__(self):
        self._client = boto3.client(
            "s3",
            aws_access_key_id = AWS_ACCESS_KEY_ID,
            aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
            region_name = AWS_REGION,
            endpoint_url = f"https://s3.{AWS_REGION}.amazonaws.com"
        )

        self._bucket = S3_BUCKET_NAME


    def upload_file(self, file_bytes: bytes, key: str , content_type : str = "application/pdf") -> str:
        """
        Upload file bytes to S3 under the gien key.
        Returns the key -- not a public URL, since the buxket is private
        and resumes must be accessed vai generate_presigned_url() instead.
        """
        self._client.put_object(
            Bucket = self._bucket,
            Key = key,
            Body = file_bytes,
            ContentType = content_type,
        )
        return key

    def generate_presigned_url(self,key:str, expires_in: int = 3600)-> str:
        """
        Generate a temporary, time-limited URL to donwload a private 
        s3 object -- lets a user view/download their own resume without making the bucket public.
        """
        return self._client.generate_presigned_url(
            "get_object",
            Params = { "Bucket": self._bucket, "Key": key},
            ExpiresIn = expires_in,
        )


    def delete_file(self, key:str)-> None:
        """
        Permanently deletes an object from S3.
        """

        self._client.delete_object(Bucket=self._bucket,Key=key)

    def download_file(self,key:str)-> bytes:
        """
        Downloads and returns the raw bytes of an  s3 object -- used to
        fetch a user's resume into memory for email attachment, without 
        evet writing it to local disk.
        """
        response = self._client.get_object(Bucket = self._bucket,Key=key)
        return response["Body"].read()


# Single shred instance -- import this , don't instantiate S3Storage()
# again elsewhere

s3_storage = S3Storage()


