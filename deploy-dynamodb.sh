#!/bin/bash
# Deploy DynamoDB tables to AWS using CloudFormation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="hamo-ume-dynamodb"
TEMPLATE_FILE="cloudformation-dynamodb.yaml"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Hamo-UME DynamoDB Tables${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: Template file '$TEMPLATE_FILE' not found${NC}"
    exit 1
fi

# Validate CloudFormation template
echo -e "${YELLOW}Validating CloudFormation template...${NC}"
aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE \
    --region $REGION > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Template is valid${NC}"
else
    echo -e "${RED}✗ Template validation failed${NC}"
    exit 1
fi

# Check if stack already exists
STACK_EXISTS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION 2>&1 || true)

if echo "$STACK_EXISTS" | grep -q "does not exist"; then
    # Create new stack
    echo -e "${YELLOW}Creating new CloudFormation stack...${NC}"
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --region $REGION \
        --tags Key=Application,Value=Hamo-UME Key=ManagedBy,Value=CloudFormation

    echo -e "${YELLOW}Waiting for stack creation to complete...${NC}"
    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME \
        --region $REGION

    echo -e "${GREEN}✓ Stack created successfully${NC}"
else
    # Update existing stack
    echo -e "${YELLOW}Updating existing CloudFormation stack...${NC}"
    UPDATE_OUTPUT=$(aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --region $REGION 2>&1 || true)

    if echo "$UPDATE_OUTPUT" | grep -q "No updates are to be performed"; then
        echo -e "${GREEN}✓ No changes detected - stack is up to date${NC}"
    else
        echo -e "${YELLOW}Waiting for stack update to complete...${NC}"
        aws cloudformation wait stack-update-complete \
            --stack-name $STACK_NAME \
            --region $REGION

        echo -e "${GREEN}✓ Stack updated successfully${NC}"
    fi
fi

# Display stack outputs
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Stack Outputs:${NC}"
echo -e "${GREEN}========================================${NC}"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Configure Elastic Beanstalk environment variables:"
echo "   - AWS_REGION=$REGION"
echo "2. Deploy your application to Elastic Beanstalk"
echo "3. The application will automatically use the DynamoDB tables"
echo ""
