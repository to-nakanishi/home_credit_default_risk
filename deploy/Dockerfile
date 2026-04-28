FROM public.ecr.aws/lambda/python:3.12

RUN pip install --no-cache-dir --only-binary :all: \
    lightgbm==4.3.0 \
    numpy \
    scipy

COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_function.lambda_handler"]
