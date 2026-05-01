$headers = @{'Content-Type' = 'application/json'}
$body = '{"query":"What materials do you use?","session_id":"test_user_123"}'
$response = Invoke-WebRequest -Uri 'http://localhost:5000/ai-query' -Method POST -Headers $headers -Body $body -UseBasicParsing
$response.Content | ConvertFrom-Json | ConvertTo-Json
