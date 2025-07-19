# modules/secrets/outputs.tf
# Output values from secrets module

output "openai_api_key_secret_arn" {
  description = "ARN of the OpenAI API Key secret in AWS Secrets Manager"
  value       = aws_secretsmanager_secret.openai_api_key.arn
  sensitive   = true
}

output "openai_api_key_secret_id" {
  description = "ID of the OpenAI API Key secret in AWS Secrets Manager"
  value       = aws_secretsmanager_secret.openai_api_key.id
  sensitive   = true
}

output "openai_api_key_access_policy_json" {
  description = "IAM policy JSON for accessing the OpenAI API key secret"
  value       = data.aws_iam_policy_document.openai_api_key_access.json
}
