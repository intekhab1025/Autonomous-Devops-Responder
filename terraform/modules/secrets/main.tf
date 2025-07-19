# modules/secrets/main.tf
# AWS Secrets Manager resources

resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "${var.name_prefix}-openai-api-key"
  description = "OpenAI/OpenRouter API key for incident responder"
  tags        = var.common_tags
}

resource "aws_secretsmanager_secret_version" "openai_api_key_version" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

# IAM policy document for accessing the secret
data "aws_iam_policy_document" "openai_api_key_access" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [aws_secretsmanager_secret.openai_api_key.arn]
  }
}
