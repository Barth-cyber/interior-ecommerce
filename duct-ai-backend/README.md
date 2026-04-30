# duct-ai-backend
Duct AI Backend for Interior Duct Ltd Website

## Render deployment and custom domain

This backend service should be deployed separately from the frontend service.
For the frontend hosted on `interiorductltd.com`, the backend should use a dedicated API subdomain, for example:

- `https://api.interiorductltd.com`

Use the Python backend defined by `render.yaml` in this repository. The service is started with Gunicorn and the production route is `/ai-query`.

In Render, configure the backend service to use that custom subdomain and set the `GEMINI_API_KEY`
value in the Render dashboard under **Environment > Environment Variables**.

Do not put the Gemini key in any committed file.
