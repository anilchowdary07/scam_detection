FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables with defaults
ENV API_BASE_URL=https://api.openai.com/v1
ENV MODEL_NAME=gpt-3.5-turbo
ENV OPENAI_API_KEY=""
ENV HF_TOKEN=""

# Expose port for Gradio UI
EXPOSE 7860

# Run server using the entry point defined in pyproject.toml
# This will call server.app:main()
CMD ["python", "-m", "server.app"]
