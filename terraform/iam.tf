#fetch-raw-weather-data--mateirobescu
data "aws_iam_policy_document" "lambda_fetch_data_policy" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.openweather_api.arn]
  }

  statement {
    actions   = ["s3:PutObject", "s3:PutObjectAcl"]
    resources = ["${aws_s3_bucket.raw_weather_data.arn}/raw/*"]
  }
}

resource "aws_iam_role" "lambda_fetch_data_role" {
  name = "lambda_fetch_data_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_fetch_data_policy_attach" {
  name   = "lambda_fetch_data_policy_attach"
  role   = aws_iam_role.lambda_fetch_data_role.id
  policy = data.aws_iam_policy_document.lambda_fetch_data_policy.json
}

#invoke-fetch-weather-data--mateirobescu
data "aws_iam_policy_document" "lambda_invoke_fetch_data_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]
    resources = [aws_dynamodb_table.cities.arn]
  }

  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.fetch_weather.arn]
  }
}

resource "aws_iam_role" "lambda_invoke_fetch_data_role" {
  name = "lambda_invoke_fetch_data_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lamba_invoke_fetch_data_policy_attach" {
  name   = "lamba_invoke_fetch_data_policy_attach"
  role   = aws_iam_role.lambda_invoke_fetch_data_role.id
  policy = data.aws_iam_policy_document.lambda_invoke_fetch_data_policy.json
}

data "aws_iam_policy_document" "lambda_load_weather_policy" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:DeleteObject"
    ]
    resources = [aws_s3_bucket.raw_weather_data.arn, "${aws_s3_bucket.raw_weather_data.arn}/raw/*"]
  }

  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.rds_weather_data_credentials.arn]
  }
}

resource "aws_iam_role" "lambda_load_weather_role" {
  name = "lambda_load_weather_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_load_weather_policy_attach" {
  name   = "lambda_load_weather_policy_attach"
  role   = aws_iam_role.lambda_load_weather_role.id
  policy = data.aws_iam_policy_document.lambda_load_weather_policy.json
}

# Permission for logs
resource "aws_iam_role_policy_attachment" "lambda_logging_fetch" {
  role       = aws_iam_role.lambda_fetch_data_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_logging_invoke" {
  role       = aws_iam_role.lambda_invoke_fetch_data_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_vpc_access_policy" {
  name = "lambda-vpc-access-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access_invoke" {
  role       = aws_iam_role.lambda_invoke_fetch_data_role.name
  policy_arn = aws_iam_policy.lambda_vpc_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access_fetch" {
  role       = aws_iam_role.lambda_fetch_data_role.name
  policy_arn = aws_iam_policy.lambda_vpc_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access_load" {
  role       = aws_iam_role.lambda_load_weather_role.name
  policy_arn = aws_iam_policy.lambda_vpc_access_policy.arn
}

