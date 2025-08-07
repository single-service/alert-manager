FROM python:3.12-slim

# set working dir
WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source
COPY app/ ./app

# default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]