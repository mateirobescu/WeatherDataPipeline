resource "random_password" "app_api_key" {
  length  = 32
  special = false
}

output "react_app_api_key" {
  value     = random_password.app_api_key.result
  sensitive = true
}