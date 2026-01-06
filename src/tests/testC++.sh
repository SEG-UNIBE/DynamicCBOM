# g++ -std=c++17 -Wall ./testPrograms/openssl_all.cpp -lcrypto -o ./testPrograms/openssl_all


# dynamic-cbom run-new-target --log-file test_logs/openssl_all_log.log -- ./testPrograms/openssl_all


dynamic-cbom parse-log test_logs/openssl_all_log.log \
    --output-path test_logs/openssl_all_cbom.json \
    --verbose \
    > test_logs/openssl_all_debug.log


# dynamic-cbom generate-chart \
#     test_logs/openssl_all_cbom.json \
#     test_logs/openssl_all_cbom_gt.json \
#     --output-path test_logs/openssl_all_comparison_chart.pdf \
#     --verbose
