output "connect_api_url" {
  value = module.connect_api.invoke_url
}

output "sns_topic_name" {
  value = var.sns_topic_name
}

output "bot_alias_id" {
  value = data.external.lex_bot_alias.result["alias_id"]
}
