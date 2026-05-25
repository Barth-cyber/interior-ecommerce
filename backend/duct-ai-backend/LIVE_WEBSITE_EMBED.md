# Live Website Embed Instructions

This backend repository does not include the live frontend website source, so the actual website embed cannot be updated here directly.

## Correct widget embed for the live site

Add the following snippet to your website HTML where you embed the chat widget:

```html
<script src="path/to/duct-ai-widget.js" data-backend-url="https://api.interiorductltd.com"></script>
```

### Notes
- `path/to/duct-ai-widget.js` should point to the widget JS file from this backend repo or its deployed public assets.
- `data-backend-url` must point to the deployed backend service URL, for example `https://api.interiorductltd.com`.
- The widget will now:
  - send prompts on `Enter`
  - use the configured backend URL instead of the page origin
  - load `duct-ai-widget.css` relative to the script location

## Optional alternative

If you cannot use the `data-backend-url` attribute, set a global variable before loading the widget:

```html
<script>
  window.DUCT_AI_BACKEND_URL = 'https://api.interiorductltd.com';
</script>
<script src="path/to/duct-ai-widget.js"></script>
```
