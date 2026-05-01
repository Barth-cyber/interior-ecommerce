$headers = @{'Content-Type' = 'application/json'}
$body = '{"query":"I need a new sofa for my living room. What sofas do you have?","session_id":"test_user_sofa"}'
$response = Invoke-WebRequest -Uri 'http://localhost:5000/ai-query' -Method POST -Headers $headers -Body $body -UseBasicParsing
$response.Content | ConvertFrom-Json | ConvertTo-Json
