# Deploy to an EC2 server

This guide deploys the Flask quote generator to an Ubuntu EC2 instance and serves it at `pathon.successlink.com.ng` using Gunicorn, Nginx, and HTTPS.

## 1. Configure EC2 and DNS

1. In the EC2 console, confirm the instance is running Ubuntu 22.04 or 24.04 and note its public IP. The deployment target provided for this app is `34.200.213.243`.
2. For a stable DNS target, associate an Elastic IP with the instance. A normal EC2 public IP can change when the instance is stopped and started.
3. In the instance's security group, allow inbound:
   - SSH (TCP 22) only from your own IP address.
   - HTTP (TCP 80) from `0.0.0.0/0` and `::/0`.
   - HTTPS (TCP 443) from `0.0.0.0/0` and `::/0`.
4. In the DNS zone for `successlink.com.ng`, add an A record for `pathon` pointing to `34.200.213.243` (or the associated Elastic IP). Wait for DNS to propagate. From a machine with `dig`, check with:

   ```bash
   dig +short pathon.successlink.com.ng
   ```

   It should return the instance's public/Elastic IP.

## 2. Connect and install system packages

From your local machine, connect using the EC2 key pair and the Ubuntu account. Replace the key path with the path to your `.pem` file:

```bash
ssh -i /path/to/key.pem ubuntu@34.200.213.243
```

On the instance:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx
```

## 3. Install the application

Clone the repository and create an isolated Python environment:

```bash
cd /opt
sudo git clone https://github.com/realsuccess40/random-quote-generator-python-app.git
sudo chown -R ubuntu:ubuntu /opt/random-quote-generator-python-app
cd /opt/random-quote-generator-python-app

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
deactivate
```

## 4. Run Gunicorn with systemd

Create a systemd service:

```bash
sudo tee /etc/systemd/system/quote-app.service > /dev/null <<'EOF'
[Unit]
Description=Gunicorn service for the random quote Flask app
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/opt/random-quote-generator-python-app
ExecStart=/opt/random-quote-generator-python-app/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 --access-logfile - --error-logfile - app:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now quote-app
sudo systemctl status quote-app --no-pager
```

Gunicorn listens only on the instance's loopback interface; Nginx will accept public web traffic and forward it to Gunicorn. The Flask development server and debug mode are not used in production.

## 5. Configure Nginx

Create an Nginx site configuration:

```bash
sudo tee /etc/nginx/sites-available/quote-app > /dev/null <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name pathon.successlink.com.ng;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/quote-app /etc/nginx/sites-enabled/quote-app
sudo nginx -t
sudo systemctl reload nginx
```

If the default Nginx welcome page takes precedence, remove the default enabled site and reload:

```bash
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

At this point, test `http://pathon.successlink.com.ng` in a browser.

## 6. Enable HTTPS

After DNS resolves to the instance and inbound TCP 80/443 are allowed, install Certbot and request a Let's Encrypt certificate:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d pathon.successlink.com.ng
```

Follow the prompts and choose the option to redirect HTTP traffic to HTTPS. Test automatic renewal:

```bash
sudo certbot renew --dry-run
```

The application should now be available at `https://pathon.successlink.com.ng`.

## Updating the application

To deploy the latest code from the repository:

```bash
cd /opt/random-quote-generator-python-app
git pull
. .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
deactivate
sudo systemctl restart quote-app
sudo systemctl status quote-app --no-pager
```

## Troubleshooting

- Check application logs with `sudo journalctl -u quote-app -n 100 --no-pager`.
- Check Nginx logs with `sudo tail -n 100 /var/log/nginx/error.log`.
- Check the service with `sudo systemctl status quote-app --no-pager` and Nginx config with `sudo nginx -t`.
- If the domain does not load, confirm the A record resolves to the instance's current public/Elastic IP and the security group allows ports 80 and 443.
