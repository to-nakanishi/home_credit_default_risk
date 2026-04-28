FROM public.ecr.aws/lambda/python:3.11
 
RUN pip install --no-cache-dir \
    lightgbm==4.3.0 \
    numpy \
    scipy
 
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/
 
CMD ["lambda_function.lambda_handler"]
 
