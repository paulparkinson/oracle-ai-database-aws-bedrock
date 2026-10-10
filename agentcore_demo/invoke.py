"""IAM-signed client. Use the same session for generate and reviewed execute."""
import argparse
import json
import uuid
import boto3
from botocore.config import Config

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-arn", required=True)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--session", default=None)
    parser.add_argument("payload", help="JSON operation payload; never credentials")
    args = parser.parse_args()
    session = args.session or str(uuid.uuid4())
    client = boto3.client("bedrock-agentcore", region_name=args.region,
                         config=Config(read_timeout=180, retries={"total_max_attempts": 1}))
    response = client.invoke_agent_runtime(agentRuntimeArn=args.runtime_arn,
        runtimeSessionId=session, contentType="application/json",
        payload=json.dumps(json.loads(args.payload)).encode())
    print("Session:", session)
    print(response["response"].read().decode())

if __name__ == "__main__":
    main()

