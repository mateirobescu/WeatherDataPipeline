#fetch-raw-weather-data--mateirobescu
resource "aws_lambda_function" "fetch_weather" {
  function_name = "fetch-raw-weather-data--mateirobescu"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  filename = "${path.module}/../lambda_functions/fetch_weather.zip"
  role     = aws_iam_role.lambda_fetch_data_role.arn

  timeout          = 30
  memory_size      = 256
  source_code_hash = filebase64sha256("${path.module}/../lambda_functions/fetch_weather.zip")

  environment {
    variables = {
      REGION = var.region
      BUCKET = aws_s3_bucket.raw_weather_data.bucket
      SECRET = aws_secretsmanager_secret.openweather_api.name
    }
  }

  depends_on = [
    aws_iam_role.lambda_fetch_data_role,
    aws_s3_bucket.raw_weather_data,
    aws_secretsmanager_secret.openweather_api
  ]

  vpc_config {
    security_group_ids = [aws_security_group.lambda_sg.id]
    subnet_ids         = [aws_subnet.private_lambda_subnet.id]
  }
}

#invoke-fetch-weather-data--mateirobescu
resource "aws_lambda_function" "invoke_fetch_weather" {
  function_name = "invoke-fetch-weather-data--mateirobescu"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  filename = "${path.module}/../lambda_functions/invoker.zip"
  role     = aws_iam_role.lambda_invoke_fetch_data_role.arn

  timeout          = 30
  memory_size      = 256
  source_code_hash = filebase64sha256("${path.module}/../lambda_functions/invoker.zip")

  depends_on = [
    aws_iam_role.lambda_invoke_fetch_data_role,
    aws_dynamodb_table.cities,
    aws_lambda_function.fetch_weather
  ]

  vpc_config {
    security_group_ids = [aws_security_group.lambda_sg.id]
    subnet_ids         = [aws_subnet.private_lambda_subnet.id]
  }
}

resource "aws_lambda_function" "load-weather-to-rds--mateirobescu" {
  function_name = "load-weather-to-rds--mateirobescu"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  filename = "${path.module}/../lambda_functions/load_weather.zip"
  role     = aws_iam_role.lambda_load_weather_role.arn

  timeout          = 30
  memory_size      = 256
  source_code_hash = filebase64sha256("${path.module}/../lambda_functions/load_weather.zip")

  depends_on = [
    aws_iam_role.lambda_load_weather_role,
    aws_s3_bucket.raw_weather_data,
    aws_db_instance.weather_db
  ]

  vpc_config {
    security_group_ids = [aws_security_group.lambda_sg.id]
    subnet_ids         = [aws_subnet.private_lambda_subnet.id]
  }
}

resource "aws_security_group_rule" "lambda_to_rds" {
  type      = "ingress"
  from_port = 3306
  to_port   = 3306
  protocol  = "tcp"

  security_group_id        = aws_security_group.weather_rds_sg.id
  source_security_group_id = aws_security_group.lambda_sg.id
}

resource "aws_security_group" "lambda_sg" {
  name        = "lambda-sg"
  description = "Security group for Lambda inside private subnet"
  vpc_id      = aws_vpc.weather_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    self      = true
  }

  tags = {
    Name = "lambda-sg"
  }
}