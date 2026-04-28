name: Deploy to AWS Lambda

on:
  push:
    branches: [main]
    paths:
      - 'deploy/**'
  workflow_dispatch:

env:
  AWS_REGION: ap-northeast-1
  ECR_REPOSITORY: home-credit-predictor
  LAMBDA_FUNCTION: home-credit-predictor

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image to ECR
        working-directory: deploy
        run: |
          IMAGE_URI=${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com/${{ env.ECR_REPOSITORY }}:latest
          docker build -t $IMAGE_URI .
          docker push $IMAGE_URI
          echo "IMAGE_URI=$IMAGE_URI" >> $GITHUB_ENV

      - name: Deploy Lambda function
        run: |
          # Image型Lambdaならupdate、zip型なら削除→再作成
          PACKAGE_TYPE=$(aws lambda get-function-configuration \
            --function-name ${{ env.LAMBDA_FUNCTION }} \
            --query 'PackageType' --output text 2>/dev/null || echo "NOT_FOUND")

          if [ "$PACKAGE_TYPE" = "Image" ]; then
            aws lambda update-function-code \
              --function-name ${{ env.LAMBDA_FUNCTION }} \
              --image-uri ${{ env.IMAGE_URI }}
          else
            aws lambda delete-function \
              --function-name ${{ env.LAMBDA_FUNCTION }} 2>/dev/null || true
            aws lambda create-function \
              --function-name ${{ env.LAMBDA_FUNCTION }} \
              --package-type Image \
              --code ImageUri=${{ env.IMAGE_URI }} \
              --role arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/home-credit-lambda-role \
              --timeout 60 \
              --memory-size 1024 \
              --environment "Variables={MODEL_BUCKET=my-home-credit-model-2026-tn,MODEL_KEY=models/lgbm_fold0.pkl,THRESHOLD=0.24}"
          fi
