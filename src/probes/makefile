# Makefile to concatenate all probe files into a single file in the build folder

# Variables
PROBE_DIR := ./
BUILD_DIR := ./build
OUTPUT_FILE := $(BUILD_DIR)/combined_probes.bt

# List of probe files
PROBE_FILES := $(wildcard $(PROBE_DIR)/*.bt)

# Default target
all: $(OUTPUT_FILE)

# Rule to concatenate probe files
$(OUTPUT_FILE): $(PROBE_FILES)
	mkdir -p $(BUILD_DIR)
	cat $^ > $@

# Clean target
clean:
	rm -f $(OUTPUT_FILE)