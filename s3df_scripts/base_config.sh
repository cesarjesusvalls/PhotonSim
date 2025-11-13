#!/bin/bash
# Base configuration for PhotonSim job generation
# This file contains common paths and settings used across all job scripts

# Base output directory for all PhotonSim simulations
OUTPUT_BASE_PATH="/sdf/data/neutrino/cjesus/photonsim_output"

# LUCiD installation path
LUCID_PATH="/sdf/home/c/cjesus/Dev/LUCiD"

# Export for use in other scripts
export OUTPUT_BASE_PATH
export LUCID_PATH
