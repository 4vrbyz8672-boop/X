TANMAY FILE STORE — NEON POSTGRESQL BUILD

REQUIRED ENVIRONMENT VARIABLES
- BOT_TOKEN: a newly generated Telegram bot token from BotFather.
- DATABASE_URL: your Neon PostgreSQL connection string.
- PORT: optional; defaults to 8080 for the control website.

IMPORTANT SECURITY
- Never put real tokens/passwords in .env.example, source code, or Git commits.
- A token previously exposed in source/chat must be revoked in BotFather and replaced.
- A database connection string previously exposed must be rotated in Neon.

RUN LOCALLY
  pip install -r requirements.txt
  export BOT_TOKEN='your-new-token'
  export DATABASE_URL='your-neon-connection-string'
  python run.py

On Windows PowerShell use $env:BOT_TOKEN='...' and $env:DATABASE_URL='...'.

GITHUB
1. Repository Settings > Secrets and variables > Actions > New repository secret.
2. Add BOT_TOKEN and DATABASE_URL as separate secrets. Do not add them to .env.example.
3. GitHub Actions is suitable for syntax/validation jobs, not a permanent Telegram bot process.
4. Deploy run.py on a persistent Python host and set the same environment variables there.

The control website listens on PORT (default 8080). Keep web_admin.key private and protect the site with HTTPS/access controls.
The bot initializes its PostgreSQL schema at startup. Previous SQLite data is not automatically imported.
