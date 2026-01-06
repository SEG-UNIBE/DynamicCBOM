mkdir -p test_logs

dynamic-cbom install-dependencies


# # run python test programs with dynamic-cbom
dynamic-cbom run-python-test testPrograms/cryptography_symmetric.py --log-file test_logs/symmetric.log
dynamic-cbom run-python-test testPrograms/cryptography_asymmetric.py --log-file test_logs/asymmetric.log
dynamic-cbom run-python-test testPrograms/cryptography_hashing.py --log-file test_logs/hashing.log


# # run new target programs with dynamic-cbom
# # set duration to 10 seconds for openssl s_client to allow enough time for handshake
# # dynamic-cbom run-new-target --log-file test_logs/curl_log.log -- /usr/bin/curl https://www.unibe.ch
# # dynamic-cbom run-new-target --log-file test_logs/curl_ibm_log.log -- /usr/bin/curl https://www.ibm.com/
# # dynamic-cbom run-new-target --log-file test_logs/wget_log.log -- /usr/bin/wget https://www.unibe.ch -O /dev/null
# # dynamic-cbom run-new-target --log-file test_logs/github_log.log -- /usr/bin/git clone https://github.com/kelseyhightower/nocode.git -O /dev/null

# parse the logs
dynamic-cbom parse-log test_logs/symmetric.log \
    --output-path test_logs/symmetric_cbom.json \
    --verbose \
    > test_logs/symmetric_debug.log
dynamic-cbom parse-log test_logs/asymmetric.log \
    --output-path test_logs/asymmetric_cbom.json \
    --verbose \
    > test_logs/asymmetric_debug.log
dynamic-cbom parse-log test_logs/hashing.log \
    --output-path test_logs/hashing_cbom.json \
    --verbose \
    > test_logs/hashing_debug.log
echo "Parsed all logs."

# generate comparison charts
dynamic-cbom generate-chart \
    test_logs/asymmetric_cbom.json \
    tests/ground_truth/asymmetric_cbom_gt.json \
    --ibm-cbom-path tests/ibm_cbomkit/asymmetric_cbom_ibm.json \
    --output-path test_logs/asymmetric_comparison_chart.pdf \
    --verbose 

dynamic-cbom generate-chart \
    test_logs/symmetric_cbom.json \
    tests/ground_truth/symmetric_cbom_gt.json \
    --ibm-cbom-path tests/ibm_cbomkit/symmetric_cbom_ibm.json \
    --output-path test_logs/symmetric_comparison_chart.pdf \
    --verbose

dynamic-cbom generate-chart \
    test_logs/hashing_cbom.json \
    tests/ground_truth/hashing_cbom_gt.json \
    --ibm-cbom-path tests/ibm_cbomkit/hashing_cbom_ibm.json \
    --output-path test_logs/hashing_comparison_chart.pdf \
    --verbose
echo "Generated comparison charts."




