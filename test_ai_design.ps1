$headers = @{'Content-Type' = 'application/json'}
$body = '{"query":"Can you help me design my living room?","session_id":"test_user_design"}'
$response = Invoke-WebRequest -Uri 'http://localhost:5000/ai-query' -Method POST -Headers $headers -Body $body -UseBasicParsing
$response.Content | ConvertFrom-Json | ConvertTo-Json
