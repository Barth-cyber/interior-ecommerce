# duct-ai-backend
Duct AI Backend for Interior Duct Ltd Website

## Render deployment and custom domain

This backend service should be deployed separately from the frontend service.
For the frontend hosted on `interiorductltd.com`, the backend should use a dedicated API subdomain, for example:

- `https://api.interiorductltd.com`

This repository is a Python Flask backend. In Render, use the `render.yaml` manifest and configure the service as a Python 3.11 web service.

If this service is already configured on Render as a Node.js service, the repository now includes a lightweight `package.json` shim to install Python dependencies and start `gunicorn`.

Set the `GEMINI_API_KEY` value in the Render dashboard under **Environment > Environment Variables**.

If you prefer, this backend also accepts `GOOGLE_API_KEY` or `GOOGLE_GEMINI_API_KEY` for Gemini.

If your website frontend is served from a different domain, embed the widget with the backend URL like this:

```html
<script src="duct-ai-widget.js" data-backend-url="https://api.interiorductltd.com"></script>
```

Do not put the Gemini key in any committed file.
