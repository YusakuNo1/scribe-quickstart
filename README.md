# Zoom AI Scribe API Quickstart

A Node.js/Express server for the [Zoom AI Scribe API](https://developers.zoom.us/docs/ai-services/scribe/) for speech-to-text transcription. It handles JWT authentication and exposes simple REST endpoints for **fast mode** (with file upload) and **batch jobs** (S3-based). Use the Vite playground to test the API with a web UI.

![screenshot](https://github.com/user-attachments/assets/6c99d0b4-f5bb-4cd0-8cca-f7a6bf1eb50e)

## Features

- **Sync transcription** — `POST /transcribe` with an audio/video file, returns transcript in the response.
- **Batch jobs** — Create, list, get, and delete Scribe batch jobs using S3 input/output buckets.
- **Webhooks** — `POST /webhooks/scribe` endpoint to receive job status notifications.

## Prerequisites

- A Zoom developer account for the Build platform
- For batch: IAM credentials to access an S3 bucket
- Node.js v24+

## Installation

```bash
git clone https://github.com/zoom/scribe-quickstart.git
cd scribe-quickstart
npm install
```

## Setup

1. Copy environment variables and add your [Zoom Build Platform](https://developers.zoom.us/docs/ai-services/build-platform/) and [AWS Security Token Service](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html) credentials:

   ```bash
   cp .env.example .env
   ```

You can use `scripts/generate-sts-creds.sh` to generate temporary AWS STS credentials using your IAM access key and secret key if you have the aws cli installed:

```bash
./scripts/generate-sts-creds.sh <AWS_ACCESS_KEY_ID> <AWS_SECRET_ACCESS_KEY>
```

This will generate a temporary AWS STS credentials and write them to the `.env` file.

2. Edit `.env` and set at minimum:

   | Variable          | Required | Description                                       |
   | ----------------- | -------- | ------------------------------------------------- |
   | `ZOOM_API_KEY`    | **Yes**  | Zoom Build platform API key                       |
   | `ZOOM_API_SECRET` | **Yes**  | Zoom Build platform API secret                    |
   | `PORT`            | No       | Server port (default: `4000`)                     |
   | `LANGUAGE`        | No       | Default transcription language (default: `en-US`) |

   For **batch jobs** you must also set:

   | Variable                | Required for batch  | Description                                  |
   | ----------------------- | ------------------- | -------------------------------------------- |
   | `S3_INPUT_URI`          | Yes                 | S3 URI for input files (e.g. `s3://bucket/`) |
   | `S3_OUTPUT_URI`         | Yes                 | S3 URI for output transcripts                |
   | `AWS_ACCESS_KEY_ID`     | Yes                 | AWS credentials for Scribe                   |
   | `AWS_SECRET_ACCESS_KEY` | Yes                 | AWS credentials for Scribe                   |
   | `AWS_SESSION_TOKEN`     | Yes (if using temp) | AWS session token                            |

   Optional:

   | Variable         | Description                       |
   | ---------------- | --------------------------------- |
   | `WEBHOOK_URL`    | URL for batch job status webhooks |
   | `WEBHOOK_SECRET` | Secret to verify webhook payloads |

3. Start the server:

   ```bash
   npm start
   ```

   The server runs at `http://localhost:4000` (or your `PORT`).

## Playground

A small web UI is provided to try transcription and batch jobs.

1. Start the API server (from the project root):

   ```bash
   npm run start
   ```

2. In another terminal, run the playground:

   ```bash
   cd playground && npm install && npm run dev
   ```

3. Open the URL shown by Vite (e.g. `http://localhost:5173`). If the API runs on a different origin, set the `API` base URL in `playground/src/shared.ts` (e.g. `export const API = 'http://localhost:4000'`) or use a Vite proxy to the API.


## Available Test Datasets

Example:
```console
python ./scripts/hf-dataset-download-extract.py --repo-id macabdul9/SuperbOODAsrSpon_CHIME6-Test
python ./scripts/hf-dataset-download-extract.py --repo-id argmaxinc/chime-6 --end-time 28
```

### The CHiME Challenges for OOV
* Short audios `macabdul9/SuperbOODAsrSpon_CHIME6-Test`
* Long audios, need to split `argmaxinc/chime-6`


## Need help?

- [Zoom AI Scribe documentation](https://developers.zoom.us/docs/ai-services/scribe)
- [API Reference](https://developers.zoom.us/docs/api/ai-services/)
- [Developer Support](https://devsupport.zoom.us) · [Developer Forum](https://devforum.zoom.us)
