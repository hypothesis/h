daemon off;
worker_processes auto;
pid /var/lib/hypothesis/nginx.pid;
error_log /dev/stderr;

events {
  worker_connections 4096;
}

http {
  client_max_body_size 20m;
  sendfile on;
  server_tokens off;

  include mime.types;
  default_type application/octet-stream;

  access_log off;

  # Dynamic DNS resolution of upstream hostnames requires a resolver to be set.
  ${RESOLVER_DIRECTIVES}

  # We set fail_timeout=0 so that the upstream isn't marked as down if a single
  # request fails (e.g. if gunicorn kills a worker for taking too long to handle
  # a single request).
  upstream web { server unix:/tmp/gunicorn-web.sock fail_timeout=0; }
  upstream websocket { server unix:/tmp/gunicorn-websocket.sock fail_timeout=0; }

  server {
    listen 5000;

    server_name _;
    server_tokens off;

    root /var/www;

    rewrite ^/index\.html$ / permanent;
    rewrite ^/app/embed.js /embed.js;
    rewrite ^/minutes/(\d+)/(.*) https://hypothesis-meeting-logs.s3.amazonaws.com/$1/$2 redirect;
    rewrite ^/minutes/(.*) https://shrub.appspot.com/hypothesis-meeting-logs/$1 redirect;

    location = /xmlrpc.php {
      return 499;
    }

    location ~ ^/(|_status|a|u|t|account|admin|api|app|app.html|assets|docs/help|embed\.js.*|forgot-password|login|logout|activate|groups|notification|robots\.txt|search|signup|stream|stream\.atom|stream\.rss|users|viewer|welcome)(/|$) {
      proxy_pass http://web;
      proxy_http_version 1.1;
      proxy_connect_timeout 10s;
      proxy_send_timeout 10s;
      proxy_read_timeout 10s;
      proxy_redirect off;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Server $http_host;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Request-Start "t=${msec}";
    }

    location /ws {
      proxy_pass http://websocket;
      proxy_http_version 1.1;
      proxy_redirect off;
      proxy_buffering off;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection upgrade;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Server $http_host;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /annotating-all-knowledge/ {
      proxy_pass https://hypothesis.github.io;
      proxy_http_version 1.1;
      proxy_set_header Host $proxy_host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /roadmap {
      return 302 "https://trello.com/b/2ajZ2dWe/public-roadmap";
    }

    location / {
      ${FALLBACK_DIRECTIVES}
    }
  }

  server {
    listen 127.0.0.234:5000;
    server_name _;

    location /status {
      stub_status on;
      access_log off;
      allow 127.0.0.0/24;
      deny all;
    }
  }
}
