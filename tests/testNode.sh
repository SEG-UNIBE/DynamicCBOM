# dynamic-cbom run-new-target --log-file test_logs/crypto_all_log.log -- /usr/bin/node ./testPrograms/crypto_all.js

# dynamic-cbom parse-log test_logs/crypto_all_log.log \
#     --output-path test_logs/crypto_all_cbom.json \
#     > test_logs/crypto_all_debug.log

dynamic-cbom generate-chart \
    test_logs/crypto_all_cbom.json \
    test_logs/crypto_all_cbom_gt.json \
    --output-path test_logs/crypto_all_comparison_chart.pdf \
    --verbose 