resource "aws_s3_bucket" "weather_data_bucket" {
  bucket        = "weather-data-bucket--mateirobescu"
  force_destroy = true

  tags = {
    Name = "Raw Weather Data Bucket"
  }
}

resource "aws_s3_bucket_notification" "raw_bucket_notifications" {
  bucket = aws_s3_bucket.weather_data_bucket.bucket

  lambda_function {
    lambda_function_arn = aws_lambda_function.load-weather-to-rds--mateirobescu.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
  }

  depends_on = [
    aws_lambda_permission.allow_s3_invoke
  ]
}

resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.load-weather-to-rds--mateirobescu.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.weather_data_bucket.arn
}