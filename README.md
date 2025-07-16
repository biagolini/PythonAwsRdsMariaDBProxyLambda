# Lambda RDS Proxy Integration (MariaDB)

This repository contains a Python-based AWS Lambda function integrated with **Amazon RDS Proxy** and **MariaDB**, designed for stateless CRUD operations via **API Gateway**. It demonstrates secure, scalable access to a managed relational database using best practices such as **AWS Secrets Manager** for credential storage.

**Requirements:** Python 3.10+ (uses match statements)

This code supports basic `GET`, `POST`, `PUT`, and `DELETE` operations on a `users` table in MariaDB.

---

## Tutorial

This project is part of a hands-on tutorial published on my Medium blog:

**Read the full tutorial here:** [https://medium.com/@biagolini](https://medium.com/@biagolini)

There you'll find a complete step-by-step guide, including:

* Setting up MariaDB, RDS Proxy, and Secrets Manager
* Creating required IAM roles and security groups
* Deploying this Lambda function and configuring VPC access

For full configuration and deployment instructions, please refer to the article.

---

## Project Structure

* `lambda_function.py`: Main Lambda function source code
* Uses environment variables to configure DB host, port, secret name, and DB name
* Connects through RDS Proxy using credentials stored in Secrets Manager
* SQL queries are parameterized for security

---

## Deployment Requirements

You must package this Lambda function with its dependencies (e.g., `pymysql`) as a Lambda Layer.

### Build Lambda Layer with Docker

```bash
# Step 1: Ensure Docker is available
docker --version

# Step 2: Build the Docker image
docker build -t lambda_layer .

# Step 3: Run a container to export the dependencies
docker run --name my_lambda_layer_container lambda_layer

# Step 4: Copy the zip file from container to local
docker cp my_lambda_layer_container:/home/lambda_dependencies.zip .

# Step 5: (Optional) Cleanup
docker stop my_lambda_layer_container
docker rm my_lambda_layer_container
docker rmi lambda_layer
```

