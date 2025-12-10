# Stateless App Runner

A lightweight, stateless application runner built with FastAPI. This service allows you to execute HTML/JS applications that are encoded directly into the URL, ensuring that the application state is contained entirely within the link itself.

## Features

- **Stateless Execution**: Applications are delivered via URL parameters.
- **Security**: URL payloads are signed with a server-side secret key to prevent tampering.
- **Compression**: Payloads are zlib-compressed to minimize URL length.
- **Admin Interface**: Built-in tool to generate signed links from HTML/JS code.
- **Dockerized**: Ready to deploy with Docker and Docker Compose.

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Clone the repository and navigate to the project root.
2. Start the service:

   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - **Runner**: `http://localhost/` (will show a default message if no payload is provided)
   - **Admin/Generator**: `http://localhost/admin`

### Generating a Link

1. Go to `http://localhost/admin`.
2. Enter the HTML/JS code you want to run.
3. Click "Generate".
4. The system will provide a signed URL. Opening this URL will render and execute your code.

## Configuration

The application is configured via environment variables in `docker-compose.yml`:

- `APP_DOMAIN`: The base domain for generated links (default: `http://mtlminiapps.us`).
- `SECRET_KEY`: A secret key used to sign and verify payloads.
  - **Important**: If not set, the server will generate a random key on startup and log it to the console. For production consistency, set this variable.

## Development

To run tests locally:

```bash
# Install dependencies
pip install -r app/requirements.txt

# Run tests
pytest
```

## How it Works

1. **Compression**: The HTML content is compressed using `zlib` (level 9).
2. **Encoding**: The compressed data is encoded using `base64` (URL-safe).
3. **Signing**: An HMAC-SHA256 signature is generated using the `SECRET_KEY`.
4. **Execution**: When the link is opened, the server verifies the signature, decodes, decompresses, and serves the content.
