resource "aws_secretsmanager_secret" "openweather_api" {
  name        = "OpenWeatherApi"
  description = "Stores OpenWeather API key"
}

resource "aws_secretsmanager_secret_version" "openweather_api_version" {
  secret_id     = aws_secretsmanager_secret.openweather_api.id
  secret_string = jsonencode({ API = var.openweather_api_key })
}

resource "aws_secretsmanager_secret" "rds_weather_data_credentials" {
  name        = "RdsWeatherDataCredentials"
  description = "Stores Rds Weather Data Credentials"
}

resource "aws_secretsmanager_secret_version" "rds_weather_data_credentials_version" {
  secret_id = aws_secretsmanager_secret.rds_weather_data_credentials.id
  secret_string = jsonencode({
    USER : var.rds_user,
    PASSWORD : var.rds_pass,
    HOST : var.rds_host,
    DBNAME : var.rds_dbname
  })
}