FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN groupadd -g 1000 appuser && useradd -r -u 1000 -g appuser appuser
RUN mkdir /app && chown appuser -R /app
WORKDIR /app
ENV HOME /app

COPY --chown=appuser requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser . /app/
EXPOSE 5000
USER appuser

CMD ["waitress-serve", "--port=5000", "--call", "server:create_app"]
