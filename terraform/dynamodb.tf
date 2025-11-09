resource "aws_dynamodb_table" "cities" {
  name         = "OpenWeather-cities"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ow-id"

  attribute {
    name = "ow-id"
    type = "S"
  }
}