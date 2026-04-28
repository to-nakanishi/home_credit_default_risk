import json
import pickle
import os
import boto3
import numpy as np

model = None
feature_names = None

BUCKET_NAME = os.environ.get('MODEL_BUCKET', 'my-home-credit-model-2026-tn')
MODEL_KEY = os.environ.get('MODEL_KEY', 'models/lgbm_fold0.pkl')
THRESHOLD = float(os.environ.get('THRESHOLD', '0.24'))


def load_model():
    global model, feature_names
    s3 = boto3.client('s3')
    s3.download_file(BUCKET_NAME, MODEL_KEY, '/tmp/model.pkl')
    with open('/tmp/model.pkl', 'rb') as f:
        model = pickle.load(f)
    feature_names = model.feature_name()


def lambda_handler(event, context):
    global model, feature_names

    if model is None:
        try:
            load_model()
        except Exception as e:
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        features = body.get('features', {})
    except:
        return {'statusCode': 400, 'body': json.dumps({'error': 'invalid request'})}

    input_array = np.array(
        [[features.get(name, 0) for name in feature_names]], dtype=np.float64
    )
    probability = float(model.predict(input_array)[0])
    decision = "auto_approve" if probability < THRESHOLD else "manual_review"

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'probability': round(probability, 6),
            'threshold': THRESHOLD,
            'decision': decision,
            'features_received': len(features)
        })
    }
