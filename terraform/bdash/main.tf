terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-west-1"
  access_key = var.AWS_ACCESS_KEY
  secret_key = var.AWS_SECRET_ACCESS_KEY
}

resource "aws_vpc" "bdash_vpc" {
  cidr_block = "10.0.0.0/24"
  tags = {
    Name = "bdash_vpc"
  }
}
