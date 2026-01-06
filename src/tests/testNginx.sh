

# check if the container is already running
if [ "$(docker ps -q -f name=nginx-tls)" ]; then
    echo "Container nginx-tls is already running."
else
    # build and run the nginx container
    docker build -t nginx-tls-demo ./testPrograms/nginx_tls_demo
    docker run -d -p 443:443 --name nginx-tls nginx-tls-demo
    echo "Started nginx-tls container."
fi

# start tracer in background and obtain its PID
dynamic-cbom global-trace --log-file test_logs/nginx_tls_log.log &
TRACER_PID=$!
echo "Started dynamic-cbom tracer with PID $TRACER_PID"

# give some time for the tracer to start
sleep 10
# make HTTPS requests to the nginx server
curl -k https://localhost

kill -INT "$TRACER_PID"
echo "Stopped dynamic-cbom tracer with PID $TRACER_PID"

dynamic-cbom parse-log test_logs/nginx_tls_log.log \
    --output-path test_logs/nginx_tls_cbom.json \
    --verbose \
    > test_logs/nginx_tls_debug.log
