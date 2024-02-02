# UniMarket Place Project

## Overview

This project is a web application that integrates with AWS services and Firebase for backend operations. It is designed to be secure, with sensitive information such as API keys and secrets stored in environment variables.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.x
- Pip package manager
- Firebase account
- AWS account

## Installation

To set up the project environment, follow these steps:

1. Clone the repository:

```
git clone https://github.com/kukr/UniMarket-Place.git
```

2. Navigate to the project directory:

```
cd cs409_project
```

3. Install the required Python packages:

```
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root of your project directory with the following content, replacing the placeholders with your actual keys and secrets:

```
AWS_ACCESS_KEY=your_aws_access_key_here
AWS_SECRET_KEY=your_aws_secret_key_here
FIREBASE_API_KEY=your_firebase_api_key_here
FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain_here
FIREBASE_DATABASE_URL=your_firebase_database_url_here
FIREBASE_PROJECT_ID=your_firebase_project_id_here
FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket_here
FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id_here
FIREBASE_APP_ID=your_firebase_app_id_here
SECRET_KEY=your_secret_key_here
```

## Usage

To run the application, execute:

```
python app.py
```

## Contributing

To contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your_feature`).
3. Make changes and commit (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your_feature`).
5. Create a new Pull Request.

## Security

Sensitive data such as API keys and secrets are stored in environment variables and are not tracked in the version control system. Ensure that the `.env` file is included in `.gitignore`.

## License

This project is licensed under the [MIT License](LICENSE).
