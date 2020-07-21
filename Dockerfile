FROM python:3.8-slim@sha256:9a827faf80ac75c692525c67bc6cff0e6e4a4093e73ad2674d17584b0c645af8
RUN adduser --disabled-password --home /app --gecos '' appuser
WORKDIR /app
USER appuser
COPY requirements.txt .
ENV PATH $PATH:/app/.local/bin
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
