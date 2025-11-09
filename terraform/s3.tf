resource "aws_s3_bucket" "raw_weather_data" {
  bucket        = "raw-weather-data--mateirobescu"
  force_destroy = true

  tags = {
    Name = "Raw Weather Data Bucket"
  }
}