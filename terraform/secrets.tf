resource "aws_secretsmanager_secret" "openweather_api" {
  name        = "OpenWeatherApi"
  description = "Stores OpenWeather API key"


}

resource "aws_secretsmanager_secret_version" "openweather_api_version" {
  secret_id     = aws_secretsmanager_secret.openweather_api.id
  secret_string = jsonencode({ API = "e935c342591fb715b2af4a51a9780a9e" })
}