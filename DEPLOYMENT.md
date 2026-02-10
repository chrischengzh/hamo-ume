# Hamo-UME AWS Deployment Guide

This guide covers deploying Hamo-UME backend to AWS with DynamoDB database.

## Architecture

- **Application**: AWS Elastic Beanstalk (Python)
- **Database**: Amazon DynamoDB (9 tables)
- **Infrastructure**: CloudFormation (IaC)

## Prerequisites

1. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```

2. **AWS Account** with permissions for:
   - CloudFormation
   - DynamoDB
   - Elastic Beanstalk
   - IAM

## Step 1: Deploy DynamoDB Tables

Use the CloudFormation template to create all DynamoDB tables:

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Deploy the tables (creates or updates)
./deploy-dynamodb.sh
```

This creates the following tables:
- `hamo_users` - User accounts (therapists and clients)
- `hamo_avatars` - Therapist avatars
- `hamo_ai_minds` - Client AI Mind profiles
- `hamo_psvs_profiles` - PSVS psychological tracking
- `hamo_conversation_sessions` - Chat sessions
- `hamo_conversation_messages` - Chat messages
- `hamo_client_avatar_connections` - Client-avatar relationships
- `hamo_invitations` - Invitation codes
- `hamo_refresh_tokens` - JWT refresh tokens

**Billing Mode**: Pay-per-request (no capacity planning needed)

## Step 2: Configure Elastic Beanstalk IAM Role

Your Elastic Beanstalk EC2 instances need permission to access DynamoDB.

### Option A: Using AWS Console

1. Go to **IAM Console** → **Roles**
2. Find your Elastic Beanstalk instance role (e.g., `aws-elasticbeanstalk-ec2-role`)
3. Attach policy: `AmazonDynamoDBFullAccess`

### Option B: Using AWS CLI

```bash
# Get your Elastic Beanstalk instance profile role name
ROLE_NAME=$(aws elasticbeanstalk describe-configuration-settings \
  --application-name hamo-ume \
  --environment-name hamo-ume-prod \
  --query 'ConfigurationSettings[0].OptionSettings[?OptionName==`IamInstanceProfile`].Value' \
  --output text)

# Attach DynamoDB policy
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

### Option C: Custom IAM Policy (Recommended - Least Privilege)

Create a custom policy with minimal permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/hamo_*",
        "arn:aws:dynamodb:us-east-1:*:table/hamo_*/index/*"
      ]
    }
  ]
}
```

## Step 3: Configure Environment Variables

Set environment variables in Elastic Beanstalk:

```bash
eb setenv AWS_REGION=us-east-1
eb setenv JWT_SECRET_KEY=your-production-secret-key-here
```

Or via AWS Console:
1. Go to **Elastic Beanstalk Console**
2. Select your environment
3. **Configuration** → **Software** → **Environment properties**
4. Add:
   - `AWS_REGION`: `us-east-1`
   - `JWT_SECRET_KEY`: (your secret key)

## Step 4: Deploy Application

```bash
# Install dependencies locally first
pip install -r requirements.txt

# Initialize Elastic Beanstalk (first time only)
eb init -p python-3.11 hamo-ume --region us-east-1

# Create environment (first time only)
eb create hamo-ume-prod

# Or deploy to existing environment
eb deploy
```

## Step 5: Verify Deployment

```bash
# Check application health
eb health

# View logs
eb logs

# Open application
eb open
```

Test the API:
```bash
curl https://your-app.elasticbeanstalk.com/
# Should return: {"message": "Welcome to Hamo-UME API"}
```

## Local Development with DynamoDB

### Option 1: Use AWS DynamoDB (Recommended)

Point to real AWS tables:
```bash
export AWS_REGION=us-east-1
export AWS_PROFILE=your-profile  # if using AWS profiles
uvicorn main:app --reload
```

### Option 2: Use DynamoDB Local

Run DynamoDB locally for development:

```bash
# Install DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Set environment variable
export DYNAMODB_ENDPOINT=http://localhost:8000

# Create tables locally
python init_dynamodb.py

# Start server
uvicorn main:app --reload
```

## Monitoring

### CloudWatch Logs

Logs are automatically sent to CloudWatch:
```bash
eb logs --cloudwatch-logs
```

### DynamoDB Metrics

Monitor table metrics in CloudWatch:
- Read/Write capacity units
- Latency
- Throttled requests

## Cost Optimization

### Pay-Per-Request Billing

The CloudFormation template uses **on-demand** billing mode:
- No minimum cost
- Pay only for what you use
- $1.25 per million write requests
- $0.25 per million read requests

### Estimated Costs (Low Traffic)

For 1,000 users with 10 messages/day:
- Writes: ~30K/month = $0.04
- Reads: ~60K/month = $0.02
- **Total: ~$0.06/month**

## Rollback

If you need to delete the DynamoDB tables:

```bash
aws cloudformation delete-stack \
  --stack-name hamo-ume-dynamodb \
  --region us-east-1
```

**⚠️ Warning**: This will permanently delete all data!

## Troubleshooting

### Error: "Unable to locate credentials"

**Solution**: Configure AWS CLI or ensure IAM role is attached to EC2 instances

```bash
aws configure
```

### Error: "ResourceNotFoundException: Requested resource not found"

**Solution**: Tables haven't been created. Run:
```bash
./deploy-dynamodb.sh
```

### Error: "AccessDeniedException"

**Solution**: EC2 instance role doesn't have DynamoDB permissions. See Step 2.

### Application can't connect to DynamoDB

**Check**:
1. Environment variable `AWS_REGION` is set
2. IAM role has DynamoDB permissions
3. Tables exist in the correct region

```bash
# List tables
aws dynamodb list-tables --region us-east-1
```

## Security Best Practices

1. **Use IAM Roles**: Never hardcode AWS credentials in code
2. **Least Privilege**: Use custom IAM policies instead of `FullAccess`
3. **Enable Encryption**: DynamoDB encryption at rest (enabled by default)
4. **VPC**: Consider placing DynamoDB VPC endpoints for private access
5. **Rotate Secrets**: Change `JWT_SECRET_KEY` regularly

## Next Steps

- [x] Deploy DynamoDB tables
- [x] Configure IAM permissions
- [x] Deploy application to Elastic Beanstalk
- [ ] Set up CloudWatch alarms for errors
- [ ] Configure auto-scaling (if using provisioned capacity)
- [ ] Set up CI/CD pipeline (GitHub Actions, CodePipeline)
- [ ] Enable DynamoDB Point-in-Time Recovery (backups)

## Support

For issues or questions:
- GitHub Issues: https://github.com/HamoAI/hamo-ume/issues
- Email: chris@hamo.ai
