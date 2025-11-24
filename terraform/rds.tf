resource "aws_db_instance" "weather_db" {
  identifier           = "weatherdata-db"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t4g.micro"
  allocated_storage    = 20
  storage_type         = "gp2"
  username             = "admin"
  password             = var.db_password
  parameter_group_name = "default.mysql8.0"

  db_name = "weather_data"

  publicly_accessible = false
  skip_final_snapshot = true
  deletion_protection = false

  vpc_security_group_ids = [aws_security_group.weather_rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.weather_db_subnets.name
}



resource "aws_security_group" "weather_rds_sg" {
  name        = "weather-rds-sg"
  description = "Allow MySQL access for weather project"
  vpc_id      = aws_vpc.weather_vpc.id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.weather_vpc.cidr_block]
    description = "Allow MySQL within VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}