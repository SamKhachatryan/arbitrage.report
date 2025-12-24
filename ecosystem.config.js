module.exports = {
  apps: [{
    name: 'arbitrage-bot',
    script: '.venv/bin/python',
    args: 'bot.py',
    cwd: '/root/projects/arbitrage.report',
    interpreter: 'none',
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
