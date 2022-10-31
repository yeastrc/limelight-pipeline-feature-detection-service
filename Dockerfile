FROM python:3

ARG IMAGE_APP_DIR=/usr/src/app

ENV APP_WORKDIR=/data/app/workdir
ENV FINAL_DIR=/data/app/finaldir
ENV HARDKLOR_EXEC_PATH=${IMAGE_APP_DIR}/bin/hardklor
ENV BULLSEYE_EXEC_PATH=${IMAGE_APP_DIR}/bin/bullseye

WORKDIR ${IMAGE_APP_DIR}

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod 755 ./bin/hardklor && chmod 755 ./bin/bullseye

CMD [ "python", "-u", "./start_service.py" ]
