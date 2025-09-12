output "invoke_url" {
  description = "API Gateway REST API URL"
  value       = aws_api_gateway_stage.stage.invoke_url
}

output "api_id" {
  description = "API Gateway REST API Id"
  value       = aws_api_gateway_rest_api.api.id
}

output "api_key" {
  description = "API Gateway REST API key"
  value       = aws_api_gateway_api_key.api_key.value
}
