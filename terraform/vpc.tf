resource "aws_vpc" "weather_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "weather-vpc"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id            = aws_vpc.weather_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.region}a"

  map_public_ip_on_launch = true

  tags = {
    Name = "weather-public-subnet"
  }
}

resource "aws_subnet" "private_lambda_subnet" {
  vpc_id            = aws_vpc.weather_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.region}a"

  map_public_ip_on_launch = false

  tags = {
    Name = "weather-private-lambda-subnet"
  }
}

resource "aws_subnet" "private_rds_subnet1" {
  vpc_id            = aws_vpc.weather_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "${var.region}a"

  map_public_ip_on_launch = false

  tags = {
    Name = "weather-private-rds-subnet"
  }
}

resource "aws_subnet" "private_rds_subnet2" {
  vpc_id            = aws_vpc.weather_vpc.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "${var.region}b"

  map_public_ip_on_launch = false

  tags = {
    Name = "weather-private-rds-subnet"
  }
}

resource "aws_db_subnet_group" "weather_db_subnets" {
  name = "weather-db-subnet-group"
  subnet_ids = [
    aws_subnet.private_rds_subnet1.id,
    aws_subnet.private_rds_subnet2.id
  ]
}

resource "aws_internet_gateway" "weather_igw" {
  vpc_id = aws_vpc.weather_vpc.id

  tags = {
    Name = "weather-igw"
  }
}

resource "aws_eip" "nat_eip" {
  domain = "vpc"
}

resource "aws_nat_gateway" "weather_nat" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_subnet.id

  tags = {
    Name = "weather-nat"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.weather_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.weather_igw.id
  }

  tags = {
    Name = "weather-public-rt"
  }
}

resource "aws_route_table_association" "public_rt_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.weather_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.weather_nat.id
  }

  tags = {
    Name = "weather-private-rt"
  }
}

resource "aws_route_table_association" "private_lambda_assoc" {
  subnet_id      = aws_subnet.private_lambda_subnet.id
  route_table_id = aws_route_table.private_rt.id
}

resource "aws_route_table_association" "private_rds_assoc1" {
  subnet_id      = aws_subnet.private_rds_subnet1.id
  route_table_id = aws_route_table.private_rt.id
}

resource "aws_route_table_association" "private_rds_assoc2" {
  subnet_id      = aws_subnet.private_rds_subnet2.id
  route_table_id = aws_route_table.private_rt.id
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id             = aws_vpc.weather_vpc.id
  service_name       = "com.amazonaws.${var.region}.secretsmanager"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.private_lambda_subnet.id]
  security_group_ids = [aws_security_group.lambda_sg.id]
}